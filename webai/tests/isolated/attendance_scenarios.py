# -*- coding: utf-8 -*-
"""Per-organisation attendance settings: unconfigured org is never 'outside', configured org uses its own radius,
settings are validated, tenants are isolated. Own process + temp DB/DATA_DIR."""
import os, secrets, sys
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["OFFICE_LATITUDE"] = "13.7563"      # legacy global default (Bangkok) must no longer decide anything
os.environ["OFFICE_LONGITUDE"] = "100.5018"
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "att-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


def mk(u, org=None):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
    if org:
        database.add_org_member(org, u, "member", "ownerA")


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, csrf


def call(cl, method, url, body=None):
    c, csrf = cl
    h = dict(H, **{"X-CSRF-Token": csrf})
    r = getattr(c, method)(url, json=body, headers=h) if body is not None else getattr(c, method)(url, headers=h)
    return r.status_code, (r.get_json() or {})


database.admin_create_user("ownerA", PW, role="user", email="a@example.com")
A, _ = database.create_organization("A Co", "ownerA")
database.admin_create_user("ownerB", PW, role="user", email="b@example.com")
B, _ = database.create_organization("B Co", "ownerB")
for u in ("w1", "w2"):
    mk(u, A)
mk("wb", B)
oa, w1, w2, wb = login("ownerA"), login("w1"), login("w2"), login("wb")

# 1) org with NO office configured: far-away coordinates are never 'outside'
st, j = call(w1, "post", "/api/attendance/clock", {"latitude": 18.79, "longitude": 98.98})   # Chiang Mai, ~580 km from the old default
check("unconfigured org: clock-in works", st == 200 and j.get("ok"), str(j))
check("unconfigured org: NOT flagged outside", j.get("is_outside") is False and j.get("status") != "outside_geofence", str(j.get("status")))
st, j = call(w2, "get", "/api/attendance/today")
check("today reports office.configured=false", st == 200 and j["office"]["configured"] is False, str(j.get("office")))

# 2) validation
st, j = call(oa, "post", "/api/org/attendance/settings", {"office_lat": "abc", "office_lng": 100, "radius_m": 200, "work_start": "09:00"})
check("bad latitude rejected", st == 400)
st, j = call(oa, "post", "/api/org/attendance/settings", {"office_lat": 13.8, "office_lng": 100.5, "radius_m": 5, "work_start": "09:00"})
check("radius below 20 m rejected", st == 400)
st, j = call(oa, "post", "/api/org/attendance/settings", {"office_lat": 13.8, "office_lng": 100.5, "radius_m": 200, "work_start": "25:99"})
check("bad time rejected", st == 400)
st, j = call(w1, "post", "/api/org/attendance/settings", {"office_lat": 13.8, "office_lng": 100.5, "radius_m": 200, "work_start": "09:00"})
check("plain member cannot change settings (403)", st == 403)

# 3) configured org
st, j = call(oa, "post", "/api/org/attendance/settings", {"office_lat": 13.8196, "office_lng": 100.5143, "radius_m": 150, "work_start": "08:30"})
check("admin saves settings", st == 200 and j["settings"]["configured"] and j["settings"]["radius_m"] == 150, str(j))
st, j = call(w2, "post", "/api/attendance/clock", {"latitude": 13.8197, "longitude": 100.5144})
check("configured org: inside radius -> not outside", st == 200 and j.get("is_outside") is False and (j.get("distance_meters") or 0) < 150, str(j))
sql = database._get_conn(); sql.execute("DELETE FROM attendance WHERE username='w2'") if False else None; sql.close()
# w2 is now checked in; use another user for the 'outside' case
mk("w3", A); w3 = login("w3")
st, j = call(w3, "post", "/api/attendance/clock", {"latitude": 13.8300, "longitude": 100.5143})   # ~1.1 km north
check("configured org: far away -> outside_geofence", st == 200 and j.get("is_outside") is True and j.get("status") == "outside_geofence", str(j))
st, j = call(w3, "get", "/api/attendance/today")
check("today now shows configured office + start time", j["office"]["configured"] and j["office"]["work_start_time"] == "08:30" and j["office"]["radius_meters"] == 150, str(j.get("office")))

