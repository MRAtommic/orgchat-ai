# -*- coding: utf-8 -*-
"""Scenarios for: source citations (Drive link), department document access, LINE expense approvals
(+ sheet logging), role-based rich menus, department usage dashboard.
Own process + throw-away DB (DB_PATH required). Exit 0 = all passed."""
import json
import os
import secrets
import sys

assert os.environ.get("DB_PATH"), "DB_PATH must point to a temporary database"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())

import app_server  # noqa: E402
import database  # noqa: E402
import line_approvals  # noqa: E402
import line_rich_menu  # noqa: E402
import rag_engine  # noqa: E402
import routes.auth as RA  # noqa: E402
from db import org_features as OF  # noqa: E402
from routes.shared import get_rag_filter  # noqa: E402

RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "scenario-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def sql(q, p=()):
    c = database._get_conn()
    try:
        cur = c.execute(q, p)
        c.commit()
        return cur
    finally:
        c.close()


def mkuser(u, org, dept="", role="member", manager=None):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
    if role != "owner":
        database.add_org_member(org, u, role, "owner1")
    sql("INSERT OR IGNORE INTO user_profiles (username, display_name, department) VALUES (?,?,?)", (u, u, dept))
    sql("UPDATE user_profiles SET department=? WHERE username=? COLLATE NOCASE", (dept, u))
    if manager:
        sql("UPDATE organization_members SET manager_username=? WHERE organization_id=? AND username=?", (manager, org, u))


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, csrf


def call(c, csrf, method, url, body=None):
    h = dict(H, **{"X-CSRF-Token": csrf})
    r = getattr(c, method)(url, json=body, headers=h) if body is not None else getattr(c, method)(url, headers=h)
    try:
        return r.status_code, r.get_json()
    except Exception:
        return r.status_code, None


# ───────── setup ─────────
database.admin_create_user("owner1", PW, role="user", email="owner1@example.com")
ORG, _ = database.create_organization("Heart Co", "owner1")
sql("UPDATE organizations SET plan='business', max_users=50 WHERE id=?", (ORG,))
database.admin_create_user("outsider", PW, role="user", email="o@example.com")
ORG2, _ = database.create_organization("Other Co", "outsider")
sql("INSERT OR IGNORE INTO user_profiles (username, display_name, department) VALUES ('owner1','owner1','')")
mkuser("acc1", ORG, "บัญชี")
mkuser("acc2", ORG, "บัญชี", manager="boss1")
mkuser("hr1", ORG, "HR")
mkuser("boss1", ORG, "บัญชี")
mkuser("nodept", ORG, "")
sql("UPDATE organization_members SET manager_username='boss1' WHERE organization_id=? AND username='acc1'", (ORG,))
for u, lid in (("acc1", "Uacc1"), ("acc2", "Uacc2"), ("boss1", "Uboss1"), ("hr1", "Uhr1"), ("owner1", "Uowner1")):
    database.link_line_user(u, lid)

# ───────── 1. Department document access ─────────
CAT_FIN = database.add_category("งบการเงิน", "d", "owner1", "public", ORG)
CAT_GEN = database.add_category("คู่มือทั่วไป", "d", "owner1", "public", ORG)
CAT_OTHER = database.add_category("ของอีกองค์กร", "d", "outsider", "public", ORG2)


def cat_ids(u):
    return {x["id"] for x in database.get_categories(u, org_id=ORG)}


check("before restriction: everyone sees both categories",
      all({CAT_FIN, CAT_GEN} <= cat_ids(u) for u in ("acc1", "hr1", "nodept")))
