# -*- coding: utf-8 -*-
"""Cross-tenant / permission regression tests for routes that take an id.
Own process, temp DB + temp DATA_DIR (never touches real data). Exit 0 = all passed."""
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path

assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR"), "DB_PATH and DATA_DIR must point to temp locations"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())

import app_server  # noqa: E402
import database  # noqa: E402
import rag_engine  # noqa: E402
import routes.auth as RA  # noqa: E402
from db import org_features as OF  # noqa: E402

RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "ac-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


class _R(list):
    def fetchone(self):
        return self[0] if self else None

    def fetchall(self):
        return list(self)


def sql(q, p=()):
    c = database._get_conn()
    try:
        cur = c.execute(q, p)
        rows = _R(cur.fetchall()) if cur.description else _R()
        c.commit()
        return rows
    finally:
        c.close()


def user(u, org=None, dept="", role="member"):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
    if org:
        database.add_org_member(org, u, role, "ownerA")
    sql("INSERT OR IGNORE INTO user_profiles (username, display_name, department) VALUES (?,?,?)", (u, u, dept))
    sql("UPDATE user_profiles SET department=? WHERE username=? COLLATE NOCASE", (dept, u))
    sql("UPDATE user_settings SET can_view_kb=1, can_edit_kb=1 WHERE username=? COLLATE NOCASE", (u,))


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, csrf


def call(cl, method, url, body=None):
    c, csrf = cl
    h = dict(H, **{"X-CSRF-Token": csrf})
    r = getattr(c, method)(url, json=body, headers=h) if body is not None else getattr(c, method)(url, headers=h)
    return r


# ── tenants ──
database.admin_create_user("ownerA", PW, role="user", email="oa@example.com")
ORG_A, _ = database.create_organization("Org A", "ownerA")
database.admin_create_user("ownerB", PW, role="user", email="ob@example.com")
ORG_B, _ = database.create_organization("Org B", "ownerB")
for o in (ORG_A, ORG_B):
    sql("UPDATE organizations SET plan='business', max_users=50 WHERE id=?", (o,))
sql("UPDATE user_settings SET can_view_kb=1, can_edit_kb=1 WHERE username IN ('ownerA','ownerB')")
sql("INSERT OR IGNORE INTO user_profiles (username, display_name, department) VALUES ('ownerA','ownerA','')")
user("acc", ORG_A, "บัญชี")
user("hr", ORG_A, "HR")
user("outsider", ORG_B, "บัญชี")
CA = {n: login(n) for n in ("ownerA", "acc", "hr", "ownerB", "outsider")}

CAT_ACC = database.add_category("งบการเงิน", "d", "ownerA", "public", ORG_A)
CAT_PUB = database.add_category("ทั่วไป", "d", "ownerA", "public", ORG_A)
CAT_B = database.add_category("ของ B", "d", "ownerB", "public", ORG_B)
OF.set_category_departments(CAT_ACC, ["บัญชี"])

# ── KB files on disk + meta ──
up = rag_engine.UPLOAD_DIR
(up / "secret_fin.txt").write_text("ตัวเลขลับ", encoding="utf-8")
(up / "open_doc.txt").write_text("ข้อมูลทั่วไป", encoding="utf-8")
(up / "fin.csv").write_text("a,b\n1,2\n", encoding="utf-8")
meta = {
    "F_SECRET": {"name": "secret_fin.txt", "path": str(up / "secret_fin.txt"), "type": "txt", "status": "ready", "organization_id": ORG_A, "category_id": CAT_ACC, "chunks": 1},
    "F_OPEN": {"name": "open_doc.txt", "path": str(up / "open_doc.txt"), "type": "txt", "status": "ready", "organization_id": ORG_A, "category_id": None, "chunks": 1},
    "F_CSV": {"name": "fin.csv", "path": str(up / "fin.csv"), "type": "csv", "status": "ready", "organization_id": ORG_A, "category_id": CAT_ACC, "chunks": 1},
}
rag_engine._save_meta(meta)
rag_engine._load_meta = lambda: json.load(open(rag_engine.META_FILE, encoding="utf-8"))  # always fresh


def code(r):
    return r.status_code


# 1) restricted file: view / download / csv / txt
check("accounting member can view restricted file", code(call(CA["acc"], "get", "/api/kb/files/view/F_SECRET")) == 200)
check("HR member CANNOT view restricted file by id", code(call(CA["hr"], "get", "/api/kb/files/view/F_SECRET")) in (403, 404))
check("org admin can view restricted file", code(call(CA["ownerA"], "get", "/api/kb/files/view/F_SECRET")) == 200)
check("other org cannot view file", code(call(CA["ownerB"], "get", "/api/kb/files/view/F_SECRET")) in (403, 404))
check("HR can view unassigned (open) file", code(call(CA["hr"], "get", "/api/kb/files/view/F_OPEN")) == 200)
check("accounting can download restricted file", code(call(CA["acc"], "get", "/api/files/download/secret_fin.txt")) == 200)
check("HR CANNOT download restricted file", code(call(CA["hr"], "get", "/api/files/download/secret_fin.txt")) == 404)
check("HR can download open file", code(call(CA["hr"], "get", "/api/files/download/open_doc.txt")) == 200)
check("HR CANNOT read restricted CSV", code(call(CA["hr"], "get", "/api/csv/F_CSV")) == 404)
check("accounting can read restricted CSV", code(call(CA["acc"], "get", "/api/csv/F_CSV")) == 200)
check("HR CANNOT read restricted TXT editor", code(call(CA["hr"], "get", "/api/txt/F_SECRET")) == 404)
check("HR CANNOT preview restricted page", code(call(CA["hr"], "get", "/api/kb/page-preview?file_id=F_SECRET&page=1")) == 404)

