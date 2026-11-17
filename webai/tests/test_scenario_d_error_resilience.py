# -*- coding: utf-8 -*-
"""OrgChat AI — Scenario D: Error Resilience Test Suite
Tests error handling:
1. AI provider failures (429 quota exhaustion, timeout, 503 outage)
2. Google Drive token expiration / revocation (clean 400/401 with Thai message, no 500)
3. LINE API errors (400, 429, 500) handled without crashing
4. Corrupted and 0-byte file uploads rejected with 400
"""
import io
import json
import os
import secrets
import sys
import tempfile
from pathlib import Path
import pytest
import requests

WEBAI = Path(__file__).resolve().parent.parent
if str(WEBAI) not in sys.path:
    sys.path.insert(0, str(WEBAI))


@pytest.fixture(scope="module")
def app_env():
    tmp = tempfile.mkdtemp(prefix="sc_d_")
    db_path = str(Path(tmp) / "sc_d.db")
    data_dir = str(Path(tmp) / "data")
    os.environ["DB_PATH"] = db_path
    os.environ["DATA_DIR"] = data_dir
    os.environ["VECTOR_BACKEND"] = "python"
    os.environ["AI_EMBEDDING_PROVIDER"] = "local"
    os.environ["FLASK_SECRET_KEY"] = secrets.token_hex(16)
    os.environ["BASE_URL"] = "https://openchat.sbs"
    for k in ("REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON", "GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"):
        os.environ.pop(k, None)

    import app_server, database, rag_engine
    import routes.auth as RA
    import routes.chat as RC
    import routes.file_upload as FU
    import routes.line_webhook as LW
    import billing

    billing.has_feature = lambda org_id, feat: True
    billing.check_usage_allowed = lambda org_id, feat: (True, 0, 100)

    RA._limiter.enabled = False
    for lim in getattr(app_server.app, "extensions", {}).get("limiter", []) or []:
        try:
            lim.enabled = False
        except Exception:
            pass

    app = app_server.app
    app.config["TESTING"] = True

    # Seed admin user & org
    PW = "Password123!"
    database.admin_create_user("admin_d", PW, role="admin", email="admin_d@test.com", display_name="Admin D")
    org_id, _ = database.create_organization("Org D", "admin_d")
    LINE_ID = "U_LINE_D_" + "9" * 20
    database.link_line_user("admin_d", LINE_ID)

    client = app.test_client()
    client.post("/api/login", json={"username": "admin_d", "password": PW})
    csrf = client.get("/api/csrf-token").get_json()["csrf_token"]
    headers = {"X-CSRF-Token": csrf}

    yield {
        "client": client,
        "headers": headers,
        "org_id": org_id,
        "line_id": LINE_ID,
        "RC": RC,
        "FU": FU,
        "LW": LW,
        "rag_engine": rag_engine,
        "database": database,
    }


def test_ai_provider_quota_429_returns_polite_thai_message(app_env):
    """When AI provider hits 429 quota exhaustion, web chat must yield polite Thai message, not crash."""
    RC = app_env["RC"]
    client = app_env["client"]
    headers = app_env["headers"]

    class Mock429Provider:
        def chat_stream(self, *a, **k):
            raise Exception("429 Resource has been exhausted (check quota or rate limit)")

    orig_provider = RC.ai_providers.get_provider
    RC.ai_providers.get_provider = lambda *a, **k: Mock429Provider()

    try:
        res = client.post("/api/chat", json={"message": "สวัสดีครับ ถามข้อความ"}, headers=headers)
        assert res.status_code == 200
        body = res.get_data(as_text=True)
        assert "error" in body
        body_decoded = body.encode("utf-8").decode("unicode_escape")
        assert ("การใช้งานหนาแน่น" in body_decoded or "รอสักครู่" in body_decoded or "ติดต่อผู้ดูแลระบบ" in body_decoded)
    finally:
        RC.ai_providers.get_provider = orig_provider


def test_ai_provider_timeout_degrades_gracefully(app_env):
    """When AI provider times out, chat stream must catch exception and yield error event without 500."""
    RC = app_env["RC"]
    client = app_env["client"]
    headers = app_env["headers"]

    class MockTimeoutProvider:
        def chat_stream(self, *a, **k):
            raise TimeoutError("AI connection timed out after 30 seconds")

    orig_provider = RC.ai_providers.get_provider
    RC.ai_providers.get_provider = lambda *a, **k: MockTimeoutProvider()

    try:
        res = client.post("/api/chat", json={"message": "ทดสอบ timeout"}, headers=headers)
        assert res.status_code == 200
        body = res.get_data(as_text=True)
        assert "error" in body
    finally:
        RC.ai_providers.get_provider = orig_provider


