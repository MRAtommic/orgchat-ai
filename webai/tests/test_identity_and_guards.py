# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from app_server import app


@pytest.fixture
def clean_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DB_PATH"] = path
    database.init_db()

    # Seed Admin and an existing user
    database.admin_create_user(
        username="admin_user",
        password="Password123!",
        role="superadmin",
        display_name="Admin Test",
    )
    database.admin_create_user(
        username="somchai",
        password="Password123!",
        role="user",
        display_name="Somchai Jaidee",
    )

    yield path

    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def client(clean_db):
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_user_setting_and_user_exists(clean_db):
    # Category 1: get_user_setting with default=False must return None for nonexistent user
    assert database.get_user_setting("non_existent_user", default=False) is None
    assert database.user_exists("non_existent_user") is False

    # Existing user returns dict and user_exists=True
    somchai_settings = database.get_user_setting("somchai", default=False)
    assert somchai_settings is not None
    assert somchai_settings["username_original"].lower() == "somchai"
    assert database.user_exists("somchai") is True
    assert database.user_exists("SOMCHAI") is True  # Case-insensitive

    # Backward compatibility: default=True returns default dict
    def_settings = database.get_user_setting("non_existent_user", default=True)
    assert def_settings is not None
    assert def_settings["role"] == "user"


def test_impersonate_and_toggle_nonexistent_user(client):
    # Category 1 & 3: Superadmin attempting to impersonate non-existent user must return 404
    with client.session_transaction() as sess:
        sess["user"] = "admin_user"
        sess["role"] = "superadmin"
        sess["org_role"] = "admin"

    csrf_res = client.get("/api/csrf-token")
    csrf_token = csrf_res.get_json().get("csrf_token", "")
    headers = {"X-CSRF-Token": csrf_token}

    resp = client.post("/api/superadmin/impersonate/ghost_user_999", headers=headers)
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["ok"] is False

    # Toggle active on non-existent user must return 404
    resp = client.post("/api/admin/users/ghost_user_999/toggle-active", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False

    # Superadmin toggle active on non-existent user must return 404
    resp = client.post("/api/superadmin/user/ghost_user_999/toggle-active", headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False

    # Superadmin set role on non-existent user must return 404
    resp = client.post("/api/superadmin/user/ghost_user_999/set-role", json={"role": "admin"}, headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False

    # User clearance on non-existent user must return 404
    resp = client.post("/api/admin/user-clearance", json={"username": "ghost_user_999", "clearance_level": "executive"}, headers=headers)
    assert resp.status_code == 404
    assert resp.get_json()["ok"] is False


def test_line_identity_mismatch_and_relink(clean_db):
    # Category 2: Line login vs bot ID linking and unlink lifecycle
    # Link bot ID
    ok = database.link_line_user("somchai", "Ubot12345", is_login=False)
    assert ok is True
    assert database.get_username_by_line_id("Ubot12345") == "somchai"

    # Link login ID
    ok = database.link_line_user("somchai", "Ulogin67890", is_login=True)
    assert ok is True
    assert database.get_username_by_line_id("Ulogin67890") == "somchai"
    # Both bot and login ID resolve to somchai
    assert database.get_username_by_line_id("Ubot12345") == "somchai"

    # Unlink LINE user
    database.unlink_line_user("somchai")
    assert database.get_username_by_line_id("Ubot12345") is None
    assert database.get_username_by_line_id("Ulogin67890") is None


def test_line_login_unlinked_account_refuses_auto_provision(client, clean_db):
    """Category 1 & 2: When an unlinked LINE user logs in via SSO, system MUST NOT
    auto-provision a ghost user without an organization. It must return 403 instructing them
    to log in via their original method first and bind LINE in settings."""
    from unittest.mock import patch, MagicMock

    mock_session = MagicMock()
    # Mock token response
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {"access_token": "mock_tok_abc", "id_token": ""}

    # Mock profile response
    mock_prof_resp = MagicMock()
    mock_prof_resp.status_code = 200
    mock_prof_resp.json.return_value = {"userId": "U_unlinked_new_user_999", "displayName": "New Stranger"}

    mock_session.post.return_value = mock_token_resp
    mock_session.get.return_value = mock_prof_resp

    with patch("routes.auth._get_line_http_session", return_value=mock_session), \
         patch("routes.auth._get_line_login_config", return_value={"channel_id": "mock_cid", "channel_secret": "mock_sec"}):
        resp = client.get("/api/line/login-callback?code=valid_test_code&state=valid_test_state")
        assert resp.status_code == 403
        html = resp.data.decode("utf-8")
        assert "ยังไม่พบบัญชีที่เชื่อมต่อกับ LINE นี้ในระบบค่ะ" in html

        # Verify NO ghost user was created in the database
        assert database.get_username_by_line_id("U_unlinked_new_user_999") is None
        assert database.user_exists("new stranger") is False
        assert database.user_exists("line_user_999") is False

