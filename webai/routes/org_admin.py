# -*- coding: utf-8 -*-
"""
routes/org_admin.py — Organization security policy, member lifecycle and admin overview.

  GET/POST /api/org/security/policy         นโยบายความปลอดภัยขององค์กร
  GET      /api/org/security/my-status      สถานะของผู้ใช้เอง (ต้องตั้งค่า 2FA หรือไม่)
  GET      /api/org/security/members        สถานะ 2FA + สิทธิ์ของสมาชิกทุกคน (ตารางสิทธิ์)
  GET      /api/org/overview                แดชบอร์ดภาพรวม
  GET      /api/org/invites                 คำเชิญที่ค้างอยู่
  DELETE   /api/org/invites/<token>         ยกเลิกคำเชิญ
  POST     /api/org/members/import          นำเข้าสมาชิกหลายคน
  POST     /api/org/members/<u>/offboard    ขั้นตอนเมื่อพนักงานลาออก
  GET      /api/org/audit(+/export)         Audit log แบบกรองได้ + ส่งออก CSV
"""
import csv
import io
import re
import secrets
import string
from datetime import datetime

from flask import Blueprint, Response, jsonify, request, session

import database
from db import org_security
from routes.shared import get_current_org_id, login_required, org_admin_required

org_admin_bp = Blueprint("org_admin", __name__)

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.\-]{3,32}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_IMPORT_ROWS = 200


def _ip():
    return request.remote_addr or "unknown"


def _audit(action, details):
    try:
        database.log_audit_event(session.get("user"), action, details, _ip(), get_current_org_id() or 1)
    except Exception:
        pass


# ───────────────────────── Security policy ─────────────────────────
@org_admin_bp.route("/api/org/security/policy", methods=["GET"])
@org_admin_required
def get_security_policy():
    return jsonify({"ok": True, "policy": org_security.get_policy(get_current_org_id())})


@org_admin_bp.route("/api/org/security/policy", methods=["POST"])
@org_admin_required
def save_security_policy():
    org_id = get_current_org_id()
    data = request.get_json(silent=True) or {}
    ok, err = org_security.set_policy(org_id, data, session.get("user"))
    if not ok:
        return jsonify({"ok": False, "error": err}), 400
    _audit("ORG_SECURITY_POLICY_UPDATED",
           f"require_2fa={data.get('require_2fa')} idle={data.get('session_timeout_min')}m "
           f"min_pw={data.get('min_password_length')} methods={','.join(data.get('allowed_login_methods') or [])}")
    session.pop("_2fa_need", None)
    return jsonify({"ok": True, "policy": org_security.get_policy(org_id),
                    "message": "บันทึกนโยบายความปลอดภัยเรียบร้อยแล้ว"})


@org_admin_bp.route("/api/org/security/my-status", methods=["GET"])
@login_required
def my_security_status():
    me = session.get("user")
    need = org_security.needs_2fa_setup(me)
    return jsonify({
        "ok": True,
        "must_setup_2fa": need,
        "idle_timeout_min": org_security.idle_seconds_for_user(me) // 60,
        "min_password_length": org_security.min_password_length_for(me),
    })


@org_admin_bp.route("/api/org/security/members", methods=["GET"])
@org_admin_required
def security_members():
    return jsonify({"ok": True, "members": org_security.members_security(get_current_org_id())})


@org_admin_bp.route("/api/org/overview", methods=["GET"])
@org_admin_required
def org_overview():
    org_id = get_current_org_id()
    data = org_security.overview(org_id)
    try:
        data["quota"] = database.get_org_quota_info(org_id)
    except Exception:
        data["quota"] = {}
    return jsonify(data)


# ───────────────────────── Invites ─────────────────────────
@org_admin_bp.route("/api/org/invites", methods=["GET"])
@org_admin_required
def list_invites():
    return jsonify({"ok": True, "invites": org_security.pending_invites(get_current_org_id())})


@org_admin_bp.route("/api/org/invites/<token>", methods=["DELETE"])
@org_admin_required
def revoke_invite(token):
    org_id = get_current_org_id()
    if org_security.revoke_invite(org_id, token):
        _audit("ORG_INVITE_REVOKED", f"token={token[:8]}…")
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "ไม่พบคำเชิญนี้"}), 404


# ───────────────────────── Bulk import ─────────────────────────
def _temp_password(length: int) -> str:
    alphabet_l, alphabet_u, digits, sym = string.ascii_lowercase, string.ascii_uppercase, string.digits, "!@#$%&*"
    pw = [secrets.choice(alphabet_l), secrets.choice(alphabet_u), secrets.choice(digits), secrets.choice(sym)]
    pool = alphabet_l + alphabet_u + digits + sym
    pw += [secrets.choice(pool) for _ in range(max(length, 12) - 4)]
    secrets.SystemRandom().shuffle(pw)
    return "".join(pw)


def _parse_csv_text(text: str) -> list:
    rows = []
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    for r in reader:
        rows.append({(k or "").strip().lower(): (v or "").strip() for k, v in r.items()})
    return rows


