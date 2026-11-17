# -*- coding: utf-8 -*-
"""Scenario C: LINE Bot Full Matrix Testing.
Users (Bound, Unbound, Deactivated) x Commands (/link, search, search <name>, product inquiry, off-topic, greeting, sticker, image).
Verifies payload length <= 5000, valid HTTP/HTTPS URIs, deactivated suspension enforcement, and proper routing.
"""
import os
import re
import secrets
import sys
import time
from pathlib import Path

assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "https://openchat.sbs")
os.environ["VECTOR_BACKEND"] = "python"
os.environ["AI_EMBEDDING_PROVIDER"] = "local"
sys.path.insert(0, os.getcwd())

import app_server, database, rag_engine  # noqa: E402
import routes.line_webhook as LW  # noqa: E402
import billing  # noqa: E402

billing.has_feature = lambda org_id, feature: True
billing.check_usage_allowed = lambda org_id, feature: (True, 0, 100)

FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


# ── Database & Users Setup ───────────────────────────────────────
PW = "Password123!"
database.admin_create_user("alice_c", PW, role="admin", email="alice@testmatrix.com", display_name="Alice C")
database.admin_create_user("dave_c", PW, role="user", email="dave@testmatrix.com", display_name="Dave Deactivated")
org_id, _ = database.create_organization("Matrix Org", "alice_c")
database.add_org_member(org_id, "dave_c", "member", "alice_c")

ALICE_LINE = "U_ALICE_" + "1" * 24
DAVE_LINE = "U_DAVE_" + "2" * 24
UNBOUND_LINE = "U_UNBOUND_" + "3" * 22

database.link_line_user("alice_c", ALICE_LINE)
database.link_line_user("dave_c", DAVE_LINE)
# Deactivate Dave
database.admin_update_user("dave_c", is_active=0)

# ── Seed Knowledge Base ──────────────────────────────────────────
pub_cat = database.add_category("สินค้าทั่วไป", visibility="public", created_by="alice_c", org_id=org_id)
upload_dir = Path(os.environ["DATA_DIR"]) / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
sample_file = upload_dir / "คู่มือสินค้า_duit_น้ำพุแมว.txt"
sample_file.write_text("คู่มือสินค้า duit น้ำพุแมวอัตโนมัติ ความจุน้ำ 2.5 ลิตร ถังพลาสติก PP ปลอดภัย BPA Free", encoding="utf-8")
meta = {
    "fid_duit": {
        "name": "คู่มือสินค้า_duit_น้ำพุแมว.txt",
        "path": str(sample_file),
        "chunks": 1,
        "size": len(sample_file.read_bytes()),
        "type": "txt",
        "department": "General",
        "category_id": pub_cat,
        "organization_id": org_id,
        "status": "ready",
        "timestamp": "2026-11-10T12:00:00"
    }
}
rag_engine._save_meta(meta)

# ── Capture Output Payloads ──────────────────────────────────────
REPLIED_PAYLOADS = []


def mock_reply_to_line(reply_token, message, quick_reply=None, sticker_data=None, dest_id=None, fallback_text=None):
    payload = {
        "reply_token": reply_token,
        "message": message,
        "quick_reply": quick_reply,
        "sticker_data": sticker_data,
        "dest_id": dest_id,
        "fallback_text": fallback_text
    }
    REPLIED_PAYLOADS.append(payload)


LW.reply_to_line = mock_reply_to_line
LW.send_line_push_notification = lambda *a, **k: None
LW.show_loading_animation = lambda *a, **k: None

# Mock AI provider
def mock_gen_resp(*a, **kwargs):
    prompt = kwargs.get("question") or kwargs.get("prompt") or (a[0] if a else "")
    if "duit" in str(prompt):
        return "น้ำพุแมว duit มีความจุน้ำ 2.5 ลิตร ค่ะ"
    return "สวัสดีค่ะ มีอะไรให้น้องพั้นช่วยดูแล หรือค้นหาข้อมูลในระบบ สอบถามได้ตลอดเลยนะคะ"

try:
    LW.ai_providers.generate_response = mock_gen_resp
except Exception:
    pass