def test_line_bot_ai_outage_replies_polite_thai_apology(app_env):
    """When AI provider fails during LINE processing, bot replies with polite Thai message and doesn't crash."""
    LW = app_env["LW"]
    line_id = app_env["line_id"]

    sent = []
    orig_reply = LW.reply_to_line
    LW.reply_to_line = lambda tok, msg, *a, **k: sent.append(msg if isinstance(msg, str) else str(msg))

    def failing_ai(*a, **k):
        raise Exception("503 Backend Service Unavailable")

    LW.ai_providers.generate_response = failing_ai

    try:
        LW.process_line_command("ถามข้อมูลสินค้า", line_id, "tok_outage")
        assert len(sent) > 0
        msg = sent[0]
        assert "ขออภัย" in msg and "ลองใหม่อีกครั้ง" in msg
    finally:
        LW.reply_to_line = orig_reply


def test_google_drive_token_expired_returns_401_with_thai_message(app_env):
    """When Google Drive token is expired or revoked, /api/drive/contents returns 401/400 with Thai explanation (not 500)."""
    FU = app_env["FU"]
    client = app_env["client"]
    headers = app_env["headers"]
    import google_drive_service

    class MockDriveFiles:
        def get(self, *a, **k):
            raise Exception("invalid_grant: Token has been expired or revoked.")

    class MockDriveService:
        def files(self):
            return MockDriveFiles()

    orig_drive_prop = FU.GoogleWorkspaceManager.drive_service
    orig_list = google_drive_service.list_folder_contents
    orig_get_auth_err = FU.google_manager.get_auth_error

    FU.google_manager.get_auth_error = lambda *a, **k: None
    FU.GoogleWorkspaceManager.drive_service = property(lambda self: MockDriveService())
    google_drive_service.list_folder_contents = lambda *a, **k: (_ for _ in ()).throw(Exception("invalid_grant: Token has been expired or revoked."))

    try:
        res = client.get("/api/drive/contents?folder_id=root", headers=headers)
        assert res.status_code in (400, 401)
        data = res.get_json()
        assert data["ok"] is False
        assert "หมดอายุ" in data["error"] or "เพิกถอน" in data["error"]
    finally:
        FU.GoogleWorkspaceManager.drive_service = orig_drive_prop
        google_drive_service.list_folder_contents = orig_list
        FU.google_manager.get_auth_error = orig_get_auth_err


def test_line_api_errors_400_429_500_handled_without_crash(app_env):
    """When LINE Messaging API returns 400, 429, or 500, reply_to_line catches and logs without crashing."""
    LW = app_env["LW"]

    class MockResp:
        def __init__(self, code, text):
            self.status_code = code
            self.text = text

    orig_post = requests.post
    try:
        # 400 Bad Request
        requests.post = lambda url, *a, **k: MockResp(400, '{"message":"Invalid replyToken"}')
        LW.reply_to_line("tok_400", "ทดสอบ 400", fallback_text="ข้อความสำรอง")

        # 429 Rate Limit
        requests.post = lambda url, *a, **k: MockResp(429, '{"message":"Rate limit"}')
        LW.reply_to_line("tok_429", "ทดสอบ 429")

        # 500 Internal Outage
        requests.post = lambda url, *a, **k: MockResp(500, '{"message":"Internal Server Error"}')
        LW.reply_to_line("tok_500", "ทดสอบ 500")
    finally:
        requests.post = orig_post


def test_corrupt_and_zero_byte_file_uploads_rejected_with_400(app_env):
    """0-byte files, corrupt PDFs, and disguised scripts must be rejected with HTTP 400 and clear error messages."""
    client = app_env["client"]
    headers = app_env["headers"]
    rag_engine = app_env["rag_engine"]

    # 1. 0-byte .txt
    r1 = client.post("/api/upload", data={"files": (io.BytesIO(b""), "empty.txt"), "department": "General"},
                     content_type="multipart/form-data", headers=headers)
    assert r1.status_code == 400
    assert "0 Bytes" in r1.get_json()["error"]

    # 2. 0-byte .pdf
    r2 = client.post("/api/upload", data={"files": (io.BytesIO(b""), "empty.pdf"), "department": "General"},
                     content_type="multipart/form-data", headers=headers)
    assert r2.status_code == 400
    assert "0 Bytes" in r2.get_json()["error"]

    # 3. Corrupt PDF
    r3 = client.post("/api/upload", data={"files": (io.BytesIO(b"NOT_A_VALID_PDF_HEADER"), "corrupt.pdf"), "department": "General"},
                     content_type="multipart/form-data", headers=headers)
    assert r3.status_code == 400
    assert "%PDF" in r3.get_json()["error"]

    # 4. Disguised executable / PHP script
    r4 = client.post("/api/upload", data={"files": (io.BytesIO(b"<?php phpinfo(); ?>"), "avatar.jpg"), "department": "General"},
                     content_type="multipart/form-data", headers=headers)
    assert r4.status_code == 400
    assert "สคริปต์" in r4.get_json()["error"]

    # 5. Verify none recorded in KB metadata
    meta = rag_engine._load_meta()
    bad_names = {"empty.txt", "empty.pdf", "corrupt.pdf", "avatar.jpg"}
    found_bad = [m["name"] for m in meta.values() if m.get("name") in bad_names]
    assert len(found_bad) == 0