# 2) re-categorise
r = call(CA["ownerB"], "put", "/api/files/F_SECRET/category", {"category_id": CAT_B})
check("other org cannot re-categorise this org's file", code(r) in (403, 404), str(r.get_json()))
check("category unchanged after cross-org attempt", rag_engine._load_meta()["F_SECRET"]["category_id"] == CAT_ACC)
r = call(CA["hr"], "put", "/api/files/F_SECRET/category", {"category_id": CAT_PUB})
check("HR cannot move a restricted file into a public category", code(r) in (403, 404), str(r.get_json()))
check("category still restricted", rag_engine._load_meta()["F_SECRET"]["category_id"] == CAT_ACC)
sql("UPDATE user_settings SET can_edit_kb=0 WHERE username='acc'")
r = call(CA["acc"], "put", "/api/files/F_OPEN/category", {"category_id": CAT_PUB})
check("member without edit permission cannot re-categorise", code(r) == 403, str(r.get_json()))
sql("UPDATE user_settings SET can_edit_kb=1 WHERE username='acc'")
r = call(CA["ownerA"], "put", "/api/files/F_OPEN/category", {"category_id": CAT_B})
check("admin cannot assign another org's category", code(r) == 403, str(r.get_json()))
rag_engine.update_file_category = lambda fid, cat: (rag_engine._save_meta({**rag_engine._load_meta(), fid: {**rag_engine._load_meta()[fid], "category_id": cat}}) or True)
database.update_file_category = lambda fid, cat: True
r = call(CA["ownerA"], "put", "/api/files/F_OPEN/category", {"category_id": CAT_PUB})
check("admin can re-categorise own file into own category", code(r) == 200 and rag_engine._load_meta()["F_OPEN"]["category_id"] == CAT_PUB, str(r.get_json()))

# 3) leave comments
lid = database.create_leave_request("hr", "ลาป่วย", "2026-12-01", "2026-12-02", "ไม่สบาย", org_id=ORG_A)
lid = lid if isinstance(lid, int) else sql("SELECT max(id) FROM leave_requests").fetchone()[0]
sql("UPDATE leave_requests SET org_id=? WHERE id=?", (ORG_A, lid))
check("applicant can read own leave comments", code(call(CA["hr"], "get", f"/api/leave/comments/{lid}")) == 200)
check("org admin can read leave comments", code(call(CA["ownerA"], "get", f"/api/leave/comments/{lid}")) == 200)
check("colleague (plain member) CANNOT read someone's leave comments", code(call(CA["acc"], "get", f"/api/leave/comments/{lid}")) == 404)
check("other org CANNOT read leave comments", code(call(CA["ownerB"], "get", f"/api/leave/comments/{lid}")) == 404)
r = call(CA["outsider"], "post", "/api/leave/comment", {"leave_id": lid, "comment": "spam"})
check("other org CANNOT add comment to a leave", code(r) == 404)
check("no spam comment stored", sql("SELECT count(*) FROM leave_comments WHERE leave_id=?", (lid,)).fetchone()[0] == 0)
r = call(CA["ownerA"], "post", "/api/leave/comment", {"leave_id": lid, "comment": "ok"})
check("org admin can comment", code(r) == 200, str(r.get_json()))
r = call(CA["ownerA"], "post", "/api/leave/comment", {"leave_id": lid, "comment": "x" * 5000})
check("oversized comment rejected", code(r) == 400)

# 4) chat room pin
rid = database.create_room("ทีมบัญชี", "ownerA", members=["hr"], org_id=ORG_A)
rid = rid if isinstance(rid, int) else sql("SELECT max(id) FROM chat_rooms").fetchone()[0]
sql("INSERT INTO room_messages (room_id, username, text) VALUES (?,?,?)", (rid, "ownerA", "ข้อความ"))
mid = sql("SELECT max(id) FROM room_messages").fetchone()[0]
check("room member can pin", code(call(CA["hr"], "post", f"/api/chat/rooms/pin/{mid}")) == 200)
check("non-member (same org) CANNOT pin", code(call(CA["acc"], "post", f"/api/chat/rooms/pin/{mid}")) == 404)
check("other org CANNOT pin", code(call(CA["ownerB"], "post", f"/api/chat/pin/room/{mid}")) == 404)
check("pin state only changed by member", sql("SELECT is_pinned FROM room_messages WHERE id=?", (mid,)).fetchone()[0] == 1)

