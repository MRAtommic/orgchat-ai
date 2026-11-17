# -*- coding: utf-8 -*-
"""Scenario A: New User End-to-End Journey from Zero.
Register -> Create Org -> Invite Member -> Upload 3 sample product files -> Query RAG with citations & off-topic verification.
"""
import io
import json
import os
import secrets
import sys
import time
from pathlib import Path

assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["VECTOR_BACKEND"] = "python"
os.environ["AI_EMBEDDING_PROVIDER"] = "local"
sys.path.insert(0, os.getcwd())

import app_server, database, rag_engine  # noqa: E402
import routes.auth as RA  # noqa: E402
import routes.chat as RC  # noqa: E402
import routes.file_upload as FU  # noqa: E402
import billing  # noqa: E402

RA._limiter.enabled = False
for lim in getattr(app_server.app, "extensions", {}).get("limiter", []) or []:
    try:
        lim.enabled = False
    except Exception:
        pass

app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "scenario-a-test"}
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


client = app.test_client()

# ── 1. Register Alice & Create Organization ──────────────────────
signup_data = {
    "org_name": "HeartWarming Corp",
    "display_name": "Alice Admin",
    "username": "alice_hw",
    "password": "Password123!",
    "confirm_password": "Password123!"
}
res_signup = client.post("/api/org/signup", json=signup_data, headers=H)
check("1. Signup Alice and create HeartWarming Corp", res_signup.status_code == 200 and res_signup.get_json().get("ok") is True)
signup_json = res_signup.get_json() or {}
org_id = signup_json.get("org_id")
check("1.1 Valid org_id created", org_id is not None and org_id > 0, str(org_id))

# Get CSRF token for Alice
res_csrf = client.get("/api/csrf-token", headers=H)
csrf_token = res_csrf.get_json().get("csrf_token")
alice_headers = dict(H, **{"X-CSRF-Token": csrf_token})

# ── 2. Member Onboarding: Add Bob ────────────────────────────────
database.admin_create_user("bob_hw", "Password123!", role="user", email="bob@heartwarming.com", display_name="Bob Member")
database.add_org_member(org_id, "bob_hw", "member", "alice_hw")
check("2. Bob joined HeartWarming Corp as member", database.is_org_member(org_id, "bob_hw"))

# ── 3. Upload 3 Sample Product Files ─────────────────────────────
sample_dir = Path("เอกสาร โปรจบ") / "เอกสารสินค้าตัวอย่างสำหรับอัปโหลด"
sample_files = [
    "คู่มือสินค้า_duit_น้ำพุแมว.txt",
    "คู่มือสินค้า_thumb_toe_ถุงเท้าพิลาทิส.txt",
    "ภาพรวมแบรนด์และสินค้า_ฮาร์ทวอมมิ่ง.txt"
]

for sname in sample_files:
    sfile = sample_dir / sname
    check(f"3. Sample file exists: {sname}", sfile.exists())
    content = sfile.read_bytes()
    data = {
        "files": (io.BytesIO(content), sname),
        "department": "General"
    }
    res_upload = client.post("/api/upload", data=data, content_type="multipart/form-data", headers=alice_headers)
    check(f"3. Upload {sname} via API", res_upload.status_code == 200 and res_upload.get_json().get("ok") is True, res_upload.get_data(as_text=True))

# Wait for background ingestion workers to finish indexing all 3 files
for _ in range(30):
    all_files = rag_engine.list_files()
    org_files = [f for f in all_files if f.get("organization_id") == org_id]
    if len(org_files) == 3 and all(f.get("status") == "ready" and f.get("chunks", 0) > 0 for f in org_files):
        break
    time.sleep(0.5)

all_files = rag_engine.list_files()
org_files = [f for f in all_files if f.get("organization_id") == org_id]
check("3.1 All 3 files registered in KB", len(org_files) == 3, f"count={len(org_files)}")
for f in org_files:
    check(f"3.2 File {f.get('name')} ready with chunks", f.get("status") == "ready" and f.get("chunks", 0) > 0, f"status={f.get('status')} chunks={f.get('chunks')}")

# ── 4. Query RAG Retrieval with Citations ────────────────────────
# Query 1: Duit Cat Fountain
ctx1, src1 = rag_engine.retrieve_context("น้ำพุแมว duit มีความจุน้ำเท่าไร", where={"organization_id": org_id})
check("4.1 Query 1 (duit fountain capacity) retrieved context", "2.5" in ctx1 or "2.5 ลิตร" in ctx1, ctx1[:100])
check("4.1 Query 1 citation contains duit file", any("duit" in (s.get("name") or s.get("file_name", "")) for s in src1), str(src1))

