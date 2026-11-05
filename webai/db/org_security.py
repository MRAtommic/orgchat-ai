"""
Organization security policy + admin overview helpers.

Policies are stored per organization in `org_security_policies`:
  require_2fa            off | admins | all
  session_timeout_min    idle timeout in minutes (15..1440)
  min_password_length    8..64
  allowed_login_methods  subset of password / google / line / qr  (owner is never locked out)
"""
import json
import sqlite3
import time
from datetime import datetime, timedelta

from db.connection import _get_conn

ALL_METHODS = ["password", "google", "line", "qr"]
DEFAULT_POLICY = {
    "require_2fa": "off",
    "session_timeout_min": 120,
    "min_password_length": 8,
    "allowed_login_methods": list(ALL_METHODS),
}

_CACHE: dict = {}
_CACHE_TTL = 30


def _ensure(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS org_security_policies (
            org_id INTEGER PRIMARY KEY,
            require_2fa TEXT DEFAULT 'off',
            session_timeout_min INTEGER DEFAULT 120,
            min_password_length INTEGER DEFAULT 8,
            allowed_login_methods TEXT,
            updated_by TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


def invalidate(org_id=None):
    if org_id is None:
        _CACHE.clear()
    else:
        _CACHE.pop(int(org_id), None)


def get_policy(org_id: int) -> dict:
    org_id = int(org_id)
    hit = _CACHE.get(org_id)
    if hit and time.time() - hit[0] < _CACHE_TTL:
        return dict(hit[1])
    pol = dict(DEFAULT_POLICY)
    pol["allowed_login_methods"] = list(ALL_METHODS)
    conn = _get_conn()
    try:
        _ensure(conn)
        row = conn.execute(
            "SELECT require_2fa, session_timeout_min, min_password_length, allowed_login_methods, updated_by, updated_at "
            "FROM org_security_policies WHERE org_id = ?", (org_id,)).fetchone()
    finally:
        conn.close()
    if row:
        pol["require_2fa"] = row[0] or "off"
        pol["session_timeout_min"] = int(row[1] or 120)
        pol["min_password_length"] = int(row[2] or 8)
        try:
            methods = json.loads(row[3]) if row[3] else None
        except Exception:
            methods = None
        if isinstance(methods, list) and methods:
            pol["allowed_login_methods"] = [m for m in methods if m in ALL_METHODS] or list(ALL_METHODS)
        pol["updated_by"], pol["updated_at"] = row[4], row[5]
    _CACHE[org_id] = (time.time(), dict(pol))
    return pol


def validate_policy(data: dict) -> tuple[dict | None, str]:
    out = {}
    r = str(data.get("require_2fa", "off")).lower()
    if r not in ("off", "admins", "all"):
        return None, "ค่าการบังคับ 2FA ไม่ถูกต้อง"
    out["require_2fa"] = r
    try:
        t = int(data.get("session_timeout_min", 120))
    except Exception:
        return None, "เวลาหมดอายุเซสชันต้องเป็นตัวเลข (นาที)"
    if not 15 <= t <= 1440:
        return None, "เวลาหมดอายุเซสชันต้องอยู่ระหว่าง 15 ถึง 1440 นาที"
    out["session_timeout_min"] = t
    try:
        m = int(data.get("min_password_length", 8))
    except Exception:
        return None, "ความยาวรหัสผ่านขั้นต่ำต้องเป็นตัวเลข"
    if not 8 <= m <= 64:
        return None, "ความยาวรหัสผ่านขั้นต่ำต้องอยู่ระหว่าง 8 ถึง 64 ตัวอักษร"
    out["min_password_length"] = m
    methods = data.get("allowed_login_methods")
    if not isinstance(methods, list):
        return None, "กรุณาเลือกวิธีล็อกอินที่อนุญาต"
    methods = [x for x in methods if x in ALL_METHODS]
    if not methods:
        return None, "ต้องอนุญาตวิธีล็อกอินอย่างน้อย 1 วิธี"
    out["allowed_login_methods"] = methods
    return out, ""


def set_policy(org_id: int, data: dict, updated_by: str) -> tuple[bool, str]:
    clean, err = validate_policy(data)
    if err:
        return False, err
    conn = _get_conn()
    try:
        _ensure(conn)
        conn.execute("""
            INSERT INTO org_security_policies
                (org_id, require_2fa, session_timeout_min, min_password_length, allowed_login_methods, updated_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(org_id) DO UPDATE SET
                require_2fa=excluded.require_2fa, session_timeout_min=excluded.session_timeout_min,
                min_password_length=excluded.min_password_length, allowed_login_methods=excluded.allowed_login_methods,
                updated_by=excluded.updated_by, updated_at=CURRENT_TIMESTAMP
        """, (int(org_id), clean["require_2fa"], clean["session_timeout_min"], clean["min_password_length"],
              json.dumps(clean["allowed_login_methods"]), updated_by))
        conn.commit()
    finally:
        conn.close()
    invalidate(org_id)
    return True, ""


# ─── Per-user effective rules (strictest wins across the user's organizations) ───
def _user_orgs(username: str) -> list:
    conn = _get_conn()
    try:
        rows = conn.execute("""
            SELECT om.organization_id, om.role, COALESCE(o.owner_username, '')
            FROM organization_members om
            LEFT JOIN organizations o ON o.id = om.organization_id
            WHERE om.username = ? COLLATE NOCASE
        """, (username,)).fetchall()
    finally:
        conn.close()
    out = []
    for r in rows:
        owner = (r[2] or "").lower()
        if not owner:  # องค์กรเก่าที่ไม่ได้บันทึกเจ้าของ: ถือว่า Admin คนแรกที่เข้าร่วมคือเจ้าของ
            conn2 = _get_conn()
            try:
                first = conn2.execute(
                    "SELECT username FROM organization_members WHERE organization_id = ? AND role = 'admin' ORDER BY joined_at, rowid LIMIT 1",
                    (r[0],)).fetchone()
            finally:
                conn2.close()
            owner = ((first[0] if first else "") or "").lower()
        out.append({"org_id": r[0], "role": r[1], "is_owner": owner == (username or "").lower()})
    return out


def idle_seconds_for_user(username: str, default: int = 7200) -> int:
    best = None
    for o in _user_orgs(username):
        t = get_policy(o["org_id"])["session_timeout_min"] * 60
        best = t if best is None else min(best, t)
    return best or default


def needs_2fa_setup(username: str) -> bool:
    """True when an org policy requires 2FA for this user and they have not enabled it yet."""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT COALESCE(totp_enabled,0) FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
    finally:
        conn.close()
    if row and row[0]:
        return False
    for o in _user_orgs(username):
        req = get_policy(o["org_id"])["require_2fa"]
        if req == "all" or (req == "admins" and o["role"] == "admin"):
            return True
    return False


def login_method_allowed(username: str, method: str) -> tuple[bool, str]:
    names = {"password": "รหัสผ่าน", "google": "Google", "line": "LINE", "qr": "QR Code"}
    sets = []
    for o in _user_orgs(username):
        if o["is_owner"]:
            continue  # เจ้าขององค์กรไม่ถูกจำกัดวิธีล็อกอิน
        sets.append(set(get_policy(o["org_id"])["allowed_login_methods"]))
    if not sets:
        return True, ""
    allowed = set.intersection(*sets)      # เข้มสุดชนะเมื่อหลายองค์กร
    if not allowed:
        allowed = set.union(*sets)         # แต่ถ้านโยบายขัดกันจนไม่เหลือวิธีใด ให้ใช้วิธีที่องค์กรใดองค์กรหนึ่งอนุญาต (กันล็อกอินไม่ได้เลย)
    if method not in allowed:
        return False, f"องค์กรของคุณไม่อนุญาตให้เข้าสู่ระบบด้วย {names.get(method, method)} กรุณาใช้วิธีอื่นที่องค์กรกำหนด"
    return True, ""


def min_password_length_for(username: str) -> int:
    best = 8
    for o in _user_orgs(username):
        best = max(best, get_policy(o["org_id"])["min_password_length"])
    return best


def check_password_policy(username: str, password: str) -> tuple[bool, str]:
    need = min_password_length_for(username)
    if len(password or "") < need:
        return False, f"นโยบายองค์กรกำหนดให้รหัสผ่านยาวอย่างน้อย {need} ตัวอักษร"
    return True, ""


# ─── Admin views ───
def members_security(org_id: int) -> list:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("""
            SELECT om.username, om.role, om.joined_at,
                   COALESCE(up.display_name, om.username) AS display_name,
                   COALESCE(up.department, '') AS department,
                   COALESCE(s.email, '') AS email,
                   COALESCE(s.is_active, 1) AS is_active,
                   COALESCE(s.totp_enabled, 0) AS totp_enabled,
                   COALESCE(s.totp_type, 'authenticator') AS totp_type,
                   COALESCE(s.can_view_financial,0) AS can_view_financial,
                   COALESCE(s.can_manage_leave,0) AS can_manage_leave,
                   COALESCE(s.can_view_kb,0) AS can_view_kb,
                   COALESCE(s.can_edit_kb,0) AS can_edit_kb,
                   COALESCE(s.can_delete_kb,0) AS can_delete_kb,
                   COALESCE(s.can_broadcast_line,0) AS can_broadcast_line,
                   COALESCE(s.can_manage_peak,0) AS can_manage_peak,
                   CASE WHEN COALESCE(up.line_user_id,'') <> '' THEN 1 ELSE 0 END AS line_linked
            FROM organization_members om
            LEFT JOIN user_profiles up ON om.username = up.username
            LEFT JOIN user_settings s ON om.username = s.username
            WHERE om.organization_id = ?
            ORDER BY CASE om.role WHEN 'admin' THEN 0 ELSE 1 END, om.joined_at
        """, (org_id,)).fetchall()
        owner = conn.execute("SELECT owner_username FROM organizations WHERE id = ?", (org_id,)).fetchone()
    except sqlite3.OperationalError:
        # older DBs without line_user_id on user_settings
        rows = conn.execute("""
            SELECT om.username, om.role, om.joined_at,
                   COALESCE(up.display_name, om.username) AS display_name,
                   COALESCE(up.department, '') AS department,
                   COALESCE(s.email, '') AS email,
                   COALESCE(s.is_active, 1) AS is_active,
                   COALESCE(s.totp_enabled, 0) AS totp_enabled,
                   COALESCE(s.totp_type, 'authenticator') AS totp_type,
                   COALESCE(s.can_view_financial,0) AS can_view_financial,
                   COALESCE(s.can_manage_leave,0) AS can_manage_leave,
                   COALESCE(s.can_view_kb,0) AS can_view_kb,
                   COALESCE(s.can_edit_kb,0) AS can_edit_kb,
                   COALESCE(s.can_delete_kb,0) AS can_delete_kb,
                   COALESCE(s.can_broadcast_line,0) AS can_broadcast_line,
                   COALESCE(s.can_manage_peak,0) AS can_manage_peak,
                   0 AS line_linked
            FROM organization_members om
            LEFT JOIN user_profiles up ON om.username = up.username
            LEFT JOIN user_settings s ON om.username = s.username
            WHERE om.organization_id = ?
        """, (org_id,)).fetchall()
        owner = conn.execute("SELECT owner_username FROM organizations WHERE id = ?", (org_id,)).fetchone()
    finally:
        conn.close()
    owner_name = ((owner[0] if owner else "") or "").lower()
    out = []
    for r in rows:
        d = {k: r[k] for k in r.keys()}
        d["is_owner"] = d["username"].lower() == owner_name
        for k in ("is_active", "totp_enabled", "can_view_financial", "can_manage_leave", "can_view_kb", "can_edit_kb",
                  "can_delete_kb", "can_broadcast_line", "can_manage_peak", "line_linked"):
            d[k] = bool(d[k])
        out.append(d)
    return out


def pending_invites(org_id: int) -> list:
    conn = _get_conn()
    out = []
    try:
        rows = conn.execute("""
            SELECT token, created_by, role, department, max_uses, used_count, expires_at, created_at
            FROM org_invite_tokens WHERE organization_id = ? ORDER BY created_at DESC
        """, (org_id,)).fetchall()
        now = datetime.now()
        for r in rows:
            exp = r[6]
            expired = False
            if exp:
                try:
                    expired = datetime.fromisoformat(str(exp).replace("Z", "")) < now
                except Exception:
                    expired = False
            used_up = bool(r[4]) and (r[5] or 0) >= r[4]
            out.append({
                "kind": "link", "token": r[0], "token_short": (r[0] or "")[:8] + "…", "created_by": r[1], "role": r[2] or "member",
                "department": r[3] or "", "max_uses": r[4] or 0, "used_count": r[5] or 0,
                "expires_at": exp, "created_at": r[7], "status": "expired" if expired else ("used_up" if used_up else "active"),
            })
    except sqlite3.OperationalError:
        pass
    finally:
        conn.close()
    return out


def revoke_invite(org_id: int, token: str) -> bool:
    conn = _get_conn()
    try:
        cur = conn.execute("DELETE FROM org_invite_tokens WHERE organization_id = ? AND token = ?", (org_id, token))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def failed_login_alerts(org_id: int, hours: int = 24, threshold: int = 3) -> list:
    """Members (or unknown names) with repeated failed logins recently."""
    since = int(time.time()) - hours * 3600
    conn = _get_conn()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ip TEXT NOT NULL, username TEXT, success INTEGER NOT NULL DEFAULT 0, ts INTEGER NOT NULL)""")
        rows = conn.execute("""
            SELECT la.username, COUNT(*) AS n, COUNT(DISTINCT la.ip) AS ips, MAX(la.ts) AS last_ts
            FROM login_attempts la
            JOIN organization_members om ON om.username = la.username COLLATE NOCASE AND om.organization_id = ?
            WHERE la.success = 0 AND la.ts >= ?
            GROUP BY la.username HAVING n >= ? ORDER BY n DESC
        """, (org_id, since, threshold)).fetchall()
    finally:
        conn.close()
    return [{"username": r[0], "failed": r[1], "distinct_ips": r[2],
             "last_at": datetime.fromtimestamp(r[3]).strftime("%Y-%m-%d %H:%M:%S")} for r in rows]


def overview(org_id: int) -> dict:
    members = members_security(org_id)
    total = len(members)
    active = sum(1 for m in members if m["is_active"])
    admins = sum(1 for m in members if m["role"] == "admin")
    with2fa = sum(1 for m in members if m["totp_enabled"])
    invites = pending_invites(org_id)
    pol = get_policy(org_id)
    alerts = failed_login_alerts(org_id)
    without_email = sum(1 for m in members if not m["email"])
    return {
        "ok": True,
        "members": {"total": total, "active": active, "suspended": total - active, "admins": admins, "without_email": without_email},
        "two_fa": {"enabled": with2fa, "missing": total - with2fa, "percent": int(round(with2fa * 100 / total)) if total else 0,
                   "required": pol["require_2fa"]},
        "invites": {"active": sum(1 for i in invites if i["status"] == "active"), "total": len(invites)},
        "policy": pol,
        "alerts": alerts,
    }