# 5) post summarize
sql("INSERT INTO posts (content, author, category, organization_id) VALUES ('ข้อมูลลับของ A','ownerA','General',?)", (ORG_A,))
pid = sql("SELECT max(id) FROM posts").fetchone()[0]
r = call(CA["ownerB"], "post", f"/api/posts/{pid}/summarize")
check("other org CANNOT summarize (read) this org's post", code(r) == 404, str(r.get_json()))
check("post summary not overwritten", (sql("SELECT summary FROM posts WHERE id=?", (pid,)).fetchone()[0] or "") == "")

# 6) schedule status
sid = database.add_schedule("ownerA", "งานสาธารณะ", "2026-12-05", is_public=1, org_id=ORG_A)
sid = sid if isinstance(sid, int) else sql("SELECT max(id) FROM schedules").fetchone()[0]
sql("UPDATE schedules SET organization_id=? WHERE id=?", (ORG_A, sid))
r = call(CA["outsider"], "patch", f"/api/schedules/{sid}/status", {"status": "done"})
check("other org CANNOT change a public schedule's status", code(r) == 403, str(r.get_json()))
check("schedule status unchanged", sql("SELECT status FROM schedules WHERE id=?", (sid,)).fetchone()[0] != "done")
r = call(CA["hr"], "patch", f"/api/schedules/{sid}/status", {"status": "doing"})
check("same-org member can change public schedule status", code(r) == 200, str(r.get_json()))

# 7) platform-wide admin endpoints must NOT be usable by an organisation owner (org creation grants role=admin)
# เส้นทางทำลาย/เขียนระดับระบบ: ตรวจว่า "ถูกป้องกันด้วย platform_admin_required" โดยไม่เรียกใช้จริง (กันทำลายข้อมูล)
DESTRUCTIVE = ["/api/wipe", "/api/prune", "/api/sync", "/api/set_key", "/api/admin/notifications/clear_all",
               "/api/admin/db/backup", "/api/admin/db/optimize", "/api/admin/chat/ai/clear", "/api/admin/chat/dm/clear",
               "/api/admin/users/<username>/toggle-active", "/api/admin/chat/room/<int:room_id>/clear"]
rules = {r.rule: r for r in app.url_map.iter_rules()}
for path in DESTRUCTIVE:
    rule = rules.get(path)
    view = app.view_functions.get(rule.endpoint) if rule else None
    check(f"{path} is platform-admin only", bool(view) and getattr(view, "_platform_admin", False), "missing" if not view else "unprotected")

r = call(CA["ownerB"], "get", "/api/admin/chat/overview")
body = json.dumps(r.get_json() or {}, ensure_ascii=False)
check("org owner of another tenant CANNOT list all orgs' chat rooms", code(r) in (401, 403) and "ทีมบัญชี" not in body, str(code(r)))
r = call(CA["ownerB"], "get", "/api/logs")
check("org owner CANNOT read server logs", code(r) in (401, 403), str(code(r)))
r = call(CA["ownerB"], "get", "/api/admin/search-insights")
check("org owner CANNOT read every tenant's search insights", code(r) in (401, 403), str(code(r)))
r = call(CA["ownerA"], "get", "/api/org/overview")
check("org owner CAN still use their own org admin endpoints", code(r) == 200, str(code(r)))
sql("UPDATE user_settings SET role='superadmin' WHERE username='ownerA'")
ca2 = login("ownerA")
r = call(ca2, "get", "/api/admin/chat/overview")
check("a real platform admin (superadmin) still can", code(r) == 200, str(code(r)))
sql("UPDATE user_settings SET role='admin' WHERE username='ownerA'")


# 8) deleting a category must actually work (regression: it always crashed on a non-existent table) and detach its files
CAT_DEL = database.add_category("ลบทิ้ง", "d", "ownerA", "public", ORG_A)
rag_engine._save_meta({**rag_engine._load_meta(), "F_DEL": {"name": "d.txt", "path": str(rag_engine.UPLOAD_DIR / "open_doc.txt"), "type": "txt", "status": "ready", "organization_id": ORG_A, "category_id": CAT_DEL, "chunks": 1}})
rag_engine.update_file_category = lambda fid, cat: (rag_engine._save_meta({**rag_engine._load_meta(), fid: {**rag_engine._load_meta()[fid], "category_id": cat}}) or True)
r = call(CA["ownerA"], "delete", f"/api/kb/categories/{CAT_DEL}")
check("deleting a KB category succeeds", code(r) == 200 and (r.get_json() or {}).get("ok"), str(r.get_json()))
check("category is gone", not any(c["id"] == CAT_DEL for c in database.get_categories("ownerA", org_id=ORG_A)))
check("its files are detached (category cleared)", rag_engine._load_meta()["F_DEL"]["category_id"] in (None, ""))
r = call(CA["ownerB"], "delete", f"/api/kb/categories/{CAT_PUB}")
check("other org cannot delete this org's category", code(r) == 404, str(code(r)))

print("")
print("ALL PASSED" if not FAILS else f"FAILED: {len(FAILS)} -> {FAILS}")
sys.exit(1 if FAILS else 0)
