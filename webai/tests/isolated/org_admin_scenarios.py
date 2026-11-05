# -*- coding: utf-8 -*-
"""Scenario script for 2FA + organization admin features.
Runs in its OWN process with a throw-away database (DB_PATH set by the caller), so it never touches
webai/chat_history.db. Exit code 0 = all scenarios passed. Run via tests/test_org_admin_isolated.py.
"""
import os
import secrets
import sys

assert os.environ.get("DB_PATH"), "DB_PATH must point to a temporary database"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())

import pyotp  # noqa: E402

import app_server  # noqa: E402
import database  # noqa: E402
import db.org_security as OS  # noqa: E402
import routes.auth as RA  # noqa: E402

RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "scenario-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def mkorg(owner, org_name):
    database.admin_create_user(owner, PW, role="user", email=owner + "@example.com")
    oid, _ = database.create_organization(org_name, owner)
    c = database._get_conn()
    c.execute("UPDATE organizations SET plan='business', max_users=50 WHERE id=?", (oid,))
    c.commit()
    c.close()
    return oid


TOT = {}


def login(u):
    c = app.test_client()
    j = c.post("/api/login", json={"username": u, "password": PW}, headers=H).get_json()
    if j.get("require_2fa") and u in TOT:
        j = c.post("/api/2fa/verify", json={"pre_auth_token": j["pre_auth_token"], "code": TOT[u].now()}, headers=H).get_json()
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, csrf, j


def call(c, csrf, method, url, body=None):
    h = dict(H, **{"X-CSRF-Token": csrf})
    r = getattr(c, method)(url, json=body, headers=h) if body is not None else getattr(c, method)(url, headers=h)
    try:
        return r.status_code, r.get_json()
    except Exception:
        return r.status_code, None


def enable_2fa(u):
    c, csrf, _ = login(u)
    s = call(c, csrf, "post", "/api/2fa/setup", {})[1]
    t = pyotp.TOTP(s["secret"])
    code = t.now()
    st, j = call(c, csrf, "post", "/api/2fa/enable", {"code": code, "type": "authenticator"})
    TOT[u] = t
    return code, j


A = mkorg("ownerA", "Org A")
B = mkorg("ownerB", "Org B")
for u in ("alice", "shared"):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
database.add_org_member(A, "alice", "member", "ownerA")
database.add_org_member(A, "shared", "member", "ownerA")
database.add_org_member(B, "shared", "member", "ownerB")

# ---- 2FA basics ----
code, en = enable_2fa("ownerA")
check("2FA enable returns 8 backup codes", len(en.get("backup_codes", [])) == 8)
check("backup codes are >= 12 chars", all(len(c) >= 12 for c in en.get("backup_codes", [])))
c2 = app.test_client()
j = c2.post("/api/login", json={"username": "ownerA", "password": PW}, headers=H).get_json()
check("login of 2FA user returns require_2fa + totp_type", j.get("require_2fa") and j.get("totp_type") == "authenticator")
r = c2.post("/api/2fa/verify", json={"pre_auth_token": j["pre_auth_token"], "code": "000000"}, headers=H)
check("wrong 2FA code rejected", r.status_code == 400)
good = TOT["ownerA"].now()
r1 = c2.post("/api/2fa/verify", json={"pre_auth_token": j["pre_auth_token"], "code": good}, headers=H)
check("right 2FA code accepted", r1.status_code == 200)
c3 = app.test_client()
j3 = c3.post("/api/login", json={"username": "ownerA", "password": PW}, headers=H).get_json()
r2 = c3.post("/api/2fa/verify", json={"pre_auth_token": j3["pre_auth_token"], "code": good}, headers=H)
check("same TOTP code cannot be replayed", r2.status_code == 400, str(r2.status_code))
c4 = app.test_client()
j4 = c4.post("/api/login", json={"username": "ownerA", "password": PW}, headers=H).get_json()
codes = [c4.post("/api/2fa/verify", json={"pre_auth_token": j4["pre_auth_token"], "code": f"{i:06d}"}, headers=H).status_code for i in range(7)]
check("token locks after 5 wrong codes (6th attempt refused)", codes[:5] == [400] * 5 and codes[5] == 429, str(codes))
check("a locked token stays unusable even with the right code",
      c4.post("/api/2fa/verify", json={"pre_auth_token": j4["pre_auth_token"], "code": TOT["ownerA"].now()}, headers=H).status_code in (400, 429))