OF.set_category_departments(CAT_FIN, ["บัญชี"])
check("accounting member sees restricted category", CAT_FIN in cat_ids("acc1"))
check("HR member does NOT see accounting category", CAT_FIN not in cat_ids("hr1"))
check("member without department does NOT see it", CAT_FIN not in cat_ids("nodept"))
check("owner (org admin) still sees it", CAT_FIN in cat_ids("owner1"))
check("unrestricted category still visible to HR", CAT_GEN in cat_ids("hr1"))
flt = json.dumps(get_rag_filter("hr1", org_id=ORG), ensure_ascii=False)
check("RAG filter for HR excludes accounting category id", f'"{CAT_FIN}"' not in flt, flt)
flt_acc = json.dumps(get_rag_filter("acc1", org_id=ORG), ensure_ascii=False)
check("RAG filter for accounting includes it", f'"{CAT_FIN}"' in flt_acc, flt_acc)
check("department match is case/space-insensitive", (OF.set_category_departments(CAT_FIN, ["  บัญชี "]) and CAT_FIN in cat_ids("acc1")))
OF.set_category_departments(CAT_FIN, [])
check("clearing restriction restores access", CAT_FIN in cat_ids("hr1"))
OF.set_category_departments(CAT_FIN, ["บัญชี"])
check("category_is_open false once department-restricted", OF.category_is_open(CAT_FIN) is False and OF.category_is_open(CAT_GEN) is True)

# HTTP: admin can set, member cannot, other org cannot
co, cso = login("owner1")
st, j = call(co, cso, "get", "/api/org/access/categories")
check("admin lists categories with departments", st == 200 and any(x["id"] == CAT_FIN and x["departments"] == ["บัญชี"] for x in j["categories"]), str(j))
st, j = call(co, cso, "post", f"/api/org/access/categories/{CAT_FIN}/departments", {"departments": ["บัญชี", "การเงิน"]})
check("admin sets departments via API", st == 200 and set(j["departments"]) == {"บัญชี", "การเงิน"}, str(j))
cm, csm = login("hr1")
st, _ = call(cm, csm, "post", f"/api/org/access/categories/{CAT_FIN}/departments", {"departments": []})
check("plain member cannot change access (403)", st == 403)
cx, csx = login("outsider")
st, _ = call(cx, csx, "post", f"/api/org/access/categories/{CAT_FIN}/departments", {"departments": []})
check("other org's admin cannot touch this org's category (404)", st == 404, str(st))
st, _ = call(co, cso, "post", f"/api/org/access/categories/{CAT_FIN}/departments", {"departments": "bad"})
check("bad payload rejected (400)", st == 400)
OF.set_category_departments(CAT_FIN, ["บัญชี"])

# ───────── 2. Sources carry page + Drive link ─────────
FID = "f_abc"


class FakeKB:
    class collection:
        @staticmethod
        def get(**kw):
            raise RuntimeError("no filename boost in test")

    @staticmethod
    def hybrid_query(q, n_results=10, where=None):
        return [{"text": "งบกำไรขาดทุนปี 2568 ...", "score": 0.9, "source": "งบ68.pdf", "file_id": FID,
                 "location": "Page 3", "department": "บัญชี", "type": "pdf"}]


rag_engine._get_kb = lambda: FakeKB
_orig_meta = rag_engine._load_meta
rag_engine._load_meta = lambda: {FID: {"name": "งบ68.pdf", "drive_link": "https://drive.google.com/file/d/XYZ/view"}}
ctx, srcs = rag_engine.retrieve_context("ขอดูงบกำไรขาดทุน", where=None)
check("retrieve_context returns source with page", srcs and srcs[0]["location"] == "Page 3", str(srcs))
check("retrieve_context returns Drive link", srcs and srcs[0]["drive_link"].startswith("https://drive.google.com/"), str(srcs))
rag_engine._load_meta = lambda: {FID: {"name": "งบ68.pdf"}}
_, srcs2 = rag_engine.retrieve_context("ขอดูงบกำไรขาดทุน", where=None)
check("file without Drive link gets empty link (falls back to in-app viewer)", srcs2 and srcs2[0]["drive_link"] == "", str(srcs2))
rag_engine._load_meta = _orig_meta

from routes.line_webhook import _line_sources_footer  # noqa: E402

