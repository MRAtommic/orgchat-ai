# -*- coding: utf-8 -*-
"""
db/org_features.py — ฟีเจอร์ระดับองค์กร 4 ส่วน

  1. สิทธิ์เอกสารตามแผนก      kb_category_departments  (หมวดความรู้ที่จำกัดเฉพาะบางแผนก)
  2. คำขออนุมัติ (เบิกจ่าย ฯลฯ)  approval_requests        (อนุมัติผ่าน LINE แล้วบันทึกลงชีต)
  3. บทบาทสำหรับ Rich Menu     role_for_menu()
  4. แดชบอร์ดการใช้งานต่อแผนก   department_usage()

ตารางสร้างเองแบบ idempotent (CREATE TABLE IF NOT EXISTS) เมื่อถูกเรียกครั้งแรก
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

from db.connection import _get_conn

NO_DEPT = "ไม่ระบุแผนก"
MENU_ROLES = ("employee", "manager", "admin")


def _ensure(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS kb_category_departments (
            category_id INTEGER NOT NULL,
            department  TEXT NOT NULL COLLATE NOCASE,
            PRIMARY KEY (category_id, department)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            kind TEXT NOT NULL DEFAULT 'expense',
            requester TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT DEFAULT '',
            amount REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            approver TEXT,
            note TEXT DEFAULT '',
            decided_at DATETIME,
            sheet_logged INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_approval_org_status ON approval_requests(org_id, status)")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS line_rich_menus (
            org_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            menu_id TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (org_id, role)
        )
    """)


def _norm_dept(d) -> str:
    return re.sub(r"\s+", " ", (d or "").strip()).lower()


# ═════════════════════════ 1. สิทธิ์ตามแผนก ═════════════════════════
def get_category_departments(category_id: int) -> list:
    conn = _get_conn()
    try:
        _ensure(conn)
        rows = conn.execute("SELECT department FROM kb_category_departments WHERE category_id = ? ORDER BY department",
                            (int(category_id),)).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


def set_category_departments(category_id: int, departments: list) -> list:
    """กำหนดแผนกที่เข้าถึงหมวดได้ (ลิสต์ว่าง = ทุกคนที่มีสิทธิ์ตามปกติ)"""
    clean, seen = [], set()
    for d in departments or []:
        d = re.sub(r"\s+", " ", str(d or "").strip())[:80]
        if d and d.lower() not in seen:
            seen.add(d.lower())
            clean.append(d)
    conn = _get_conn()
    try:
        _ensure(conn)
        conn.execute("DELETE FROM kb_category_departments WHERE category_id = ?", (int(category_id),))
        for d in clean:
            conn.execute("INSERT OR IGNORE INTO kb_category_departments (category_id, department) VALUES (?, ?)",
                         (int(category_id), d))
        conn.commit()
        return clean
    finally:
        conn.close()