# Query 2: Thumb Toe socks
ctx2, src2 = rag_engine.retrieve_context("ถุงเท้า thumb toe มีคุณสมบัติเด่นอะไรบ้าง", where={"organization_id": org_id})
check("4.2 Query 2 (thumb toe socks features) retrieved context", "พิลาทิส" in ctx2 or "กันลื่น" in ctx2 or "นิ้วโป้ง" in ctx2, ctx2[:100])
check("4.2 Query 2 citation contains thumb toe file", any("thumb_toe" in (s.get("name") or s.get("file_name", "")) for s in src2), str(src2))

# Query 3: HeartWarming overview
ctx3, src3 = rag_engine.retrieve_context("บริษัท ฮาร์ทวอมมิ่ง ดำเนินธุรกิจอะไร และมีแบรนด์สินค้าอะไรบ้าง", where={"organization_id": org_id})
check("4.3 Query 3 (heartwarming overview) retrieved context", "ฮาร์ทวอมมิ่ง" in ctx3 and "duit" in ctx3, ctx3[:100])
check("4.3 Query 3 citation contains brand overview file", any("ฮาร์ทวอมมิ่ง" in (s.get("name") or s.get("file_name", "")) for s in src3), str(src3))

# Query 4: Off-topic query (สูตรทำต้มยำกุ้ง)
ctx4, src4 = rag_engine.retrieve_context("แนะนำวิธีปรุงต้มยำกุ้งน้ำข้นสูตรโบราณ", where={"organization_id": org_id})
# Should not contain any relevant culinary advice in context from our 3 product files
check("4.4 Query 4 (off-topic culinary) has no recipe content", "ตะไคร้" not in ctx4 and "น้ำพริกเผา" not in ctx4)

# ── 5. End-to-End Chat API with Mocked AI Generation ──────────────
class MockAIProvider:
    def chat_stream(self, question, history, system_prompt, **kwargs):
        q = str(question)
        if "duit" in q:
            yield "น้ำพุแมวอัตโนมัติแบรนด์ duit มีความจุน้ำ 2.5 ลิตร ค่ะ (อ้างอิง: คู่มือสินค้า_duit_น้ำพุแมว.txt)"
        elif "ต้มยำกุ้ง" in q:
            yield "ขออภัยค่ะ ไม่พบข้อมูลเกี่ยวกับสูตรทำต้มยำกุ้งในเอกสารขององค์กร HeartWarming Corp ค่ะ"
        else:
            yield "ตอบคำถามเรียบร้อยค่ะ"

orig_get_provider = RC.ai_providers.get_provider
RC.ai_providers.get_provider = lambda *a, **k: MockAIProvider()

def parse_sse(stream_text):
    full_text = ""
    sources = []
    for line in stream_text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            try:
                payload = json.loads(line[6:])
                if "content" in payload:
                    full_text += payload["content"]
                if "sources" in payload:
                    sources = payload["sources"]
            except Exception:
                pass
    return full_text, sources

try:
    # 5.1 Alice queries chat for duit fountain
    chat_res1 = client.post("/api/chat", json={"message": "น้ำพุแมว duit มีความจุน้ำเท่าไร"}, headers=alice_headers)
    chat_body1 = chat_res1.get_data(as_text=True)
    text1, sources1 = parse_sse(chat_body1)
    check("5.1 Chat response 200 for duit query", chat_res1.status_code == 200)
    check("5.1 Chat stream contains answer 2.5 ลิตร", "2.5 ลิตร" in text1, text1)
    check("5.1 Chat stream includes cited source duit manual", any("duit" in s.get("name", "") for s in sources1), str(sources1))

    # 5.2 Alice queries chat for off-topic tom yum
    chat_res2 = client.post("/api/chat", json={"message": "วิธีทำต้มยำกุ้งน้ำข้นสูตรโบราณ"}, headers=alice_headers)
    chat_body2 = chat_res2.get_data(as_text=True)
    text2, sources2 = parse_sse(chat_body2)
    check("5.2 Chat response 200 for off-topic query", chat_res2.status_code == 200)
    check("5.2 Chat stream answers with 'ไม่พบข้อมูล'", "ไม่พบข้อมูล" in text2, text2)
    check("5.2 Off-topic query does not cite product manuals", not any("duit" in s.get("name", "") for s in sources2), str(sources2))
finally:
    RC.ai_providers.get_provider = orig_get_provider

print("ALL PASSED" if not FAILS else f"FAILED: {len(FAILS)} checks")
sys.exit(1 if FAILS else 0)
