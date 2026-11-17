# -*- coding: utf-8 -*-
"""Org-level 'disconnect Google' must work for superadmin / global admin / org admin and refuse plain members. Temp DB, Google mocked."""
import os, secrets, sys
from unittest.mock import MagicMock
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "gd-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


database.admin_create_user("sup", PW, role="superadmin", email="sup@example.com")
database.admin_create_user("gadm", PW, role="admin", email="gadm@example.com")
database.admin_create_user("orgadm", PW, role="user", email="orgadm@example.com")
database.admin_create_user("mem", PW, role="user", email="mem@example.com")
oid, _ = database.create_organization("GD Org", "orgadm")
for u in ("sup", "gadm", "mem"):
    database.add_org_member(oid, u, "member", "orgadm")
database.add_org_member(oid, "sup", "admin", "orgadm") if False else None

svc = MagicMock()
RA.oauth2_service = svc
RA.OAUTH2_AVAILABLE = True


def try_disconnect(u):
    svc.reset_mock()
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    r = c.post("/api/auth/google/disconnect?scope=org", headers=dict(H, **{"X-CSRF-Token": csrf}))
    return r, svc.disconnect_org.called


r, called = try_disconnect("sup")
check("superadmin can disconnect the org Google account", r.status_code == 200 and called, f"{r.status_code} {r.get_data(as_text=True)[:100]}")
r, called = try_disconnect("gadm")
check("global admin can disconnect", r.status_code == 200 and called, f"{r.status_code}")
r, called = try_disconnect("orgadm")
check("organisation owner/admin can disconnect", r.status_code == 200 and called, f"{r.status_code} {r.get_data(as_text=True)[:100]}")
r, called = try_disconnect("mem")
check("plain member is refused (and nothing is disconnected)", r.status_code == 403 and not called, f"{r.status_code}")
print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
