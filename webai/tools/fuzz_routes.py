# -*- coding: utf-8 -*-
"""Throws odd inputs at every route (isolated temp DB/DATA_DIR, outbound network blocked) and reports unhandled
exceptions / HTTP 500s, de-duplicated by exception type + code location.

    DB_PATH=<tmp>/x.db DATA_DIR=<tmp>/d VECTOR_BACKEND=python python tools/fuzz_routes.py [max_routes]

Destructive endpoints (wipe/backup/clear-all/logout...) are skipped by name; nothing external is contacted.
"""
import os
import re
import secrets
import socket
import sys
import time
import traceback

assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR"), "set DB_PATH and DATA_DIR to temp locations first"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["ORGCHAT_FUZZ_MODE"] = "1"
os.environ["SQLITE_BUSY_TIMEOUT"] = "2000"
os.environ["DISABLE_BACKGROUND_TASKS"] = "1"
for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON", "STRIPE_SECRET_KEY", "LINE_CHANNEL_ACCESS_TOKEN"):
    os.environ.pop(k, None)
sys.path.insert(0, os.getcwd())

# block every outbound connection (keeps the run fast and safe)
_real_cc = socket.create_connection


def _blocked(*a, **k):
    raise ConnectionError("outbound network blocked by fuzz_routes")


def _only_local(address, *a, **k):
    if address and address[0] in ("127.0.0.1", "localhost", "::1"):
        return _real_cc(address, *a, **k)
    return _blocked()


socket.create_connection = _only_local

import app_server  # noqa: E402
import database  # noqa: E402
import routes.auth as RA  # noqa: E402

RA._limiter.enabled = False
for lim in getattr(app_server.app, "extensions", {}).get("limiter", []) or []:
    try:
        lim.enabled = False
    except Exception:
        pass
app = app_server.app
app.config["TESTING"] = False
app.config["PROPAGATE_EXCEPTIONS"] = True

SKIP = re.compile(r"wipe|prune|/sync|backup|optimi[sz]e|clear_all|/clear\b|/clear$|logout|shutdown|restart|set_key|drop|truncate|purge|socket\.io|static|"
                  r"delete-account|offboard|/api/admin/db|debug/routes|reset-all|factory|stripe/webhook|/line/webhook|/stream|download|"
                  r"/api/chat|/ai|ai[-_/]|summar|generat|/tts|analy|ocr|scan|translate|/ask|insight|brief|digest|reply|assistant|harvest|wiki/ai", re.I)
H = {"User-Agent": "fuzz-ua"}
PW = "Passw0rd!x"

database.admin_create_user("fz_super", PW, role="user", email="fz@example.com")
c0 = database._get_conn()
c0.execute("UPDATE user_settings SET role='superadmin' WHERE username='fz_super'")
c0.commit()
c0.close()
oid, _ = database.create_organization("Fuzz Org", "fz_super")
database.admin_create_user("fz_member", PW, role="user", email="fm@example.com")
database.add_org_member(oid, "fz_member", "member", "fz_super")


def login(u):
    cl = app.test_client()
    cl.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = cl.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return cl, csrf


PAYLOADS = [
    {},
    {"id": None, "name": None, "text": None, "message": None, "username": None},
    {"id": "o'brien \"q\" %00 กข", "name": "<b>x</b> &amp;", "text": "x" * 5000, "limit": -5, "page": "abc", "amount": "NaN"},
    {"id": 10 ** 30, "amount": -1e308, "date": "9999-99-99", "email": "not-an-email", "items": "not-a-list", "start_date": "x", "end_date": None},
    {"items": [None, 1, "x", {}], "ids": "1,2,3", "data": [[]], "lat": "abc", "lng": None},
]
QUERIES = ["", "?limit=abc", "?limit=-1&page=0", "?id=%00&q=" + "A" * 2000, "?days=99999999999&year=abc&month=13"]

start = time.time()
max_routes = int(sys.argv[1]) if len(sys.argv) > 1 else 10 ** 9
max_seconds = int(os.environ.get("FUZZ_MAX_SECONDS", "240"))
found = {}
count = 0
clients = {"superadmin": login("fz_super"), "member": login("fz_member")}
rules = [r for r in sorted(app.url_map.iter_rules(), key=lambda r: r.rule) if not SKIP.search(r.rule)]
total_to_fuzz = min(len(rules), max_routes)
print(f"🚀 Fuzzing starting: {total_to_fuzz} non-destructive routes selected (max time: {max_seconds}s)...", flush=True)

try:
    for rule in rules:
        if count >= max_routes or time.time() - start > max_seconds:
            break
        methods = [m for m in rule.methods if m in ("GET", "POST", "PUT", "PATCH", "DELETE")]
        path = re.sub(r"<(?:int:)?[^>]+>", "1", rule.rule)
        path = re.sub(r"<path:[^>]+>", "x/y", path)
        count += 1
        if count % 10 == 0 or count == total_to_fuzz:
            elapsed = time.time() - start
            print(f"  [progress] fuzzed {count}/{total_to_fuzz} routes in {elapsed:.1f}s ({len(found)} issues found)...", flush=True)

        for who, (cl, csrf) in clients.items():
            for m in methods:
                variants = [(None, q) for q in QUERIES] if m == "GET" else [(p, "") for p in PAYLOADS]
                for body, q in variants:
                    hdr = dict(H, **{"X-CSRF-Token": csrf})
                    try:
                        if m == "GET":
                            r = cl.get(path + q, headers=hdr)
                        else:
                            r = getattr(cl, m.lower())(path, json=body, headers=hdr)
                        if r.status_code >= 500:
                            found.setdefault(("HTTP %d" % r.status_code, rule.rule, m), who)
                    except Exception as e:  # unhandled exception inside a route
                        tb = traceback.extract_tb(e.__traceback__)
                        here = next((f for f in reversed(tb) if "webai" in f.filename.replace("\\", "/") and "/site-packages/" not in f.filename.replace("\\", "/")), tb[-1])
                        key = (type(e).__name__ + ": " + str(e)[:80], f"{os.path.basename(here.filename)}:{here.lineno}", m)
                        found.setdefault(key, f"{who} {rule.rule}")
except KeyboardInterrupt:
    print("\n⚠️ Fuzzing interrupted by user. Generating partial report...", flush=True)

elapsed_total = time.time() - start
print(f"\n✅ Fuzzing finished: tested {count} routes in {elapsed_total:.1f}s -> {len(found)} distinct crash sites", flush=True)
for (what, where, m), ctx in sorted(found.items(), key=lambda x: str(x)):
    print(f"CRASH {what}  @ {where}  [{m}] ({ctx})")

report_path = os.environ.get("FUZZ_REPORT_PATH", os.path.join(os.environ["DATA_DIR"], "fuzz_report.json"))
try:
    import json
    report_data = {
        "fuzzed_count": count,
        "elapsed_seconds": round(elapsed_total, 2),
        "crash_count": len(found),
        "crashes": [{"error": what, "location": where, "method": m, "context": ctx} for (what, where, m), ctx in sorted(found.items())]
    }
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump(report_data, rf, indent=2, ensure_ascii=False)
    print(f"📝 Report saved to: {report_path}", flush=True)
except Exception as _re:
    print(f"⚠️ Could not write report file: {_re}", flush=True)