foot = _line_sources_footer([dict(srcs[0])], "คำตอบ")
check("LINE footer lists file, page and link", "งบ68.pdf" in foot and "Page 3" in foot and "https://drive.google.com/file/d/XYZ/view" in foot, foot)
check("LINE footer omitted when answer says nothing found", _line_sources_footer([dict(srcs[0])], "ยังไม่พบข้อมูลส่วนนี้ในระบบนะคะ") == "")
evil = _line_sources_footer([{"name": "x.pdf", "drive_link": "javascript:alert(1)"}], "ok")
check("LINE footer ignores non-Drive links", "javascript:" not in evil, evil)

# ───────── 3. Expense approvals ─────────
pushed = []
fake_push = lambda lid, msg: pushed.append((lid, msg))
check("parse 'เบิก 500 ค่าเดินทาง'", OF.parse_expense_command("เบิก 500 ค่าเดินทาง") == (500.0, "ค่าเดินทาง"))
check("parse 'ขอเบิก 1,250.50 บาท ค่าอุปกรณ์'", OF.parse_expense_command("ขอเบิก 1,250.50 บาท ค่าอุปกรณ์") == (1250.5, "ค่าอุปกรณ์"))
check("parse plain 'เบิก' is not a command", OF.parse_expense_command("เบิก") is None)
check("parse unrelated text is not a command", OF.parse_expense_command("วันนี้เบิกบานจัง") is None)

res = line_approvals.submit_expense("acc1", ORG, 500, "ค่าเดินทาง", fake_push)
check("submit creates request", res["ok"] and res["id"], str(res))
check("first approver is the direct manager (boss1)", res["approvers"][0] == "boss1", str(res["approvers"]))
check("card pushed to boss1's LINE id", any(lid == "Uboss1" for lid, _ in pushed))
check("requester not among approvers", "acc1" not in res["approvers"])
flex = pushed[0][1]["contents"]
check("card has approve+reject postbacks", f"approve_expense&id={res['id']}" in json.dumps(flex) and f"reject_expense&id={res['id']}" in json.dumps(flex))
rid = res["id"]
texts = []
push_text = lambda u, t: texts.append((u, t))

check("requester cannot approve own request", "ตัวเอง" in line_approvals.handle_decision("approve_expense", rid, "Uacc1", push_text))
check("unrelated employee (HR) cannot approve", "เฉพาะ" in line_approvals.handle_decision("approve_expense", rid, "Uhr1", push_text))
check("request still pending after rejected attempts", OF.get_request(rid)["status"] == "pending")
sheet_calls = []


class FakeSheets:
    def __init__(self):
        self.tabs = []
        self.rows = []

    def spreadsheets(self):
        return self

    def get(self, spreadsheetId):
        o = self
        return type("E", (), {"execute": lambda s: {"sheets": [{"properties": {"title": t}} for t in o.tabs]}})()

    def batchUpdate(self, spreadsheetId, body):
        o = self
        def ex():
            o.tabs.append(body["requests"][0]["addSheet"]["properties"]["title"])
        return type("E", (), {"execute": lambda s: ex()})()

    def values(self):
        return self

    def update(self, **kw):
        self.header = kw["body"]["values"][0]
        return type("E", (), {"execute": lambda s: None})()

    def append(self, **kw):
        o = self
        return type("E", (), {"execute": lambda s: o.rows.append(kw["body"]["values"][0])})()