def send_cmd(uid, text):
    REPLIED_PAYLOADS.clear()
    LW.process_line_command(text, uid, "reply_tok_123")
    return list(REPLIED_PAYLOADS)


def send_event(event_dict):
    REPLIED_PAYLOADS.clear()
    LW.process_line_event(event_dict)
    return list(REPLIED_PAYLOADS)


def extract_all_text(payloads):
    texts = []
    for p in payloads:
        msg = p.get("message")
        if isinstance(msg, str):
            texts.append(msg)
        elif isinstance(msg, dict):
            if "text" in msg:
                texts.append(msg["text"])
            elif "altText" in msg:
                texts.append(msg["altText"])
        elif isinstance(msg, list):
            for m in msg:
                if isinstance(m, dict) and "text" in m:
                    texts.append(m["text"])
    return " ".join(texts)


def extract_all_uris(payloads):
    uris = []
    for p in payloads:
        # Check quick_reply
        qr = p.get("quick_reply") or {}
        for itm in qr.get("items", []):
            act = itm.get("action", {})
            if act.get("type") == "uri" and "uri" in act:
                uris.append(act["uri"])
        # Check message content for flex uris
        msg = p.get("message")
        msg_str = str(msg)
        found_uris = re.findall(r'https?://[^\s\'"<>]+', msg_str)
        uris.extend(found_uris)
    return uris


# ── TEST MATRIX ──────────────────────────────────────────────────
# 1. DEACTIVATED USER (DAVE)
# Every action must result in a suspension message, never leak files or answer queries
dave_commands = [
    ("/link", send_cmd(DAVE_LINE, "/link")),
    ("ค้นหา", send_cmd(DAVE_LINE, "ค้นหา")),
    ("ค้นหา duit", send_cmd(DAVE_LINE, "ค้นหา duit")),
    ("ถามข้อมูลสินค้า", send_cmd(DAVE_LINE, "น้ำพุแมว duit มีความจุน้ำเท่าไร")),
    ("ถามนอกเรื่อง", send_cmd(DAVE_LINE, "แนะนำสูตรทำต้มยำกุ้งหน่อย")),
    ("ทักทาย", send_cmd(DAVE_LINE, "สวัสดีครับ")),
    ("สติกเกอร์", send_event({"type": "message", "replyToken": "tok", "source": {"userId": DAVE_LINE, "type": "user"}, "message": {"type": "sticker", "packageId": "1", "stickerId": "1"}})),
    ("รูปภาพ", send_event({"type": "message", "replyToken": "tok", "source": {"userId": DAVE_LINE, "type": "user"}, "message": {"type": "image", "id": "img_dave"}})),
]

for cmd_name, payloads in dave_commands:
    text = extract_all_text(payloads)
    check(f"Dave (deactivated) x {cmd_name} rejected with suspension", "ระงับการใช้งานชั่วคราว" in text or "ไม่มีสิทธิ์" in text, text[:80])
    check(f"Dave (deactivated) x {cmd_name} payload length <= 5000", len(text) <= 5000, f"len={len(text)}")
    check(f"Dave (deactivated) x {cmd_name} does not leak duit", "2.5 ลิตร" not in text and "BPA Free" not in text)

# 2. UNBOUND USER
unbound_commands = [
    ("/link", send_cmd(UNBOUND_LINE, "/link")),
    ("ค้นหา", send_cmd(UNBOUND_LINE, "ค้นหา")),
    ("ค้นหา duit", send_cmd(UNBOUND_LINE, "ค้นหา duit")),
    ("ถามข้อมูลสินค้า", send_cmd(UNBOUND_LINE, "น้ำพุแมว duit มีความจุน้ำเท่าไร")),
    ("ถามนอกเรื่อง", send_cmd(UNBOUND_LINE, "แนะนำสูตรทำต้มยำกุ้งหน่อย")),
    ("ทักทาย", send_cmd(UNBOUND_LINE, "สวัสดีครับ")),
    ("สติกเกอร์", send_event({"type": "message", "replyToken": "tok", "source": {"userId": UNBOUND_LINE, "type": "user"}, "message": {"type": "sticker", "packageId": "1", "stickerId": "1"}})),
    ("รูปภาพ", send_event({"type": "message", "replyToken": "tok", "source": {"userId": UNBOUND_LINE, "type": "user"}, "message": {"type": "image", "id": "img_unbound"}})),
]

