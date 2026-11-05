# -*- coding: utf-8 -*-
"""Route smoke test: log in as an organization admin and call every argument-free GET route.
Fails if any route answers 5xx or raises. Runs in its own process with a temporary DB (DB_PATH required).
Exit code 0 = no crashes. Prints every route that returned >= 500 with the first lines of the traceback."""
import os
import re
import secrets
import sys
import traceback

assert os.environ.get("DB_PATH"), "DB_PATH must point to a temporary database"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())

import app_server  # noqa: E402
import database  # noqa: E402
import routes.auth as RA  # noqa: E402

RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = False          # let Flask's error handlers run so we see real 500s
app.config["PROPAGATE_EXCEPTIONS"] = False
H = {"User-Agent": "smoke-ua"}
PW = "Passw0rd!x"

database.admin_create_user("smokeadmin", PW, role="user", email="smoke@example.com")
oid, _ = database.create_organization("Smoke Org", "smokeadmin")
c = app.test_client()
j = c.post("/api/login", json={"username": "smokeadmin", "password": PW}, headers=H).get_json()
assert j.get("ok"), j

SKIP = re.compile(r"^/(static|socket\.io|logout|api/logout|api/qr|line/webhook|stripe|api/line/login|api/auth/google|api/line/exchange|game|sw\.js|api/admin/db|api/admin/system/cleanup|api/export)")
bad, ok, redirects, auth = [], 0, 0, 0
rules = sorted({r.rule for r in app.url_map.iter_rules() if "GET" in r.methods and "<" not in r.rule and not SKIP.search(r.rule)})
for rule in rules:
    try:
        r = c.get(rule, headers=H)
    except Exception as e:  # an exception escaped the app
        bad.append((rule, "EXC", "".join(traceback.format_exception_only(type(e), e)).strip()))
        continue
    if r.status_code >= 500:
        bad.append((rule, r.status_code, r.get_data(as_text=True)[:160].replace("\n", " ")))
    elif r.status_code in (301, 302, 303, 307, 308):
        redirects += 1
    elif r.status_code in (401, 403):
        auth += 1
    else:
        ok += 1

print(f"routes checked: {len(rules)} | ok(2xx/4xx): {ok} | redirects: {redirects} | 401/403: {auth} | 5xx/exceptions: {len(bad)}")
for rule, st, msg in bad:
    print(f"BAD {st} {rule} :: {msg}")
print("RESULT:", "NO CRASHES" if not bad else "CRASHES FOUND")
sys.exit(1 if bad else 0)