# the thread inside handle_decision uses the real google_manager (no creds -> returns False); verify state + direct sheet write
msg = line_approvals.handle_decision("approve_expense", rid, "Uboss1", push_text)
check("direct manager approves", "อนุมัติ" in msg and OF.get_request(rid)["status"] == "approved", msg)
check("approver recorded", OF.get_request(rid)["approver"] == "boss1")
check("requester notified", any(u == "acc1" and "อนุมัติ" in t for u, t in texts), str(texts))
check("second click blocked (already decided)", "ไปแล้ว" in line_approvals.handle_decision("reject_expense", rid, "Uboss1", push_text))
check("decision cannot flip", OF.get_request(rid)["status"] == "approved")
fs = FakeSheets()
ok = OF.append_to_sheet(OF.get_request(rid), sheets_service=fs, spreadsheet_id="SID")
check("sheet tab created with header", ok and fs.tabs == [OF.APPROVAL_SHEET_TAB] and fs.header == OF.APPROVAL_SHEET_HEADERS)
check("sheet row has requester, dept, amount, status", fs.rows and fs.rows[0][2] == "acc1" and fs.rows[0][3] == "บัญชี" and fs.rows[0][5] == 500.0 and fs.rows[0][6] == "อนุมัติ", str(fs.rows))
check("sheet marked logged in DB", OF.get_request(rid)["sheet_logged"] == 1)
inj = OF.create_request(ORG, "acc1", "=HYPERLINK(\"http://evil\")", 10)
OF.decide_request(inj, "approved", "boss1")
fs2 = FakeSheets()
OF.append_to_sheet(OF.get_request(inj), sheets_service=fs2, spreadsheet_id="SID")
check("formula injection neutralised in sheet", fs2.rows[0][4].startswith("'="), str(fs2.rows))

res2 = line_approvals.submit_expense("hr1", ORG, 900, "ค่าอบรม", fake_push)
check("employee without manager falls back to org admin", res2["approvers"] == ["owner1"], str(res2["approvers"]))
check("org admin can approve any request", "อนุมัติ" in line_approvals.handle_decision("approve_expense", res2["id"], "Uowner1", push_text))
check("invalid amount rejected", not line_approvals.submit_expense("hr1", ORG, -5, "x", fake_push)["ok"])
check("empty title rejected", not line_approvals.submit_expense("hr1", ORG, 5, "  ", fake_push)["ok"])
check("unknown request id handled", "ไม่พบ" in line_approvals.handle_decision("approve_expense", 99999, "Uboss1", push_text))
check("unlinked LINE user cannot approve", "ผูกบัญชี" in line_approvals.handle_decision("approve_expense", rid, "Unobody", push_text))
res3 = line_approvals.submit_expense("acc2", ORG, 100, "ค่าน้ำ", fake_push)
check("pending summary shows request to manager only", "ค่าน้ำ" in line_approvals.pending_summary("boss1", ORG) and "ค่าน้ำ" not in line_approvals.pending_summary("hr1", ORG))

# web decide endpoint
res4 = line_approvals.submit_expense("hr1", ORG, 300, "ค่าไฟ", fake_push)
st, j = call(co, cso, "post", f"/api/org/approvals/{res4['id']}/decide", {"decision": "reject", "note": "เกินงบ"})
check("admin rejects via web", st == 200 and OF.get_request(res4["id"])["status"] == "rejected", str(j))
st, _ = call(co, cso, "post", f"/api/org/approvals/{res4['id']}/decide", {"decision": "approve"})
check("web double decision gives 409", st == 409)
st, _ = call(cx, csx, "post", f"/api/org/approvals/{res3['id']}/decide", {"decision": "approve"})
check("other org's admin cannot decide (404)", st == 404, str(st))
st, j = call(co, cso, "get", "/api/org/approvals?status=pending")
check("pending list endpoint", st == 200 and all(r["status"] == "pending" for r in j["requests"]))

# ───────── 4. Role-based rich menus ─────────
check("role: org admin -> admin", OF.role_for_menu("owner1", ORG) == "admin")
check("role: someone's manager -> manager", OF.role_for_menu("boss1", ORG) == "manager")
check("role: plain member -> employee", OF.role_for_menu("hr1", ORG) == "employee")
check("role: unknown -> employee", OF.role_for_menu("ghost", ORG) == "employee")
png = line_rich_menu.render_image("admin")
check("menu image is a 2500x1686 PNG", png[:8] == b"\x89PNG\r\n\x1a\n" and len(png) > 5000)