for cmd_name, payloads in unbound_commands:
    text = extract_all_text(payloads)
    uris = extract_all_uris(payloads)
    check(f"Unbound x {cmd_name} informs to link or shows onboarding", "ผูกบัญชี" in text or "เชื่อมต่อ" in text or "ยินดีต้อนรับ" in text, text[:80])
    check(f"Unbound x {cmd_name} payload length <= 5000", len(text) <= 5000, f"len={len(text)}")
    check(f"Unbound x {cmd_name} URIs valid http/https", all(u.startswith("http://") or u.startswith("https://") for u in uris), str(uris))
    check(f"Unbound x {cmd_name} does not leak org files", "2.5 ลิตร" not in text and "BPA Free" not in text)

# 3. BOUND USER (ALICE)
# 3.1 /link
alice_link = send_cmd(ALICE_LINE, "/link")
text_link = extract_all_text(alice_link)
check("Alice (bound) x /link confirms already linked", "ผูกบัญชีไว้เรียบร้อยแล้ว" in text_link, text_link[:80])

# 3.2 ค้นหา (empty search)
alice_search_empty = send_cmd(ALICE_LINE, "ค้นหา")
text_se = extract_all_text(alice_search_empty)
check("Alice (bound) x ค้นหา prompts for keyword or lists files", "ค้นหา" in text_se or "ไฟล์" in text_se or "คลัง" in text_se, text_se[:80])

# 3.3 ค้นหา duit (file search)
alice_search_duit = send_cmd(ALICE_LINE, "ค้นหา duit")
text_sd = extract_all_text(alice_search_duit)
check("Alice (bound) x ค้นหา duit finds duit file", "duit" in text_sd or "น้ำพุแมว" in text_sd, text_sd[:80])

# 3.4 ถามข้อมูลสินค้า (product inquiry)
alice_prod = send_cmd(ALICE_LINE, "น้ำพุแมว duit มีความจุน้ำเท่าไร")
text_prod = extract_all_text(alice_prod)
check("Alice (bound) x ถามข้อมูลสินค้า answers with product detail", "2.5" in text_prod or "duit" in text_prod, text_prod[:80])

# 3.5 ถามนอกเรื่อง (off-topic inquiry)
alice_offtopic = send_cmd(ALICE_LINE, "แนะนำสูตรทำต้มยำกุ้งหน่อย")
text_off = extract_all_text(alice_offtopic)
check("Alice (bound) x ถามนอกเรื่อง polite reply without crash", len(text_off) > 0 and len(text_off) <= 5000, text_off[:80])

# 3.6 ทักทาย (greeting)
alice_greet = send_cmd(ALICE_LINE, "สวัสดีครับ")
text_gr = extract_all_text(alice_greet)
check("Alice (bound) x ทักทาย responds with friendly greeting", "สวัสดี" in text_gr or "น้องพั้น" in text_gr, text_gr[:80])

# 3.7 สติกเกอร์ (sticker event)
alice_sticker = send_event({"type": "message", "replyToken": "tok", "source": {"userId": ALICE_LINE, "type": "user"}, "message": {"type": "sticker", "packageId": "1", "stickerId": "1"}})
text_stk = extract_all_text(alice_sticker)
check("Alice (bound) x สติกเกอร์ acknowledges sticker politely", "สติกเกอร์" in text_stk or "น้องพั้น" in text_stk, text_stk[:80])

# 3.8 รูปภาพ (image event)
# Bound user sends image -> triggers batching or receipt check without 500 crash
alice_img = send_event({"type": "message", "replyToken": "tok", "source": {"userId": ALICE_LINE, "type": "user"}, "message": {"type": "image", "id": "img_alice"}})
check("Alice (bound) x รูปภาพ processed without crash", True)

print("ALL PASSED" if not FAILS else f"FAILED: {len(FAILS)} checks")
sys.exit(1 if FAILS else 0)