@org_admin_bp.route("/api/org/members/import", methods=["POST"])
@org_admin_required
def import_members():
    """Create many accounts at once. Accepts {rows:[...]} or {csv:"username,email,display_name,department,role\\n..."}.
    A temporary password is generated per account and returned ONCE in the report."""
    org_id = get_current_org_id()
    me = session.get("user")
    data = request.get_json(silent=True) or {}
    rows = data.get("rows")
    if rows is None and data.get("csv"):
        rows = _parse_csv_text(str(data["csv"]))
    if not isinstance(rows, list) or not rows:
        return jsonify({"ok": False, "error": "ไม่พบข้อมูลสมาชิกที่จะนำเข้า"}), 400
    if len(rows) > MAX_IMPORT_ROWS:
        return jsonify({"ok": False, "error": f"นำเข้าได้ครั้งละไม่เกิน {MAX_IMPORT_ROWS} รายการ"}), 400

    quota = database.get_org_quota_info(org_id) or {}
    max_users = -1 if quota.get("is_unlimited") else int(quota.get("max_users") or 5)
    min_len = org_security.get_policy(org_id)["min_password_length"]

    report, created = [], 0
    for i, raw in enumerate(rows, start=1):
        row = {str(k).strip().lower(): (str(v).strip() if v is not None else "") for k, v in (raw or {}).items()}
        username = row.get("username") or row.get("ชื่อผู้ใช้") or ""
        email = (row.get("email") or row.get("อีเมล") or "").lower()
        display = row.get("display_name") or row.get("name") or row.get("ชื่อ") or username
        dept = row.get("department") or row.get("แผนก") or "General"
        role = "admin" if (row.get("role") or "").lower() == "admin" else "member"
        entry = {"row": i, "username": username, "email": email, "status": "", "temp_password": ""}
        if not _USERNAME_RE.match(username):
            entry["status"] = "ข้าม: ชื่อผู้ใช้ต้องเป็น a-z 0-9 _ . - ยาว 3-32 ตัว"
        elif email and not _EMAIL_RE.match(email):
            entry["status"] = "ข้าม: รูปแบบอีเมลไม่ถูกต้อง"
        else:
            pw = _temp_password(min_len)
            try:
                if not database.admin_create_user(username, pw, role="user", display_name=display, department=dept, email=email or None):
                    entry["status"] = "ข้าม: มีชื่อผู้ใช้นี้อยู่แล้ว"
                else:
                    ok, why = database.add_org_member_with_quota(org_id, username, role, me, max_users)
                    if not ok:
                        entry["status"] = "ข้าม: " + ("จำนวนสมาชิกเต็มโควตาแพ็กเกจ" if why == "quota_exceeded" else "เพิ่มเข้าองค์กรไม่สำเร็จ")
                    else:
                        entry["status"] = "สร้างแล้ว"
                        entry["temp_password"] = pw
                        created += 1
            except Exception as e:  # keep going; report the row
                entry["status"] = f"ผิดพลาด: {e}"
        report.append(entry)
    _audit("ORG_MEMBERS_IMPORTED", f"created={created} total_rows={len(rows)}")
    return jsonify({"ok": True, "created": created, "skipped": len(rows) - created, "report": report,
                    "note": "รหัสผ่านชั่วคราวแสดงครั้งเดียว กรุณาแจ้งสมาชิกให้เปลี่ยนรหัสผ่านหลังเข้าสู่ระบบครั้งแรก"})


