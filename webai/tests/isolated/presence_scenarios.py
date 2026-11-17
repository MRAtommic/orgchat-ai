# -*- coding: utf-8 -*-
"""Presence: heartbeat TTL, startup reset, tenant isolation of /api/users/status, socket ping. Own process + temp DB."""
import os, secrets, sys
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "pr-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


for u in ("ownerA", "a1", "ownerB", "b1", "solo"):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
oa, _ = database.create_organization("OrgA", "ownerA")
ob, _ = database.create_organization("OrgB", "ownerB")
database.add_org_member(oa, "a1", "member", "ownerA")
database.add_org_member(ob, "b1", "member", "ownerB")


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    return c


def status(c):
    r = c.get("/api/users/status", headers=H)
    return r.status_code, {x["username"]: x for x in (r.get_json() or {}).get("users", [])}


# 1) heartbeat => online; stale => offline
database.set_user_online("a1", "General")
database.set_user_online("b1", "General")
ca = login("ownerA")
code, st = status(ca)
check("endpoint ok", code == 200)
check("peer a1 online", st.get("a1", {}).get("is_online") is True, str(st))
check("other-org b1 NOT visible", "b1" not in st and "ownerB" not in st, str(list(st)))
check("last_activity is UTC ISO (Z)", str(st["a1"]["last_activity"]).endswith("Z"), str(st.get("a1")))

conn = database._get_conn()
conn.execute("UPDATE user_status SET last_activity = datetime('now','-5 minutes') WHERE username='a1'")
conn.commit(); conn.close()
code, st = status(ca)
check("stale heartbeat (5 min) => offline though is_online=1", st["a1"]["is_online"] is False, str(st["a1"]))
check("get_online_users excludes stale", "a1" not in {u["username"] for u in database.get_online_users()})

database.touch_user("a1")
code, st = status(ca)
check("touch_user revives online", st["a1"]["is_online"] is True)

# 2) startup reset
database.reset_all_offline()
check("reset_all_offline clears everyone", database.get_online_users() == [])

# 3) touch creates a row for a user who never connected
database.touch_user("solo")
check("touch creates row", any(u["username"] == "solo" for u in database.get_online_users()))

# 4) socket heartbeat from a logged-in client marks online and broadcasts to peers only
import app_server as AS  # noqa: E402
sio = AS.socketio
flask_c = login("a1")
sc = sio.test_client(app, flask_test_client=flask_c)
sc.emit("presence_ping", {"room": "General"})
check("presence_ping marks online", "a1" in {u["username"] for u in database.get_online_users()})
peer = sio.test_client(app, flask_test_client=login("ownerA"))
peer.emit("user_online", {"room": "General"})
other = sio.test_client(app, flask_test_client=login("b1"))
other.emit("user_online", {"room": "General"})
peer.get_received(); other.get_received()
sc.emit("user_offline")
got_peer = [m for m in peer.get_received() if m["name"] == "user_status_updated"]
got_other = [m for m in other.get_received() if m["name"] == "user_status_updated"]
check("same-org peer told a1 went offline", any(m["args"][0].get("username") == "a1" for m in got_peer), str(got_peer))
check("other org gets nothing", not got_other, str(got_other))
check("payload has no global user list", all("online_users" not in m["args"][0] for m in got_peer))

# 5) disconnect => offline
sc2 = sio.test_client(app, flask_test_client=login("a1"))
sc2.emit("user_online", {"room": "General"})
check("online after user_online", "a1" in {u["username"] for u in database.get_online_users()})
sc2.disconnect()
check("offline after disconnect", "a1" not in {u["username"] for u in database.get_online_users()})

# 6) unauthenticated
r = app.test_client().get("/api/users/status", headers=H)
check("anonymous blocked", r.status_code in (401, 302, 403), str(r.status_code))

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