def get_user_department(username: str) -> str:
    if not username:
        return ""
    conn = _get_conn()
    try:
        row = conn.execute("SELECT department FROM user_profiles WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        return (row[0] or "").strip() if row else ""
    except Exception:
        return ""
    finally:
        conn.close()


def _is_privileged(username: str, org_id) -> bool:
    """แอดมินระบบ / แอดมินองค์กร มองเห็นทุกหมวดเสมอ"""
    if not username:
        return False
    if username == "Admin":
        return True
    conn = _get_conn()
    try:
        row = conn.execute("SELECT role FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if row and row[0] in ("admin", "superadmin"):
            return True
        if org_id is not None:
            r = conn.execute(
                "SELECT role FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE",
                (org_id, username)).fetchone()
            if r and (r[0] or "").lower() in ("admin", "owner"):
                return True
    except Exception:
        return False
    finally:
        conn.close()
    return False


def category_is_open(category_id) -> bool:
    """True เมื่อหมวดเป็นสาธารณะทั้งองค์กร (ไม่จำกัดผู้ใช้/ระดับ/แผนก) หรือไม่มีหมวด
    ใช้ตัดสินว่าลิงก์ Drive ของไฟล์ในหมวดนี้เปิดสาธารณะได้หรือไม่"""
    if category_id in (None, "", 0):
        return True
    conn = _get_conn()
    try:
        _ensure(conn)
        r = conn.execute("SELECT visibility, access_level FROM kb_categories WHERE id = ?", (int(category_id),)).fetchone()
        if not r:
            return False
        if (r[0] or "public") != "public" or (r[1] or "public") != "public":
            return False
        d = conn.execute("SELECT 1 FROM kb_category_departments WHERE category_id = ? LIMIT 1", (int(category_id),)).fetchone()
        return d is None
    except Exception:
        return False
    finally:
        conn.close()


def list_org_categories(org_id: int) -> list:
    """หมวดความรู้ของ org (รวมหมวดเก่าที่ไม่มี org) พร้อมแผนกที่จำกัดไว้"""
    conn = _get_conn()
    try:
        _ensure(conn)
        cols = [r[1] for r in conn.execute("PRAGMA table_info(kb_categories)").fetchall()]
        where = "WHERE (organization_id = ? OR organization_id IS NULL)" if "organization_id" in cols else ""
        params = (int(org_id),) if where else ()
        rows = conn.execute(f"SELECT id, name, COALESCE(visibility,'public'), COALESCE(access_level,'public') FROM kb_categories {where} ORDER BY name", params).fetchall()
        deps = defaultdict(list)
        for cid, d in conn.execute("SELECT category_id, department FROM kb_category_departments ORDER BY department").fetchall():
            deps[int(cid)].append(d)
        return [{"id": r[0], "name": r[1], "visibility": r[2], "access_level": r[3], "departments": deps.get(int(r[0]), [])} for r in rows]
    finally:
        conn.close()


def category_in_org(category_id: int, org_id: int) -> bool:
    return any(int(c["id"]) == int(category_id) for c in list_org_categories(org_id))


def filter_categories_by_department(username: str, org_id, categories: list) -> list:
    """ตัดหมวดที่จำกัดแผนกออก ถ้าผู้ใช้ไม่ได้อยู่ในแผนกที่อนุญาต
    ใช้ต่อท้าย get_categories() จึงมีผลกับทุกเส้นทางที่ค้นหาข้อมูล (เว็บแชต, LINE, สรุปเอกสาร, รายการไฟล์)"""
    if not categories:
        return categories
    ids = [int(c["id"]) for c in categories if c.get("id") is not None]
    if not ids:
        return categories
    conn = _get_conn()
    try:
        _ensure(conn)
        q = ",".join("?" * len(ids))
        rows = conn.execute(f"SELECT category_id, department FROM kb_category_departments WHERE category_id IN ({q})", ids).fetchall()
    finally:
        conn.close()
    if not rows:
        return categories
    allowed = defaultdict(set)
    for cid, dept in rows:
        allowed[int(cid)].add(_norm_dept(dept))
    if _is_privileged(username, org_id):
        return categories
    my_dept = _norm_dept(get_user_department(username))
    out = []
    for c in categories:
        cid = int(c["id"]) if c.get("id") is not None else None
        deps = allowed.get(cid)
        if not deps:
            out.append(c)
        elif my_dept and my_dept in deps:
            out.append(c)
        elif username and (c.get("created_by") or "").lower() == username.lower():
            out.append(c)
    return out


# ═════════════════════════ 2. คำขออนุมัติ ═════════════════════════
def _row_to_req(r) -> dict:
    keys = ["id", "org_id", "kind", "requester", "title", "detail", "amount", "status",
            "approver", "note", "decided_at", "sheet_logged", "created_at"]
    return dict(zip(keys, r))


_REQ_COLS = "id, org_id, kind, requester, title, detail, amount, status, approver, note, decided_at, sheet_logged, created_at"


def create_request(org_id: int, requester: str, title: str, amount: float = 0, kind: str = "expense", detail: str = "") -> int:
    title = (title or "").strip()[:200]
    if not title:
        raise ValueError("ต้องระบุรายละเอียดคำขอ")
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        raise ValueError("จำนวนเงินไม่ถูกต้อง")
    if amount < 0 or amount > 100_000_000:
        raise ValueError("จำนวนเงินไม่ถูกต้อง")
    conn = _get_conn()
    try:
        _ensure(conn)
        cur = conn.execute(
            "INSERT INTO approval_requests (org_id, kind, requester, title, detail, amount) VALUES (?,?,?,?,?,?)",
            (int(org_id), kind, requester, title, (detail or "")[:1000], amount))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_request(req_id: int):
    conn = _get_conn()
    try:
        _ensure(conn)
        r = conn.execute(f"SELECT {_REQ_COLS} FROM approval_requests WHERE id = ?", (int(req_id),)).fetchone()
        return _row_to_req(r) if r else None
    finally:
        conn.close()


def list_requests(org_id: int, status: str = None, limit: int = 100) -> list:
    conn = _get_conn()
    try:
        _ensure(conn)
        sql, params = f"SELECT {_REQ_COLS} FROM approval_requests WHERE org_id = ?", [int(org_id)]
        if status:
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(max(1, min(int(limit), 500)))
        return [_row_to_req(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()


def find_approvers(org_id: int, requester: str) -> list:
    """ผู้อนุมัติ: หัวหน้าโดยตรง → หัวหน้าแผนก → แอดมินองค์กร (เรียงตามลำดับความใกล้ชิด) ไม่รวมผู้ขอเอง"""
    out = []

    def add(u):
        u = (u or "").strip()
        if u and u.lower() != (requester or "").lower() and u.lower() not in [x.lower() for x in out]:
            out.append(u)

    conn = _get_conn()
    try:
        r = conn.execute("SELECT manager_username FROM organization_members WHERE organization_id = ? AND username = ? COLLATE NOCASE",
                         (org_id, requester)).fetchone()
        if r:
            add(r[0])
        dept = get_user_department(requester)
        if dept:
            try:
                d = conn.execute("SELECT head_username FROM organization_departments WHERE organization_id = ? AND name = ? COLLATE NOCASE",
                                 (org_id, dept)).fetchone()
                if d:
                    add(d[0])
            except Exception:
                pass
        for a in conn.execute(
                "SELECT username FROM organization_members WHERE organization_id = ? AND lower(role) IN ('admin','owner')",
                (org_id,)).fetchall():
            add(a[0])
    finally:
        conn.close()
    return out


def can_decide(org_id: int, approver: str, req: dict) -> bool:
    if not approver or not req:
        return False
    if (req.get("requester") or "").lower() == approver.lower():
        return False  # อนุมัติของตัวเองไม่ได้
    return approver.lower() in [a.lower() for a in find_approvers(org_id, req["requester"])] \
        or _is_privileged(approver, org_id)


def decide_request(req_id: int, status: str, approver: str, note: str = "") -> bool:
    """อนุมัติ/ปฏิเสธ — สำเร็จได้ครั้งเดียว (กันกดซ้ำ/อนุมัติซ้อน)"""
    if status not in ("approved", "rejected"):
        return False
    conn = _get_conn()
    try:
        _ensure(conn)
        cur = conn.execute(
            "UPDATE approval_requests SET status = ?, approver = ?, note = ?, decided_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND status = 'pending'", (status, approver, (note or "")[:300], int(req_id)))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def mark_sheet_logged(req_id: int):
    conn = _get_conn()
    try:
        _ensure(conn)
        conn.execute("UPDATE approval_requests SET sheet_logged = 1 WHERE id = ?", (int(req_id),))
        conn.commit()
    finally:
        conn.close()


_FORMULA_START = ("=", "+", "-", "@", "\t", "\r")


def sheet_safe(v):
    """กัน formula injection เมื่อเขียนลง Google Sheets แบบ USER_ENTERED"""
    if isinstance(v, str) and v.startswith(_FORMULA_START):
        return "'" + v
    return v


APPROVAL_SHEET_TAB = "อนุมัติคำขอ (จากระบบ)"
APPROVAL_SHEET_HEADERS = ["เลขที่", "ประเภท", "ผู้ขอ", "แผนก", "รายการ", "จำนวนเงิน", "ผลพิจารณา",
                          "ผู้อนุมัติ", "หมายเหตุ", "วันที่ขอ", "วันที่พิจารณา"]
KIND_LABEL = {"expense": "เบิกจ่าย", "leave": "ลา", "other": "อื่นๆ"}
STATUS_LABEL = {"approved": "อนุมัติ", "rejected": "ปฏิเสธ", "pending": "รอพิจารณา"}


def approval_sheet_row(req: dict) -> list:
    return [sheet_safe(x) for x in [
        req["id"], KIND_LABEL.get(req.get("kind"), req.get("kind")), req.get("requester"),
        get_user_department(req.get("requester")), req.get("title"), req.get("amount") or 0,
        STATUS_LABEL.get(req.get("status"), req.get("status")), req.get("approver") or "",
        req.get("note") or "", req.get("created_at") or "", req.get("decided_at") or "",
    ]]


def append_to_sheet(req: dict, sheets_service=None, spreadsheet_id=None) -> bool:
    """บันทึกผลลงชีตขององค์กร (สร้างแท็บ + หัวตารางให้เองถ้ายังไม่มี)
    sheets_service/spreadsheet_id ส่งเข้ามาได้เพื่อทดสอบ; ถ้าไม่ส่งจะใช้ Google Workspace ขององค์กร"""
    own_ctx = False
    gm = None
    try:
        if sheets_service is None:
            from google_drive_service import google_manager as gm
            gm.set_context(username=req.get("requester"), org_id=req.get("org_id"))
            own_ctx = True
            sheets_service, spreadsheet_id = gm.sheets_service, gm.spreadsheet_id
        if not sheets_service or not spreadsheet_id:
            return False
        tab = APPROVAL_SHEET_TAB
        meta = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        if not any(s["properties"]["title"] == tab for s in meta.get("sheets", [])):
            sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id, body={"requests": [{"addSheet": {"properties": {"title": tab}}}]}).execute()
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=f"'{tab}'!A1", valueInputOption="USER_ENTERED",
                body={"values": [APPROVAL_SHEET_HEADERS]}).execute()
        sheets_service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id, range=f"'{tab}'!A1", valueInputOption="USER_ENTERED",
            body={"values": [approval_sheet_row(req)]}).execute()
        if isinstance(req.get("id"), int):
            mark_sheet_logged(req["id"])
        return True
    except Exception as e:
        import logging
        logging.getLogger("OrgChatAI").error(f"[approval] sheet log failed for #{req.get('id')}: {e}")
        return False
    finally:
        if own_ctx and gm is not None:
            try:
                gm.clear_context()
            except Exception:
                pass


_EXPENSE_RE = re.compile(r"^\s*(?:ขอ)?เบิก(?:จ่าย)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:บาท|฿)?\s*(.*)$")


def parse_expense_command(text: str):
    """'เบิก 500 ค่าเดินทาง' → (500.0, 'ค่าเดินทาง')  ไม่ตรงรูปแบบ → None"""
    m = _EXPENSE_RE.match(text or "")
    if not m:
        return None
    try:
        amount = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    title = (m.group(2) or "").strip()
    return (amount, title or "ค่าใช้จ่ายทั่วไป")


# ═════════════════════════ 3. บทบาทสำหรับ Rich Menu ═════════════════════════
def role_for_menu(username: str, org_id) -> str:
    """admin = แอดมินระบบ/องค์กร, manager = เป็นหัวหน้าของใครสักคนหรือหัวหน้าแผนก, อื่นๆ = employee"""
    if not username:
        return "employee"
    if _is_privileged(username, org_id):
        return "admin"
    conn = _get_conn()
    try:
        if org_id is not None:
            r = conn.execute("SELECT 1 FROM organization_members WHERE organization_id = ? AND manager_username = ? COLLATE NOCASE LIMIT 1",
                             (org_id, username)).fetchone()
            if r:
                return "manager"
            try:
                d = conn.execute("SELECT 1 FROM organization_departments WHERE organization_id = ? AND head_username = ? COLLATE NOCASE LIMIT 1",
                                 (org_id, username)).fetchone()
                if d:
                    return "manager"
            except Exception:
                pass
        s = conn.execute("SELECT role FROM user_settings WHERE username = ? COLLATE NOCASE", (username,)).fetchone()
        if s and s[0] == "manager":
            return "manager"
    except Exception:
        pass
    finally:
        conn.close()
    return "employee"


def save_menu_id(org_id: int, role: str, menu_id: str):
    conn = _get_conn()
    try:
        _ensure(conn)
        conn.execute("INSERT OR REPLACE INTO line_rich_menus (org_id, role, menu_id, updated_at) VALUES (?,?,?,CURRENT_TIMESTAMP)",
                     (int(org_id), role, menu_id))
        conn.commit()
    finally:
        conn.close()


def get_menu_ids(org_id: int) -> dict:
    conn = _get_conn()
    try:
        _ensure(conn)
        return {r[0]: r[1] for r in conn.execute("SELECT role, menu_id FROM line_rich_menus WHERE org_id = ?", (int(org_id),)).fetchall()}
    finally:
        conn.close()


# ═════════════════════════ 4. แดชบอร์ดต่อแผนก ═════════════════════════
def _source_names(sources_json) -> list:
    if not sources_json:
        return []
    try:
        data = json.loads(sources_json) if isinstance(sources_json, str) else sources_json
    except Exception:
        return []
    names = []
    for s in data if isinstance(data, list) else []:
        if isinstance(s, dict) and s.get("type") != "image":
            n = (s.get("name") or s.get("source") or "").strip()
            if n:
                names.append(n)
    return names


def _norm_question(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())[:120]


def department_usage(org_id: int, days: int = 30, minutes_per_answer: int = 5) -> dict:
    days = max(1, min(int(days), 365))
    minutes_per_answer = max(1, min(int(minutes_per_answer), 120))
    cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    conn = _get_conn()
    try:
        rows = conn.execute(
            """SELECT m.username, m.role, m.text, m.sources, m.feedback, m.timestamp,
                      COALESCE(NULLIF(TRIM(up.department), ''), ?) AS dept
               FROM messages m
               LEFT JOIN user_profiles up ON up.username = m.username COLLATE NOCASE
               WHERE m.organization_id = ? AND m.timestamp >= ?""",
            (NO_DEPT, int(org_id), cutoff)).fetchall()
    finally:
        conn.close()

    depts = {}

    def bucket(d):
        return depts.setdefault(d, {"department": d, "questions": 0, "answered": 0, "unanswered": 0,
                                    "thumbs_up": 0, "thumbs_down": 0, "users": set(),
                                    "_q": Counter(), "_src": Counter()})

    daily = Counter()
    for username, role, text, sources, feedback, ts, dept in rows:
        b = bucket(dept)
        if role == "user":
            b["questions"] += 1
            b["users"].add((username or "").lower())
            q = _norm_question(text)
            if len(q) >= 4:
                b["_q"][q] += 1
            daily[str(ts)[:10]] += 1
        elif role == "bot":
            names = _source_names(sources)
            if names:
                b["answered"] += 1
                for n in set(names):
                    b["_src"][n] += 1
            else:
                b["unanswered"] += 1
            if feedback == 1:
                b["thumbs_up"] += 1
            elif feedback == -1:
                b["thumbs_down"] += 1

    out = []
    for b in depts.values():
        if not b["questions"] and not b["answered"]:
            continue
        saved = b["answered"] * minutes_per_answer
        out.append({
            "department": b["department"], "questions": b["questions"], "active_users": len(b["users"]),
            "answered_with_sources": b["answered"], "no_source_answers": b["unanswered"],
            "thumbs_up": b["thumbs_up"], "thumbs_down": b["thumbs_down"],
            "minutes_saved": saved, "hours_saved": round(saved / 60, 1),
            "top_questions": [{"text": t, "count": c} for t, c in b["_q"].most_common(5) if c >= 1],
            "top_sources": [{"name": n, "count": c} for n, c in b["_src"].most_common(5)],
        })
    out.sort(key=lambda x: -x["questions"])
    total_q = sum(d["questions"] for d in out)
    total_ans = sum(d["answered_with_sources"] for d in out)
    return {
        "days": days, "minutes_per_answer": minutes_per_answer,
        "totals": {"questions": total_q, "answered_with_sources": total_ans,
                   "active_users": len({u for d in depts.values() for u in d["users"]}),
                   "hours_saved": round(total_ans * minutes_per_answer / 60, 1)},
        "departments": out,
        "daily": [{"date": d, "questions": c} for d, c in sorted(daily.items())],
        "note": "เวลาที่ประหยัด = จำนวนคำตอบที่มีแหล่งอ้างอิง × นาทีเฉลี่ยที่ใช้ค้นหาเอง (ค่าประมาณ ปรับได้)",
    }
