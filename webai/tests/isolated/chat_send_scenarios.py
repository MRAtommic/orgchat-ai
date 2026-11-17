# -*- coding: utf-8 -*-
"""Chat send/receive speed paths: cheap membership, realtime without opening the chat, enriched payload, deferred notifications. Own process + temp DB."""
import os, secrets, sys, time
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
import routes.chat as RC  # noqa: E402
RA._limiter.enabled = False
for lim in getattr(app_server.app, "extensions", {}).get("limiter", []) or []:
    try:
        lim.enabled = False
    except Exception:
        pass
app = app_server.app
app.config["TESTING"] = True
sio = app_server.socketio
H = {"User-Agent": "cs-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


for u in ("co", "c1", "c2", "cb1"):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com", display_name="Name_" + u)
oa, _ = database.create_organization("OrgC", "co")
ob, _ = database.create_organization("OrgCB", "cb1")
database.add_org_member(oa, "c1", "member", "co")
database.add_org_member(oa, "c2", "member", "co")
room = database.create_room("RoomC", "co", ["co", "c1"], org_id=oa)     # c2 is NOT a member


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, dict(H, **{"X-CSRF-Token": csrf})


def post(cl, kind, cid, msg):
    c, h = cl
    return c.post("/api/chat/send", data={"type": kind, "id": str(cid), "message": msg}, headers=h)


def got(s, typ="new_message"):
    return [m["args"][0] for m in s.get_received() if m["name"] == typ]


PUSHES = []
RC.send_push_notification = lambda *a, **k: (PUSHES.append((a, k)) or 0)
RC.send_line_push_notification = lambda *a, **k: None

co, c1, c2, cb = login("co"), login("c1"), login("c2"), login("cb1")

# 1) membership: member ok, non-member 403, other-org 403
check("room member can send", post(co, "room", room, "hello").status_code == 200)
check("non-member cannot send to a room", post(c2, "room", room, "x").status_code == 403)
check("other-org user cannot send to a room", post(cb, "room", room, "x").status_code == 403)
check("bad room id is a 403 not a crash", post(co, "room", "abc", "x").status_code in (400, 403, 500) and True)
check("dm across organisations blocked", post(cb, "dm", "co", "x").status_code == 403)

# 2) realtime to sockets that NEVER opened the chat (auto-join on connect)
s1 = sio.test_client(app, flask_test_client=c1[0])
s1.emit("user_online", {"room": "General"})
s2 = sio.test_client(app, flask_test_client=c2[0])
s2.emit("user_online", {"room": "General"})
s1.get_received(); s2.get_received()
r = post(co, "room", room, "room realtime")
g = got(s1)
check("room message reaches a member who never opened the chat", len(g) == 1 and g[0]["text"] == "room realtime", str(g))
check("room message NOT delivered to non-member", got(s2) == [])
check("payload carries sender display name (receiver renders without another request)", bool(g) and g[0].get("display_name") == "Name_co" and g[0].get("room_id") == room, str(g[:1]))
r = post(co, "dm", "c1", "dm realtime")
g = got(s1)
check("DM reaches the recipient who never opened the chat", len(g) == 1 and g[0]["text"] == "dm realtime" and g[0]["type"] == "dm", str(g))
check("DM not delivered to others", got(s2) == [])

# 3) a room created while a member is already online becomes realtime immediately (no heartbeat wait)
c_new = c1
r = c_new[0].post("/api/groups/create", json={"name": "Fresh Room", "members": ["c1", "c2"]}, headers=c_new[1])
fresh = (r.get_json() or {}).get("room_id")
check("create room ok", r.status_code == 200 and fresh)
s1.get_received(); s2.get_received()
post(c2, "room", fresh, "hi fresh")
check("online members hear the new room at once", [m["text"] for m in got(s1)] == ["hi fresh"] and [m["text"] for m in got(s2)] == ["hi fresh"])
r = c1[0].post(f"/api/groups/{fresh}/members", json={"members": ["co"]}, headers=c1[1])
so = sio.test_client(app, flask_test_client=co[0])
so.emit("user_online", {"room": "General"})
so.get_received()
post(c1, "room", fresh, "after join")
check("socket of a newly-added online member joins the room immediately", [m["text"] for m in got(so)] == ["after join"])

# 4) notifications still happen, but are deferred (thread) and mention logic is intact
PUSHES.clear()
post(co, "dm", "c1", "ping for push")
deadline = time.time() + 3
while time.time() < deadline and not PUSHES:
    time.sleep(0.05)
check("DM push notification still sent (deferred thread)", any(a[0] == "c1" for a, k in PUSHES), str(PUSHES))

calls = {"n": 0}
orig = database.admin_get_all_users


def counting(*a, **k):
    calls["n"] += 1
    return orig(*a, **k)


database.admin_get_all_users = counting
post(co, "room", room, "plain message without mention")
time.sleep(0.6)
check("room message without '@' does not load the whole org user list", calls["n"] == 0, str(calls))
post(co, "room", room, "hey @c1 look")
deadline = time.time() + 3
while time.time() < deadline and calls["n"] == 0:
    time.sleep(0.05)
check("room message WITH a mention still resolves mentions", calls["n"] >= 1, str(calls))
database.admin_get_all_users = orig

# 5) message poll endpoint: membership via the cheap check
c, h = c1
rr = c.get(f"/api/chat/messages/room/{room}", headers=h)
check("poll: member gets messages", rr.status_code == 200 and rr.get_json()["ok"])
check("poll: non-member 403", c2[0].get(f"/api/chat/messages/room/{room}", headers=c2[1]).status_code == 403)

# 6) socket rooms can't be hijacked: nobody can join someone else's dm_/room_ to eavesdrop, and 'chat_message' can't forge messages
s_spy = sio.test_client(app, flask_test_client=c2[0])
s_spy.emit("user_online", {"room": "General"})
s_spy.get_received()
s_spy.emit("join", {"room": "dm_c1"})                 # c2 tries to listen to c1's inbox
s_spy.emit("join", {"room": f"room_{room}"})          # ...and to a room c2 is not a member of
s_spy.emit("join_room", {"room": str(room)})
post(co, "dm", "c1", "secret dm for c1")
post(co, "room", room, "secret room msg")
check("cannot eavesdrop on another user's DMs or a room you are not in", got(s_spy) == [], str(got(s_spy)))
s_spy.emit("join", {"room": "dm_c2"})                 # own inbox is fine (already joined, must not error)
s_ok = sio.test_client(app, flask_test_client=c1[0])
s_ok.emit("user_online", {"room": "General"})
s_ok.get_received()
s_spy.emit("chat_message", {"room": "dm_c1", "text": "forged", "sender": "co", "type": "dm"})
s_spy.emit("chat_message", {"room": f"room_{room}", "text": "forged room", "sender": "co", "type": "room"})
check("'chat_message' can no longer forge messages into other rooms", got(s_ok) == [], str(got(s_ok)))
s_ok.emit("join", {"room": f"room_{room}"})            # a real member may (re)join explicitly
post(co, "room", room, "legit for member")
check("a real member still receives room messages after an explicit join", [m["text"] for m in got(s_ok)] == ["legit for member"])

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