# ───────────────────────── Offboarding ─────────────────────────
@org_admin_bp.route("/api/org/members/<username>/offboard", methods=["POST"])
@org_admin_required
def offboard_member(username):
    """พนักงานลาออก: ระงับบัญชี, ตัดการผูก LINE, ออกจากระบบทุกอุปกรณ์, โอนลูกทีมให้หัวหน้าใหม่, (เลือก) ถอดออกจากองค์กร"""
    org_id = get_current_org_id()
    me = session.get("user")
    data = request.get_json(silent=True) or {}
    remove_from_org = bool(data.get("remove_from_org"))
    reassign_to = (data.get("reassign_to") or "").strip()

    if username.lower() == (me or "").lower():
        return jsonify({"ok": False, "error": "ไม่สามารถดำเนินการกับบัญชีของตัวเองได้"}), 400
    if not database.is_org_member(org_id, username):
        return jsonify({"ok": False, "error": "ไม่พบสมาชิกคนนี้ในองค์กร"}), 404
    if database.is_org_owner(org_id, username):
        return jsonify({"ok": False, "error": "ไม่สามารถทำกับเจ้าขององค์กรได้ ต้องโอนความเป็นเจ้าของก่อน"}), 400
    if reassign_to and not database.is_org_member(org_id, reassign_to):
        return jsonify({"ok": False, "error": "ผู้รับช่วงงานต้องเป็นสมาชิกขององค์กร"}), 400

    steps = []
    # บัญชีหนึ่งอาจอยู่หลายองค์กร: ห้ามระงับบัญชี/ตัดการผูก LINE ทั้งระบบ เพราะจะกระทบองค์กรอื่นที่ไม่ใช่ของแอดมินคนนี้
    other_orgs = [o for o in database.get_user_orgs(username) if int(o["id"]) != int(org_id)]
    shared_account = bool(other_orgs)
    if shared_account:
        remove_from_org = True
    conn = database._get_conn()
    try:
        if not shared_account:
            conn.execute("UPDATE user_settings SET is_active = 0 WHERE username = ? COLLATE NOCASE", (username,))
            steps.append("ระงับบัญชีแล้ว")
        reports = conn.execute(
            "SELECT username FROM organization_members WHERE organization_id = ? AND manager_username = ? COLLATE NOCASE",
            (org_id, username)).fetchall()
        new_mgr = reassign_to or ""
        conn.execute(
            "UPDATE organization_members SET manager_username = ? WHERE organization_id = ? AND manager_username = ? COLLATE NOCASE",
            (new_mgr or None, org_id, username))
        if reports:
            steps.append(f"โอนลูกทีม {len(reports)} คนให้ {new_mgr or 'ไม่มีหัวหน้า'}")
        conn.commit()
    finally:
        conn.close()
    if shared_account:
        steps.append(f"บัญชีนี้ยังเป็นสมาชิกอีก {len(other_orgs)} องค์กร จึงไม่ระงับบัญชีและไม่ตัดการผูก LINE (ถอดออกจากองค์กรนี้เท่านั้น)")
    else:
        try:
            if database.unlink_line_user(username):
                steps.append("ตัดการผูกบัญชี LINE แล้ว")
        except Exception:
            pass
        try:
            database.increment_user_session_version(username)
            steps.append("ออกจากระบบทุกอุปกรณ์แล้ว")
        except Exception:
            pass
    if remove_from_org:
        if database.remove_org_member(org_id, username):
            steps.append("ถอดออกจากองค์กรแล้ว")
    _audit("ORG_MEMBER_OFFBOARDED", f"user={username} remove={remove_from_org} reassign={reassign_to or '-'}")
    return jsonify({"ok": True, "steps": steps})


# ───────────────────────── Audit log (filter + export) ─────────────────────────
def _audit_query(org_id):
    args = request.args
    where, params = ["org_id = ?"], [org_id]
    user = (args.get("user") or "").strip()
    action = (args.get("action") or "").strip()
    d_from, d_to = (args.get("from") or "").strip(), (args.get("to") or "").strip()
    if user:
        where.append("username LIKE ? COLLATE NOCASE")
        params.append(f"%{user}%")
    if action:
        where.append("(action LIKE ? OR details LIKE ?)")
        params += [f"%{action}%", f"%{action}%"]
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d_from):
        where.append("timestamp >= ?")
        params.append(d_from + " 00:00:00")
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d_to):
        where.append("timestamp <= ?")
        params.append(d_to + " 23:59:59")
    return " AND ".join(where), params


@org_admin_bp.route("/api/org/audit", methods=["GET"])
@org_admin_required
def org_audit():
    org_id = get_current_org_id()
    try:
        limit = max(1, min(200, int(request.args.get("limit", 50))))
        offset = max(0, int(request.args.get("offset", 0)))
    except ValueError:
        limit, offset = 50, 0
    where, params = _audit_query(org_id)
    conn = database._get_conn()
    try:
        total = conn.execute(f"SELECT COUNT(*) FROM audit_logs WHERE {where}", params).fetchone()[0]
        rows = conn.execute(
            f"SELECT id, username, action, details, ip_address, timestamp FROM audit_logs WHERE {where} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?", params + [limit, offset]).fetchall()
    finally:
        conn.close()
    return jsonify({"ok": True, "total": total, "logs": [
        {"id": r[0], "username": r[1], "action": r[2], "details": r[3], "ip": r[4], "time": r[5]} for r in rows]})


@org_admin_bp.route("/api/org/audit/export", methods=["GET"])
@org_admin_required
def org_audit_export():
    org_id = get_current_org_id()
    where, params = _audit_query(org_id)
    conn = database._get_conn()
    try:
        rows = conn.execute(
            f"SELECT timestamp, username, action, details, ip_address FROM audit_logs WHERE {where} "
            f"ORDER BY id DESC LIMIT 5000", params).fetchall()
    finally:
        conn.close()
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["เวลา", "ผู้ใช้", "กิจกรรม", "รายละเอียด", "IP"])
    for r in rows:
        # กัน CSV/Excel formula injection
        w.writerow([("'" + str(c) if isinstance(c, str) and c[:1] in "=+-@" else c) for c in r])
    _audit("ORG_AUDIT_EXPORTED", f"rows={len(rows)}")
    fn = f"org_{org_id}_audit_{datetime.now():%Y%m%d_%H%M}.csv"
    return Response(("﻿" + buf.getvalue()).encode("utf-8"), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={fn}"})
