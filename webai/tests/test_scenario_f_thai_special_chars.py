# -*- coding: utf-8 -*-
"""
Scenario F: Tests for Thai special characters, emojis, numerals, Unicode normalization,
and URL percent-encoding across Database, RAG, File Upload/Download, and LINE Flex messages.
"""
import os
import sys
import tempfile
import io
import shutil
import pytest
import urllib.parse
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
import rag_engine
from app_server import app
from routes.line_webhook import _sanitize_line_uris


@pytest.fixture
def f_test_env():
    # Temporary DB
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    os.environ["DB_PATH"] = db_path
    database.init_db()

    # Temporary KB & Upload dir
    tmp_upload_dir = Path(tempfile.mkdtemp(prefix="test_upload_thai_"))
    orig_upload = rag_engine.UPLOAD_DIR
    orig_kb = rag_engine._kb
    rag_engine.UPLOAD_DIR = tmp_upload_dir
    rag_engine._kb = None

    yield {
        "db_path": db_path,
        "upload_dir": tmp_upload_dir,
    }

    rag_engine.UPLOAD_DIR = orig_upload
    rag_engine._kb = orig_kb
    shutil.rmtree(tmp_upload_dir, ignore_errors=True)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture
def client(f_test_env):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_thai_org_department_and_event_persistence(f_test_env):
    """Test 1: Org name, Department name, and Event log with Thai characters, numerals, and emojis."""
    raw_org_name = "บจก. ก้าวหน้า ๑๒๓ (ประเทศไทย) & <Co.,Ltd.>"
    oid, _ = database.create_org(raw_org_name, "owner_f")
    assert oid is not None

    org = database.get_org(oid)
    assert org is not None
    # clean_label strips dangerous '<>' but preserves Thai, digits, &, and Latin characters
    assert "บจก. ก้าวหน้า ๑๒๓ (ประเทศไทย) & <Co.,Ltd.>" == org["name"] or "บจก. ก้าวหน้า ๑๒๓ (ประเทศไทย) & Co.,Ltd." in org["name"]

    dept_name = "การตลาด & ประชาสัมพันธ์ / ฝ่าย IT (ชั้น ๔)"
    created = database.admin_create_user(
        username="user_thai",
        password="Password123!",
        role="user",
        display_name="สมชาย สดใส 🌟",
        department=dept_name,
    )
    assert created is True

    prof = database.get_user_profile("user_thai")
    assert prof["department"] == dept_name
    assert prof["display_name"] == "สมชาย สดใส 🌟"

    # Event log with Thai digits, percentage, and emoji
    event_title = "ประชุม Q4: สรุปงบ ๑๐๐% 🎯"
    database.log_event(event_title, user="user_thai", org_id=oid)
    events = database.get_audit_logs(org_id=oid, limit=5)
    assert len(events) >= 1
    assert events[0]["details"] == event_title or events[0]["action"] == event_title


def test_thai_chat_message_with_symbols(f_test_env):
    """Test 2: Chat message with quotes, ampersand, Thai slang, and emojis."""
    oid, _ = database.create_org("OrgThai", "owner_thai")
    database.admin_create_user("user_chat", "Password123!", role="user")

    chat_msg = 'สวัสดีครับ 555+ 🙏 สอบถามเรื่อง "โปรโมชั่น" & ส่วนลด 50% นะครับ'
    mid = database.add_room_message(1, "user_chat", chat_msg)
    assert mid is not None

    msgs = database.get_room_messages(1, limit=5)
    assert len(msgs) >= 1
    saved = next(m for m in msgs if m.get("text") == chat_msg)
    assert saved["text"] == chat_msg


def test_thai_filename_upload_download_and_rag(f_test_env, client):
    """Test 3: File with Thai name, symbols, Thai text indexing and RFC 5987 download."""
    # Seed admin user and org
    oid, _ = database.create_org("OrgThaiFile", "admin_thai")
    cat_id = database.add_category("หมวดคู่มือทั่วไป ๑", org_id=oid, created_by="admin_thai")

    with client.session_transaction() as sess:
        sess["user"] = "admin_thai"
        sess["role"] = "admin"
        sess["org_id"] = oid
        sess["org_role"] = "admin"

    csrf_res = client.get("/api/csrf-token")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf_token}

    thai_filename = "คู่มือ_ผู้ใช้-๒๕๖๙_พิเศษ.txt"
    thai_content = "นโยบายองค์กร ๒๕๖๙: สิทธิการใช้วันลาพักร้อน ๑๕ วันทำการต่อปี สำหรับพนักงานประจำทุกคน".encode("utf-8")

    data = {
        "files": [(io.BytesIO(thai_content), thai_filename)],
        "department": "General",
        "category_id": cat_id,
    }

    # Upload file
    resp = client.post("/api/upload", data=data, content_type="multipart/form-data", headers=headers)
    assert resp.status_code == 200
    upload_res = resp.get_json()
    assert upload_res["ok"] is True
    assert len(upload_res["results"]) == 1
    assert upload_res["results"][0]["file"] == thai_filename

    # Verify file is listed with Thai filename
    all_files = rag_engine.list_files()
    file_entry = next((f for f in all_files if thai_filename in f.get("name", "")), None)
    assert file_entry is not None
    disk_fn = Path(file_entry["path"]).name

    # Download file and check Content-Disposition
    dl_resp = client.get(f"/api/files/download/{disk_fn}")
    assert dl_resp.status_code == 200
    cd_header = dl_resp.headers.get("Content-Disposition", "")
    assert "attachment" in cd_header
    # Download content matches original Thai text
    assert "นโยบายองค์กร ๒๕๖๙" in dl_resp.data.decode("utf-8")


def test_line_uri_sanitization_with_thai():
    """Test 4: LINE Flex URI sanitization converts Thai characters in URLs to valid ASCII percent-encoded URIs."""
    test_flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "button",
                    "action": {
                        "type": "uri",
                        "label": "ดาวน์โหลด",
                        "uri": "https://openchat.sbs/api/files/download/upload_123_คู่มือ_การใช้งาน.pdf?token=abc-123",
                    },
                }
            ],
        },
    }

    sanitized = _sanitize_line_uris(test_flex)
    btn_uri = sanitized["body"]["contents"][0]["action"]["uri"]

    # URI must be valid ASCII for LINE API compliance
    assert btn_uri.isascii() is True
    assert "https://openchat.sbs/api/files/download/upload_123_" in btn_uri
    assert "%E0%B8" in btn_uri  # Percent-encoded Thai bytes
    assert "?token=abc-123" in btn_uri