# 4) isolation: other org unaffected
st, j = call(wb, "post", "/api/attendance/clock", {"latitude": 13.8300, "longitude": 100.5143})
check("other org still unconfigured -> not outside", j.get("is_outside") is False and j.get("status") != "outside_geofence", str(j))
st, j = call(wb, "get", "/api/org/attendance/settings")
check("other org's member cannot read admin settings (403)", st == 403)
st, j = call(oa, "get", "/api/org/attendance/settings")
check("admin can read own settings", st == 200 and j["settings"]["office_lat"] == 13.8196)


# 5) GPS must not be blocked by the server, and unconfigured orgs do not need GPS at all
r = app.test_client().get("/", headers=H)
pp = r.headers.get("Permissions-Policy", "")
check("Permissions-Policy allows geolocation for the site itself", "geolocation=(self)" in pp and "geolocation=()" not in pp, pp)
mk("w4", B); w4 = login("w4")
st, j = call(w4, "post", "/api/attendance/clock", {})
check("unconfigured org: clock-in WITHOUT any coordinates works", st == 200 and j.get("ok"), str(j))
mk("w5", A); w5 = login("w5")
st, j = call(w5, "post", "/api/attendance/clock", {})
check("configured org: coordinates are still required (400)", st == 400, str(st))


# 6) monthly overview for the admin (totals / per person / per day) and tenant isolation
for u, d, ti, to, st in (("w1", "2026-10-01", "08:20:00", "17:20:00", "on_time"), ("w1", "2026-10-02", "09:40:00", "17:40:00", "late"),
                          ("w2", "2026-10-01", "08:50:00", "16:50:00", "on_time"), ("w3", "2026-10-02", "10:00:00", None, "outside_geofence"),
                          ("w1", "2026-09-30", "08:00:00", "17:00:00", "on_time")):
    database.record_attendance(u, A, "check_in", status=st, custom_date=d, custom_time=ti)
    if to:
        database.record_attendance(u, A, "check_out", status="on_time", custom_date=d, custom_time=to)
database.record_attendance("wb", B, "check_in", status="late", custom_date="2026-10-01", custom_time="11:00:00")
st, j = call(oa, "get", "/api/org/attendance/summary?month=2026-10")
t = j.get("totals", {})
check("summary: totals correct (4 check-ins, 2 on time, 1 late, 1 outside, 25 h)", st == 200 and t.get("checkins") == 4 and t.get("on_time") == 2 and t.get("late") == 1 and t.get("outside") == 1 and t.get("hours") == 25.0, str(t))
check("summary: other month's record excluded", all(d["date"].startswith("2026-10") for d in j.get("days", [])))
check("summary: other organisation's record excluded", "wb" not in [e["username"] for e in j.get("employees", [])])
w1row = next((e for e in j.get("employees", []) if e["username"] == "w1"), {})
check("summary: per-person numbers (w1: 2 days, 1 late, 17 h)", w1row.get("days") == 2 and w1row.get("late") == 1 and w1row.get("hours") == 17.0, str(w1row))
d1 = next((d for d in j.get("days", []) if d["date"] == "2026-10-01"), {})
check("summary: per-day numbers (2026-10-01: 2 present)", d1.get("present") == 2, str(d1))
st, _ = call(oa, "get", "/api/org/attendance/summary?month=2026-13")
check("summary: bad month rejected (400)", st == 400)
st, _ = call(w1, "get", "/api/org/attendance/summary?month=2026-10")
check("summary: plain member cannot read it (403)", st == 403)

print("")
print("ALL PASSED" if not FAILS else f"FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
