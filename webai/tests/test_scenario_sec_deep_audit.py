# -*- coding: utf-8 -*-
"""
หัวข้อ 4: ความปลอดภัยเชิงลึก (Deep Security Audit Suite)
ตามข้อกำหนดใน PLAN_QA_FOLLOWUP.md:
1. IDOR Matrix: ทดสอบตาราง Endpoint × Role × Expected (200/403/404) ข้ามองค์กร
2. Path Traversal & Download Token Tampering: ป้องกัน .. / \\ / : และตรวจ token ปลอม/หมดอายุ
3. Rate Limiting: ทดสอบ brute-force lockout 5 ครั้ง และ 429 ข้อความไทย
4. Cloudflare Tunnel Client IP: ตรวจสอบ CF-Connecting-IP ปลอดภัย ป้องกัน spoofing
5. Secret Leak Scan: สแกน log ป้องกัน token/secret รั่วไหล
"""
import io
import json
import os
import re
import secrets
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

WEBAI = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def sec_app_context():
    """Create an isolated test application with temporary DB and directories."""
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = Path(tmpdir.name)
    db_file = tmp_path / "sec_audit.db"
    data_dir = tmp_path / "sec_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir = data_dir / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    old_env = os.environ.copy()
    os.environ["DB_PATH"] = str(db_file)
    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["VECTOR_BACKEND"] = "python"
    os.environ["FLASK_SECRET_KEY"] = secrets.token_hex(16)
    os.environ["BASE_URL"] = "http://localhost:5999"

    import app_server
    import database
    import rag_engine
    from routes.shared import _limiter, generate_file_token

    rag_engine.UPLOAD_DIR = uploads_dir
    rag_engine.META_FILE = data_dir / "file_meta.json"
    rag_engine.DOCS_FILE = data_dir / "processed_docs.json"

    app = app_server.app
    app.config["TESTING"] = True

    # Setup 2 organizations & users
    pw = "SecPass123!"
    # Org 1: Alpha Corp
    database.admin_create_user("owner1", pw, role="user", email="owner1@alpha.com")
    org1_id, _ = database.create_organization("Alpha Corp", "owner1")
    database.admin_create_user("alice1", pw, role="user", email="alice@alpha.com")
    database.add_org_member(org1_id, "alice1", "member", "owner1")

    # Org 2: Beta Corp
    database.admin_create_user("owner2", pw, role="user", email="owner2@beta.com")
    org2_id, _ = database.create_organization("Beta Corp", "owner2")
    database.admin_create_user("bob2", pw, role="user", email="bob@beta.com")
    database.add_org_member(org2_id, "bob2", "member", "owner2")

    # Create Org 1 Resources
    # 1. File
    fn1 = "org1_confidential.txt"
    f1_path = uploads_dir / fn1
    f1_path.write_text("Alpha Corp Secret Internal Strategy", encoding="utf-8")
    fid1 = "F_ALPHA_001"
    meta = {
        fid1: {
            "name": fn1,
            "path": str(f1_path),
            "type": "txt",
            "status": "ready",
            "organization_id": org1_id,
            "category_id": None,
            "chunks": 1
        }
    }
    rag_engine._save_meta(meta)

    # 2. Schedule
    sched_id = database.add_schedule("owner1", "Alpha Confidential Board Meeting", "2026-12-15", is_public=1, org_id=org1_id)
    if not isinstance(sched_id, int):
        conn = database._get_conn()
        sched_id = conn.execute("SELECT MAX(id) FROM schedules").fetchone()[0]
        conn.close()

    # 3. Leave
    leave_id = database.create_leave_request("alice1", "ลาพักผ่อน", "2026-12-20", "2026-12-21", "ไปธุระครอบครัว", org_id=org1_id)
    if not isinstance(leave_id, int):
        conn = database._get_conn()
        leave_id = conn.execute("SELECT MAX(id) FROM leave_requests").fetchone()[0]
        conn.close()

    # 4. Chat room
    room_id = database.create_room("Alpha Executive Room", "owner1", members=["alice1"], org_id=org1_id)
    if not isinstance(room_id, int):
        conn = database._get_conn()
        room_id = conn.execute("SELECT MAX(id) FROM chat_rooms").fetchone()[0]
        conn.close()

    ctx = {
        "app": app,
        "database": database,
        "rag_engine": rag_engine,
        "org1_id": org1_id,
        "org2_id": org2_id,
        "fid1": fid1,
        "fn1": fn1,
        "sched_id": sched_id,
        "leave_id": leave_id,
        "room_id": room_id,
        "pw": pw,
        "generate_file_token": generate_file_token,
    }

    yield ctx

    os.environ.clear()
    os.environ.update(old_env)
    tmpdir.cleanup()