# ---- 2FA secret encryption at rest ----
import secret_vault  # noqa: E402
conn_v = database._get_conn()
stored = conn_v.execute("SELECT totp_secret FROM user_settings WHERE username='ownerA'").fetchone()[0]
conn_v.close()
check("TOTP secret is stored encrypted (enc:v1:...)", isinstance(stored, str) and stored.startswith("enc:v1:") and "=" not in stored[:6])
check("encrypted secret decrypts to a valid base32 seed", len(secret_vault.decrypt(stored)) >= 16 and secret_vault.decrypt(stored) == TOT["ownerA"].secret)
# legacy plaintext account still logs in and is upgraded afterwards
database.admin_create_user("legacy2fa", PW, role="user", email="legacy@example.com")
seed = pyotp.random_base32()
conn_v = database._get_conn()
conn_v.execute("UPDATE user_settings SET totp_enabled=1, totp_secret=?, totp_type='authenticator' WHERE username='legacy2fa'", (seed,))
conn_v.commit(); conn_v.close()
cl = app.test_client()
jl = cl.post("/api/login", json={"username": "legacy2fa", "password": PW}, headers=H).get_json()
rl = cl.post("/api/2fa/verify", json={"pre_auth_token": jl["pre_auth_token"], "code": pyotp.TOTP(seed).now()}, headers=H)
check("legacy plaintext 2FA account can still log in", rl.status_code == 200)
conn_v = database._get_conn()
after = conn_v.execute("SELECT totp_secret FROM user_settings WHERE username='legacy2fa'").fetchone()[0]
conn_v.close()
check("legacy secret is upgraded to encrypted after first successful login", after.startswith("enc:v1:") and secret_vault.decrypt(after) == seed)
check("garbage ciphertext decrypts to empty (no crash)", secret_vault.decrypt("enc:v1:not-a-token") == "")

rw = app.test_client().post("/api/login", json={"username": "alice", "password": "definitely-wrong"}, headers=H)
check("wrong password returns HTTP 401 with a message", rw.status_code == 401 and rw.get_json().get("ok") is False and rw.get_json().get("error"))

# ---- org security policy ----
import time as _t
_t.sleep(31)  # next TOTP window (the last code was already used above)
oa, oa_csrf, oj = login("ownerA")
check("owner can log in with a fresh 2FA code", oj.get("ok") is True, str(oj))
st, _ = call(oa, oa_csrf, "post", "/api/org/security/policy",
             {"require_2fa": "all", "session_timeout_min": 30, "min_password_length": 12, "allowed_login_methods": ["password", "line"]})
check("owner can save policy", st == 200)
st, _ = call(oa, oa_csrf, "post", "/api/org/security/policy",
             {"require_2fa": "all", "session_timeout_min": 5, "min_password_length": 12, "allowed_login_methods": ["password"]})
check("invalid policy (timeout 5) rejected", st == 400)
al, al_csrf, _ = login("alice")
st, _ = call(al, al_csrf, "get", "/api/org/security/policy")
check("non-admin cannot read policy", st == 403)
st, j = call(al, al_csrf, "get", "/api/org/quota")
check("member without 2FA is blocked by 'require all'", st == 403 and (j or {}).get("error") == "2fa_setup_required")
st, _ = call(al, al_csrf, "post", "/api/2fa/setup", {})
check("blocked member can still reach 2FA setup", st == 200)
check("google login blocked for member when org disallows it", OS.login_method_allowed("alice", "google")[0] is False)
check("owner is never blocked from a login method", OS.login_method_allowed("ownerA", "google")[0] is True)
OS.invalidate()
ok, msg = OS.check_password_policy("alice", "Abcdefg1!x")
check("org min password length enforced (10 < 12)", ok is False)

