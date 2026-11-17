# -*- coding: utf-8 -*-
"""LINE 'ค้นหา <คำ>' must search files first (even for words like รายชื่อ), keep the staff-directory shortcut for plain directory questions,
and never list files from categories the user cannot access. Temp DB/DATA_DIR, LINE + AI mocked."""
import os, secrets, sys
from pathlib import Path
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["VECTOR_BACKEND"] = "python"
sys.path.insert(0, os.getcwd())
import app_server, database, rag_engine  # noqa: E402
import routes.line_webhook as LW  # noqa: E402
import billing  # noqa: E402
billing.has_feature = lambda org_id, feature: True      # LINE Bot needs a Pro plan; this test is about routing/permissions, not billing
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


PW = "Passw0rd!x"
database.admin_create_user("boss", PW, role="admin", email="boss@example.com", display_name="Boss")
database.admin_create_user("mem", PW, role="user", email="mem@example.com", display_name="Mem")
oid, _ = database.create_organization("LS Org", "boss")
database.add_org_member(oid, "mem", "member", "boss")
BOSS_LINE, MEM_LINE = "U" + "b" * 32, "U" + "c" * 32
database.link_line_user("boss", BOSS_LINE)
database.link_line_user("mem", MEM_LINE)
pub = database.add_category("ทั่วไป", visibility="public", created_by="boss", org_id=oid)
priv = database.add_category("เงินเดือน", visibility="private", created_by="boss", org_id=oid)

d = Path(os.environ["DATA_DIR"]) / "uploads"
d.mkdir(parents=True, exist_ok=True)
meta = {}
for i, (name, cat) in enumerate([("รายชื่อพนักงาน.txt", pub), ("salary.data.csv", priv), ("กฎระเบียบ.txt", pub)]):
    disk = d / f"f{i}_{name}"
    disk.write_text("x", encoding="utf-8")
    meta[f"id{i}"] = {"name": name, "path": str(disk), "chunks": 1, "size": 1, "type": name.rsplit(".", 1)[-1], "department": "General",
                      "category_id": cat, "organization_id": oid, "status": "ready", "timestamp": "2026-01-01T00:00:00"}
rag_engine._save_meta(meta)

SENT = []
_ORIG_REPLY = LW.reply_to_line
LW.reply_to_line = lambda token, msg, *a, **k: SENT.append(msg if isinstance(msg, str) else " ".join(m.get("text", "") if isinstance(m, dict) else str(m) for m in msg) + " " + str(msg))
LW.send_line_push_notification = lambda *a, **k: None
try:
    LW.ai_providers.generate_response = lambda *a, **k: "AI_STUB_ANSWER"
except Exception:
    pass


def say(line_id, text):
    SENT.clear()
    try:
        LW.process_line_command(text, line_id, "tok")
    except Exception as e:
        SENT.append(f"EXC:{type(e).__name__}:{e}")
    return "\n".join(str(x) for x in SENT)


r = say(MEM_LINE, "ค้นหา รายชื่อ")
check("'ค้นหา รายชื่อ' returns the FILE (with link), not the staff list", "รายชื่อพนักงาน.txt" in r and "รายชื่อพนักงานและสมาชิก" not in r, r[:200])
check("…and gives a download/open link", "/api/files/download/" in r or "#kb" in r, r[:200])
r = say(MEM_LINE, "ค้นหาไฟล์รายชื่อ")
check("'ค้นหาไฟล์รายชื่อ' returns the file", "รายชื่อพนักงาน.txt" in r and "รายชื่อพนักงานและสมาชิก" not in r, r[:200])
r = say(MEM_LINE, "รายชื่อพนักงาน")
check("plain 'รายชื่อพนักงาน' still gives the staff directory", "รายชื่อพนักงานและสมาชิก" in r, r[:200])
r = say(MEM_LINE, "ค้นหา salary")
check("member CANNOT see the salary file (restricted category)", "salary.data.csv" not in r, r[:200])
r = say(MEM_LINE, "ค้นหาไฟล์ salary")
check("explicit file search for a restricted file → 'not found', no leak", "salary.data.csv" not in r and ("ไม่พบ" in r), r[:200])
r = say(BOSS_LINE, "ค้นหา salary")
check("admin CAN find the salary file", "salary.data.csv" in r, r[:200])
r = say(MEM_LINE, "ค้นหา ซิ่งๆๆ ที่ไม่มีไฟล์")
check("ambiguous 'ค้นหา X' with no file match is NOT answered with a hard 'file not found'", "ยังไม่พบไฟล์" not in r, r[:200])
# ---- links must be valid for LINE (Thai file names were sent raw → HTTP 400 "Invalid action URI" → no reply at all) ----
import re  # noqa: E402
r = say(MEM_LINE, "ค้นหา รายชื่อ")
urls = re.findall(r"https?://[^\s\\\"'<>)\]]+", r)
check("file-search links contain ASCII only (Thai file names are percent-encoded)", bool(urls) and all(u.isascii() for u in urls), repr([u[-60:] for u in urls if not u.isascii()][:2]))
r = say(MEM_LINE, "ค้นหา")
check("bare 'ค้นหา' (Rich Menu button) lists the files instead of asking the AI", "รายชื่อพนักงาน.txt" in r and "AI_STUB_ANSWER" not in r, r[:200])

