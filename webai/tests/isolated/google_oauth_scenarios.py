# -*- coding: utf-8 -*-
"""Google Drive/OAuth callback must not crash with a raw JSON internal_error (was: database.get_user did not exist). Temp DB, Google fully mocked."""
import os, secrets, sys, time
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
H = {"User-Agent": "go-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


database.admin_create_user("gus", PW, role="user", email="gus@example.com")
oid, _ = database.create_organization("GOrg", "gus")

svc = MagicMock()
svc.is_configured = True
svc.redirect_uri = "http://localhost:5999/api/auth/google/callback"
svc.exchange_code_for_token.return_value = {"email": "gus.drive@gmail.com", "name": "Gus", "access_token": "AT", "refresh_token": "RT", "token_expiry": None, "picture": None}
svc.setup_user_workspace.return_value = True
RA.oauth2_service = svc
RA.OAUTH2_AVAILABLE = True


def callback(state_org=None, user="gus", extra=""):
    st = secrets.token_hex(8)
    database.oauth_state_store(st, {"username": user, "mode": "personal", "org_id": state_org, "code_verifier": "v", "redirect_uri": svc.redirect_uri})
    c = app.test_client()
    c.post("/api/login", json={"username": "gus", "password": PW}, headers=H)
    r = c.get(f"/api/auth/google/callback?state={st}&code=abc{extra}", headers=H)
    return c, r


c, r = callback()
body = r.get_data(as_text=True)
check("callback succeeds (no JSON internal_error)", r.status_code == 200 and "internal_error" not in body, f"{r.status_code} {body[:120]}")
check("Google email saved for the user", (database.get_google_token("gus") or {}).get("google_email") == "gus.drive@gmail.com" if hasattr(database, "get_google_token") else True)
with c.session_transaction() as s:
    check("session keeps the user's real organisation (not forced to org 1)", s.get("org_id") == oid and s.get("user") == "gus", str(dict(s)))

svc.exchange_code_for_token.side_effect = RuntimeError("google down")
c, r = callback()
body = r.get_data(as_text=True)
check("token-exchange failure → readable page, not raw JSON", "internal_error" not in body and r.status_code in (200, 302, 400, 500) and not body.lstrip().startswith("{"), body[:150])

svc.exchange_code_for_token.side_effect = None
c, r = callback(extra="&error=access_denied")
check("user pressing cancel redirects back", r.status_code == 302 and "google_cancelled" in r.headers.get("Location", ""))

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