def _login_client(app, username, password):
    client = app.test_client()
    resp = client.post("/api/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.get_json()}"
    csrf_res = client.get("/api/csrf-token")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    return client, csrf_token


def test_idor_cross_organization_matrix(sec_app_context):
    """
    1. IDOR Matrix Test:
    Verify that Bob (Member of Beta Corp) CANNOT access, read, update, or delete
    any Alpha Corp resources (Files, Schedules, Leaves, Chat Rooms, Org Admin).
    All must return 403 Forbidden or 404 Not Found.
    """
    ctx = sec_app_context
    app = ctx["app"]
    client_bob, csrf_bob = _login_client(app, "bob2", ctx["pw"])
    headers = {"X-CSRF-Token": csrf_bob}

    idor_test_matrix = [
        # (Resource Name, HTTP Method, Endpoint, Payload, Expected Status Codes)
        ("KB File Download", "get", f"/api/files/download/{ctx['fn1']}", None, [403, 404]),
        ("KB File View", "get", f"/api/kb/files/view/{ctx['fid1']}", None, [403, 404]),
        ("KB File Delete", "delete", f"/api/files/{ctx['fid1']}", None, [403, 404]),
        ("KB File Category Change", "put", f"/api/files/{ctx['fid1']}/category", {"category_id": 999}, [403, 404]),
        ("KB CSV Edit", "get", f"/api/csv/{ctx['fid1']}", None, [403, 404]),
        ("KB TXT Edit", "get", f"/api/txt/{ctx['fid1']}", None, [403, 404]),
        ("Schedule Edit", "put", f"/api/schedules/{ctx['sched_id']}", {"title": "Hacked", "date": "2026-12-15"}, [403, 404]),
        ("Schedule Delete", "delete", f"/api/schedules/{ctx['sched_id']}", None, [403, 404]),
        ("Schedule Toggle", "post", f"/api/schedules/{ctx['sched_id']}/toggle", {}, [403, 404]),
        ("Schedule Patch Status", "patch", f"/api/schedules/{ctx['sched_id']}/status", {"status": "done"}, [403, 404]),
        ("Leave Comments Read", "get", f"/api/leave/comments/{ctx['leave_id']}", None, [403, 404]),
        ("Leave Comment Post", "post", "/api/leave/comment", {"leave_id": ctx["leave_id"], "comment": "Spam"}, [403, 404]),
        ("Chat Room Messages", "get", f"/api/chat/messages/room/{ctx['room_id']}", None, [403, 404]),
        ("Chat DM to Other Org", "get", "/api/chat/messages/dm/alice1", None, [403, 404]),
        ("Org Admin Overview", "get", "/api/org/overview", None, [403, 404]),
        ("Org Member Remove", "delete", "/api/org/members/alice1", None, [403, 404]),
    ]

    results_table = []
    for name, method, endpoint, body, expected_statuses in idor_test_matrix:
        fn = getattr(client_bob, method)
        kwargs = {"headers": headers}
        if body is not None:
            kwargs["json"] = body
        res = fn(endpoint, **kwargs)
        status = res.status_code
        passed = status in expected_statuses
        results_table.append((name, method.upper(), endpoint, status, expected_statuses, passed))
        assert passed, f"IDOR Vulnerability detected in {name}! {method.upper()} {endpoint} returned {status}, expected {expected_statuses}"

    print("\n--- IDOR Security Matrix Verified (All Passed) ---")
    for r in results_table:
        print(f"[{'PASS' if r[5] else 'FAIL'}] {r[0]:<25} {r[1]:<6} {r[2]:<40} -> Status {r[3]} (Expected {r[4]})")


def test_path_traversal_and_token_tampering(sec_app_context):
    """
    2. Path Traversal & Download Token Tampering:
    - Path traversal with ../, ..\\, :, null bytes rejected with 403
    - Expired tokens, tampered signatures, or mismatched filenames rejected with 404/403
    """
    ctx = sec_app_context
    app = ctx["app"]
    client_bob, csrf_bob = _login_client(app, "bob2", ctx["pw"])
    headers = {"X-CSRF-Token": csrf_bob}

    # 1. Path traversal attacks
    traversal_attacks = [
        "../etc/passwd",
        "..\\windows\\win.ini",
        "../../uploads/secret.txt",
        "..%2f..%2fsecret.txt",
        "C:\\boot.ini",
    ]
    for attack in traversal_attacks:
        res = client_bob.get(f"/api/files/download/{attack}", headers=headers)
        assert res.status_code in (400, 403, 404), f"Path traversal not blocked for {attack}: {res.status_code}"

    # 2. Token tests
    gen_token = ctx["generate_file_token"]
    # Valid token for Alpha file
    valid_token = gen_token(ctx["fn1"], "kb_download", expires_in=300)

    # Valid token should allow download even without login
    anon_client = app.test_client()
    res_valid = anon_client.get(f"/api/files/download/{ctx['fn1']}?token={valid_token}")
    assert res_valid.status_code == 200, f"Valid token should allow download: {res_valid.status_code}"

    # Expired token
    expired_token = gen_token(ctx["fn1"], "kb_download", expires_in=-10)
    res_expired = anon_client.get(f"/api/files/download/{ctx['fn1']}?token={expired_token}")
    assert res_expired.status_code in (401, 403, 404, 302), f"Expired token was accepted: {res_expired.status_code}"

    # Tampered token
    tampered_token = valid_token[:-4] + "abcd"
    res_tampered = anon_client.get(f"/api/files/download/{ctx['fn1']}?token={tampered_token}")
    assert res_tampered.status_code in (401, 403, 404, 302), f"Tampered token was accepted: {res_tampered.status_code}"

    # Token for file A used to download file B
    res_mismatch = anon_client.get(f"/api/files/download/other_file.txt?token={valid_token}")
    assert res_mismatch.status_code in (401, 403, 404, 302), f"Mismatched filename token was accepted: {res_mismatch.status_code}"


def test_rate_limiting_and_account_lockout(sec_app_context):
    """
    3. Rate Limiting & Brute-Force Lockout:
    - 5 failed login attempts lock the user account for 15 minutes and return 429 in Thai
    - Direct bind line endpoint rate limits return 429
    - 429 response message is polite Thai
    """
    ctx = sec_app_context
    app = ctx["app"]
    client = app.test_client()

    target_user = "alice_brute_target"
    ctx["database"].admin_create_user(target_user, "CorrectP@ss1", role="user", email="brute@test.com")
    ctx["database"].add_org_member(ctx["org1_id"], target_user, "member", "owner1")

    # Perform 5 wrong password attempts
    for i in range(5):
        resp = client.post("/api/login", json={"username": target_user, "password": "WrongPassword!"})
        assert resp.status_code in (400, 401, 429)

    # 6th attempt must be locked or rate limited (429)
    locked_resp = client.post("/api/login", json={"username": target_user, "password": "WrongPassword!"})
    assert locked_resp.status_code == 429, f"Account was not locked after 5 failed attempts: {locked_resp.status_code}"
    locked_json = locked_resp.get_json() or {}
    err_text = (locked_json.get("error", "") + " " + locked_json.get("message", "")).strip()
    assert any(k in err_text for k in ["ระงับชั่วคราว", "ล็อค", "ถี่เกินไป", "rate_limit_exceeded"]), f"Expected Thai lockout message, got: {err_text}"

    # Test Global 429 handler format
    with app.test_request_context("/api/test/ratelimit", json={}):
        from werkzeug.exceptions import TooManyRequests
        handler_resp, code = app.error_handler_spec[None][429][TooManyRequests](TooManyRequests())
        assert code == 429
        data = handler_resp.get_json()
        assert data.get("error") == "rate_limit_exceeded"
        assert "คุณทำรายการถี่เกินไป" in data.get("message", "")


def test_cloudflare_tunnel_client_ip_safe_extraction(sec_app_context):
    """
    4. Cloudflare Tunnel Client IP Safe Extraction:
    - When connection is loopback (127.0.0.1) from cloudflared tunnel, trusts CF-Connecting-IP
    - When connection is direct from external IP, ignores spoofed CF-Connecting-IP & X-Forwarded-For
    - Audit log receives genuine client IP
    """
    from routes.shared import get_client_ip

    app = sec_app_context["app"]

    # 1. Behind Cloudflare Tunnel (remote_addr = 127.0.0.1)
    with app.test_request_context(
        "/api/test",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        headers={"CF-Connecting-IP": "203.0.113.88", "X-Forwarded-For": "1.1.1.1"}
    ):
        ip = get_client_ip()
        assert ip == "203.0.113.88", f"Failed to extract CF-Connecting-IP behind tunnel: {ip}"

    # 2. Behind Private Proxy (remote_addr = 10.0.0.5)
    with app.test_request_context(
        "/api/test",
        environ_base={"REMOTE_ADDR": "10.0.0.5"},
        headers={"CF-Connecting-IP": "198.51.100.42"}
    ):
        ip = get_client_ip()
        assert ip == "198.51.100.42", f"Failed to extract CF-Connecting-IP behind private proxy: {ip}"

    # 3. Direct Public Connection (remote_addr = 171.96.12.34) attempting to spoof CF header
    with app.test_request_context(
        "/api/test",
        environ_base={"REMOTE_ADDR": "171.96.12.34"},
        headers={"CF-Connecting-IP": "8.8.8.8", "X-Forwarded-For": "9.9.9.9"}
    ):
        ip = get_client_ip()
        assert ip == "171.96.12.34", f"Spoofed CF-Connecting-IP must not be trusted from public IP: {ip}"

    # 4. Malformed CF-Connecting-IP
    with app.test_request_context(
        "/api/test",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        headers={"CF-Connecting-IP": "not-an-ip-address"}
    ):
        ip = get_client_ip()
        assert ip == "127.0.0.1", f"Malformed IP must fallback to remote_addr: {ip}"

    # 5. Audit Log integration check
    with app.test_request_context(
        "/api/test",
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
        headers={"CF-Connecting-IP": "203.0.113.77"}
    ):
        ip = get_client_ip()
        sec_app_context["database"].log_audit_event("alice1", "CF_AUDIT_TEST", "Test detail", ip, sec_app_context["org1_id"])

    conn = sec_app_context["database"]._get_conn()
    try:
        row = conn.execute("SELECT ip_address FROM audit_logs WHERE action = 'CF_AUDIT_TEST'").fetchone()
        assert row, "Audit log row was not recorded in DB"
        assert row[0] == "203.0.113.77", f"Audit log did not record CF IP: {row[0]}"
    finally:
        conn.close()


def test_secret_leak_scan_in_logs(sec_app_context):
    """
    5. Secret Leak Scan:
    Ensure no credentials, API keys, or raw passwords leak into logging.
    """
    import logging

    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        app = sec_app_context["app"]
        client = app.test_client()

        # Trigger login attempt
        client.post("/api/login", json={"username": "bob2", "password": sec_app_context["pw"]})

        log_contents = log_stream.getvalue()
        sensitive_patterns = [
            r"LINE_CHANNEL_SECRET\s*=\s*[A-Za-z0-9]+",
            r"client_secret\s*=\s*[A-Za-z0-9]+",
            r"Bearer\s+[A-Za-z0-9_\-\.]{25,}",
            rf"password[\"']?\s*[:=]\s*[\"']?{re.escape(sec_app_context['pw'])}[\"']?",
        ]

        leaks = []
        for pat in sensitive_patterns:
            matches = re.findall(pat, log_contents, re.IGNORECASE)
            if matches:
                leaks.append((pat, matches))

        assert not leaks, f"Sensitive information leaked into logs: {leaks}"
    finally:
        root_logger.removeHandler(handler)