sm = LW._sanitize_line_uris({"type": "flex", "contents": {"footer": {"contents": [{"action": {"type": "uri", "uri": "https://x.example/api/files/download/f0_รายชื่อ.txt?token=abc"}}]}}})
u = sm["contents"]["footer"]["contents"][0]["action"]["uri"]
check("sanitizer percent-encodes Thai in button URIs and keeps valid URIs intact", u.isascii() and "%E0%B8" in u and u.startswith("https://x.example/api/files/download/") and
      LW._sanitize_line_uris({"uri": "https://a.example/p?x=1&y=2#f"})["uri"] == "https://a.example/p?x=1&y=2#f", u)

calls = []


class _Resp:
    def __init__(self, code, text=""):
        self.status_code, self.text = code, text


def _fake_post(url, headers=None, json=None, timeout=None):
    calls.append(json)
    if len(calls) == 1:
        return _Resp(400, '{"message":"A message (messages[0]) in the request body is invalid","details":[{"message":"Invalid action URI"}]}')
    return _Resp(200)


_old_post, _old_tok = LW.requests.post, LW.get_channel_access_token
LW.requests.post, LW.get_channel_access_token = _fake_post, (lambda *a, **k: "tok")
_ORIG_REPLY("rtok", [{"type": "flex", "altText": "ผลค้นหาไฟล์", "contents": {"type": "bubble"}}, {"type": "text", "text": "ข้อความสำรอง"}])
LW.requests.post, LW.get_channel_access_token = _old_post, _old_tok
check("when LINE still rejects a card because of a URI, the reply is retried as plain text",
      len(calls) == 2 and all(m.get("type") == "text" for m in (calls[1] or {}).get("messages", [])) and len(calls[1]["messages"]) == 2, str(calls[1:] )[:200])

# ---- file search sends only the card; the text is kept as a fallback for a rejected card ----
SEEN = []
_keep = LW.reply_to_line
LW.reply_to_line = lambda token, msg, *a, **k: SEEN.append((msg, k))
LW.process_line_command("ค้นหา รายชื่อ", MEM_LINE, "tok")
LW.reply_to_line = _keep
card_msgs = [m for m, k in SEEN]
check("file search replies with ONE card message (no duplicate long text)", len(card_msgs) == 1 and isinstance(card_msgs[0], dict) and card_msgs[0].get("type") == "flex", str(type(card_msgs[0]) if card_msgs else None))
check("…and carries a plain-text fallback without ** markers", bool(SEEN) and "รายชื่อพนักงาน.txt" in (SEEN[0][1].get("fallback_text") or "") and "**" not in (SEEN[0][1].get("fallback_text") or ""))

calls2 = []


def _fake_post2(url, headers=None, json=None, timeout=None):
    calls2.append(json)
    return _Resp(400, '{"message":"something else is invalid"}') if len(calls2) == 1 else _Resp(200)


LW.requests.post, LW.get_channel_access_token = _fake_post2, (lambda *a, **k: "tok")
_ORIG_REPLY("rtok", {"type": "flex", "altText": "x", "contents": {"type": "bubble"}}, fallback_text="ข้อความสำรองของการ์ด")
LW.requests.post, LW.get_channel_access_token = _old_post, _old_tok
check("a rejected card (any 400) falls back to the provided plain text",
      len(calls2) == 2 and calls2[1]["messages"][0]["text"] == "ข้อความสำรองของการ์ด", str(calls2)[:200])

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