class FakeHTTP:
    def __init__(self, fail_upload_for=None):
        self.calls, self.n = [], 0
        self.fail_upload_for = fail_upload_for

    def _resp(self, code, js=None):
        return type("R", (), {"status_code": code, "json": lambda s: js or {}, "text": ""})()

    def post(self, url, **kw):
        self.calls.append(("POST", url, kw))
        if url.endswith("/v2/bot/richmenu"):
            self.n += 1
            return self._resp(200, {"richMenuId": f"menu-{kw['json']['name']}-{self.n}"})
        if "/content" in url:
            return self._resp(500 if self.fail_upload_for and self.fail_upload_for in url else 200)
        return self._resp(200)

    def delete(self, url, **kw):
        self.calls.append(("DELETE", url, kw))
        return self._resp(200)


fh = FakeHTTP()
r = line_rich_menu.setup_menus(ORG, "TOKEN", base_url="https://example.test", http=fh)
check("setup creates menus for all three roles", r["ok"] and set(r["menus"]) == {"employee", "manager", "admin"}, str(r))
created = [c for c in fh.calls if c[1].endswith("/v2/bot/richmenu")]
check("three menus created, six areas each", len(created) == 3 and all(len(c[2]["json"]["areas"]) == 6 for c in created))
adm = next(c for c in created if "admin" in c[2]["json"]["name"])
check("admin menu has dashboard link, employee menu does not",
      any(a["action"].get("uri", "").endswith("/dashboard") for a in adm[2]["json"]["areas"]) and
      not any(a["action"].get("uri", "").endswith("/dashboard") for a in next(c for c in created if "employee" in c[2]["json"]["name"])[2]["json"]["areas"]))
check("manager menu has approvals shortcut", any(a["action"].get("text") == "รออนุมัติ" for a in
      next(c for c in created if "manager" in c[2]["json"]["name"])[2]["json"]["areas"]))
check("employee menu has no approvals shortcut", not any(a["action"].get("text") == "รออนุมัติ" for a in
      next(c for c in created if "employee" in c[2]["json"]["name"])[2]["json"]["areas"]))
check("employee menu set as default", any(f"/user/all/richmenu/{r['menus']['employee']}" in c[1] for c in fh.calls))
check("menu ids stored", OF.get_menu_ids(ORG) == r["menus"])
fh2 = FakeHTTP()
r2 = line_rich_menu.setup_menus(ORG, "TOKEN", base_url="https://example.test", http=fh2)
deleted = [c[1] for c in fh2.calls if c[0] == "DELETE"]
check("re-setup deletes this app's previous menus only", len(deleted) == 3 and all(m in "".join(deleted) for m in r["menus"].values()))
fh3 = FakeHTTP(fail_upload_for="admin")
r3 = line_rich_menu.setup_menus(ORG, "TOKEN", base_url="https://example.test", http=fh3)
check("partial failure reported, not silent", (not r3["ok"]) and r3["errors"], str(r3))

fh4 = FakeHTTP()
line_rich_menu.setup_menus(ORG, "TOKEN", base_url="https://example.test", http=fh4)
ids = OF.get_menu_ids(ORG)
check("apply_role_menu links the right menu to the user", line_rich_menu.apply_role_menu("Uboss1", "manager", ORG, "TOKEN", http=fh4)
      and fh4.calls[-1][1].endswith(f"/user/Uboss1/richmenu/{ids['manager']}"))
n = len(fh4.calls)
line_rich_menu.ensure_user_menu("Uboss1", "boss1", ORG, "TOKEN", http=fh4, background=False)
line_rich_menu.ensure_user_menu("Uboss1", "boss1", ORG, "TOKEN", http=fh4, background=False)
check("ensure_user_menu links once then caches", len(fh4.calls) - n == 1, str(len(fh4.calls) - n))
sql("UPDATE organization_members SET role='admin' WHERE organization_id=? AND username='boss1'", (ORG,))
line_rich_menu.ensure_user_menu("Uboss1", "boss1", ORG, "TOKEN", http=fh4, background=False)
check("role change re-links to admin menu", fh4.calls[-1][1].endswith(f"/richmenu/{ids['admin']}"))
sql("UPDATE organization_members SET role='member' WHERE organization_id=? AND username='boss1'", (ORG,))
check("apply with no menus configured is a safe no-op", line_rich_menu.apply_role_menu("Uzzz", "admin", ORG2, "TOKEN", http=fh4) is False)