# ---- conflicting policies must not lock a multi-org user out of everything ----
OS.set_policy(A, {"require_2fa": "off", "session_timeout_min": 120, "min_password_length": 8, "allowed_login_methods": ["password"]}, "ownerA")
OS.set_policy(B, {"require_2fa": "off", "session_timeout_min": 120, "min_password_length": 8, "allowed_login_methods": ["google"]}, "ownerB")
check("conflicting org policies still leave at least one method",
      OS.login_method_allowed("shared", "password")[0] or OS.login_method_allowed("shared", "google")[0])

# ---- member lifecycle ----
oa, oa_csrf, _ = login("ownerA") if False else (oa, oa_csrf, None)
st, j = call(oa, oa_csrf, "post", "/api/org/members/import",
             {"csv": "username,email,display_name,department,role\ncarol,carol@example.com,Carol,HR,member\nbad name,x,Bad,IT,member\ncarol,dup@example.com,Dup,IT,member"})
check("import creates 1, skips 2", st == 200 and j["created"] == 1 and j["skipped"] == 2, str(j and (j['created'], j['skipped'])))
check("import returns a 12+ char temp password", len(j["report"][0]["temp_password"]) >= 12)
st, j = call(oa, oa_csrf, "post", "/api/org/invite-token", {"role": "member"})
st, j = call(oa, oa_csrf, "get", "/api/org/invites")
check("pending invites listed", st == 200 and len(j["invites"]) >= 1)
tok = j["invites"][0]["token"]
check("invite can be revoked once", call(oa, oa_csrf, "delete", "/api/org/invites/" + tok)[0] == 200 and call(oa, oa_csrf, "delete", "/api/org/invites/" + tok)[0] == 404)

# offboarding a single-org member suspends the account; a shared account is NOT suspended globally
st, j = call(oa, oa_csrf, "post", "/api/org/members/carol/offboard", {"remove_from_org": True})
check("offboard single-org member suspends account", st == 200 and database.get_user_setting("carol").get("is_active") == 0)
st, j = call(oa, oa_csrf, "post", "/api/org/members/shared/offboard", {})
check("offboard shared member removes from this org only",
      st == 200 and not database.is_org_member(A, "shared") and database.is_org_member(B, "shared"))
check("shared account stays active (other organization unaffected)", database.get_user_setting("shared").get("is_active") in (1, True))
OS.set_policy(B, {"require_2fa": "off", "session_timeout_min": 120, "min_password_length": 8, "allowed_login_methods": ["password", "google"]}, "ownerB")  # Org B (google-only above) now allows password too
check("shared account can still log in to its remaining organization", login("shared")[2].get("ok") is True)
check("cannot offboard yourself", call(oa, oa_csrf, "post", "/api/org/members/ownerA/offboard", {})[0] == 400)

# ---- overview / audit ----
st, j = call(oa, oa_csrf, "get", "/api/org/overview")
check("overview reports 2FA adoption", st == 200 and "percent" in j["two_fa"])
st, j = call(oa, oa_csrf, "get", "/api/org/audit?action=ORG_&limit=5")
check("audit log filter works", st == 200 and j["total"] >= 1)
r = oa.get("/api/org/audit/export", headers=H)
check("audit export is CSV", r.status_code == 200 and "text/csv" in r.mimetype)

print("\nRESULT:", "ALL PASSED" if not FAILS else "FAILED: " + "; ".join(FAILS))
sys.exit(1 if FAILS else 0)
