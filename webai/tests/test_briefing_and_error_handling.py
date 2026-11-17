# -*- coding: utf-8 -*-
"""
Regression test for Morning Briefing and Global Error Handler.
Verifies:
1. POST /api/admin/briefing/trigger succeeds without AttributeError
2. 500 errors return clear Thai message in 'error' instead of opaque 'internal_error'
"""
import os
import secrets
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

WEBAI = Path(__file__).resolve().parent.parent


@pytest.fixture
def briefing_env():
    tmpdir = tempfile.TemporaryDirectory()
    tmp_path = Path(tmpdir.name)
    db_file = tmp_path / "briefing.db"
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    old_env = os.environ.copy()
    os.environ["DB_PATH"] = str(db_file)
    os.environ["DATA_DIR"] = str(data_dir)
    os.environ["VECTOR_BACKEND"] = "python"
    os.environ["FLASK_SECRET_KEY"] = secrets.token_hex(16)
    os.environ["BASE_URL"] = "http://localhost:5999"

    import app_server
    import database

    database.init_db()

    app = app_server.app
    app.config["TESTING"] = True

    pw = "P@ssword123!"
    uname = f"brief_admin_{secrets.token_hex(3)}"
    database.admin_create_user(uname, pw, role="admin", email=f"{uname}@brief.com")
    org_id, _ = database.create_organization(f"Briefing Corp {secrets.token_hex(4)}", uname)
    database.link_line_user(uname, "U_BRIEF_ADMIN")

    ctx = {
        "app": app,
        "database": database,
        "org_id": org_id,
        "username": uname,
        "pw": pw,
    }

    yield ctx

    import gc
    gc.collect()
    os.environ.clear()
    os.environ.update(old_env)
    try:
        tmpdir.cleanup()
    except Exception:
        pass


def test_briefing_trigger_route_success(briefing_env):
    ctx = briefing_env
    app = ctx["app"]
    client = app.test_client()

    res_login = client.post("/api/login", json={"username": ctx["username"], "password": ctx["pw"]})
    assert res_login.status_code == 200
    csrf = client.get("/api/csrf-token").get_json()["csrf_token"]

    with patch("routes.chat.send_line_push_notification", return_value=True) as mock_push:
        res = client.post("/api/admin/briefing/trigger", headers={"X-CSRF-Token": csrf})
        assert res.status_code == 200, f"Trigger briefing failed: {res.get_json()}"
        data = res.get_json()
        assert data.get("ok") is True
        assert "Morning Briefing" in data.get("message", "")
        mock_push.assert_called_once()


def test_global_500_error_thai_message(briefing_env):
    ctx = briefing_env
    app = ctx["app"]
    client = app.test_client()

    res_login = client.post("/api/login", json={"username": ctx["username"], "password": ctx["pw"]})
    assert res_login.status_code == 200
    csrf = client.get("/api/csrf-token").get_json()["csrf_token"]

    with patch("routes.admin.database.get_executive_summary_data", side_effect=RuntimeError("Simulated DB failure")):
        res = client.post("/api/admin/briefing/trigger", headers={"X-CSRF-Token": csrf, "X-Requested-With": "XMLHttpRequest"})
        assert res.status_code == 500
        data = res.get_json()
        assert data["ok"] is False
        assert "เกิดข้อผิดพลาด" in data["error"], f"Error must contain polite Thai message, got: {data['error']}"