# ───────── 5. Department usage dashboard ─────────
def msg(u, role, text, sources=None, fb=0, org=ORG, ts="datetime('now')"):
    sql(f"INSERT INTO messages (username, role, text, sources, feedback, organization_id, timestamp) VALUES (?,?,?,?,?,?,{ts})",
        (u, role, text, json.dumps(sources) if sources else None, fb, org))


srcA = [{"name": "ระเบียบการเบิก.pdf", "type": "pdf", "location": "Page 1"}]
for _ in range(3):
    msg("acc1", "user", "เบิกค่าเดินทางต้องใช้เอกสารอะไร")
    msg("acc1", "bot", "ใช้ใบเสร็จ", srcA, fb=1)
msg("acc2", "user", "สิทธิ์ลาพักร้อนกี่วัน")
msg("acc2", "bot", "10 วัน", [{"name": "คู่มือพนักงาน.pdf", "type": "pdf"}])
msg("hr1", "user", "ขอแบบฟอร์มสมัครงาน")
msg("hr1", "bot", "ไม่มีข้อมูล", None, fb=-1)
msg("nodept", "user", "wifi รหัสอะไร")
msg("acc1", "user", "ข้อความเก่า", ts="datetime('now','-90 day')")
msg("outsider", "user", "คนละองค์กร", org=ORG2)
dash = OF.department_usage(ORG, days=30, minutes_per_answer=5)
by = {d["department"]: d for d in dash["departments"]}
check("dashboard groups by department", {"บัญชี", "HR", OF.NO_DEPT} <= set(by), str(list(by)))
check("accounting: 4 questions, 2 users", by["บัญชี"]["questions"] == 4 and by["บัญชี"]["active_users"] == 2, str(by.get("บัญชี")))
check("accounting: answered with sources = 4", by["บัญชี"]["answered_with_sources"] == 4)
check("time saved = answered x minutes", by["บัญชี"]["minutes_saved"] == 20 and by["บัญชี"]["hours_saved"] == 0.3)
check("top question counted", by["บัญชี"]["top_questions"][0] == {"text": "เบิกค่าเดินทางต้องใช้เอกสารอะไร", "count": 3}, str(by["บัญชี"]["top_questions"]))
check("top source counted", by["บัญชี"]["top_sources"][0]["name"] == "ระเบียบการเบิก.pdf" and by["บัญชี"]["top_sources"][0]["count"] == 3)
check("HR: unanswered + thumbs down", by["HR"]["no_source_answers"] == 1 and by["HR"]["thumbs_down"] == 1 and by["HR"]["minutes_saved"] == 0)
check("old messages outside window excluded", by["บัญชี"]["questions"] == 4)
check("other org's messages excluded", all(d["department"] != "คนละองค์กร" for d in dash["departments"]) and dash["totals"]["questions"] == 6, str(dash["totals"]))
check("members without department grouped", by[OF.NO_DEPT]["questions"] == 1)
check("totals consistent", dash["totals"]["answered_with_sources"] == 4 and dash["totals"]["hours_saved"] == round(4 * 5 / 60, 1))
check("90-day window includes old message", OF.department_usage(ORG, days=120)["totals"]["questions"] == 7)
check("minutes clamped to sane range", OF.department_usage(ORG, 30, 99999)["minutes_per_answer"] == 120)
st, j = call(co, cso, "get", "/api/org/usage-dashboard?days=30&minutes=10")
check("dashboard endpoint (admin) ok and honours minutes", st == 200 and j["minutes_per_answer"] == 10 and j["totals"]["questions"] == 6, str(j)[:200])
st, _ = call(cm, csm, "get", "/api/org/usage-dashboard")
check("dashboard endpoint forbidden for member (403)", st == 403)
st, _ = call(co, cso, "get", "/api/org/usage-dashboard?days=abc")
check("bad days param -> 400", st == 400)

print("")
print("ALL PASSED" if not FAILS else f"FAILED: {len(FAILS)} -> {FAILS}")
sys.exit(1 if FAILS else 0)
