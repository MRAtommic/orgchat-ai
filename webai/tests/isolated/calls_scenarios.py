# -*- coding: utf-8 -*-
"""Calls: signaling hardening (spoofed sender, cross-org, offline callee, bad type/size) + ICE server config. Own process + temp DB."""
import os, secrets, sys, base64, hmac, hashlib
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
for k in ("CLOUDFLARE_TURN_KEY_ID", "CLOUDFLARE_TURN_API_TOKEN", "METERED_APP_NAME", "METERED_API_KEY", "TURN_URLS", "TURN_SECRET", "TURN_USERNAME", "TURN_CREDENTIAL"):
    os.environ.pop(k, None)
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
import routes.chat as RC  # noqa: E402
import webrtc_ice  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
sio = app_server.socketio
H = {"User-Agent": "call-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


for u in ("ownerA", "a1", "a2", "ownerB", "b1", "solo", "solo2"):
    database.admin_create_user(u, PW, role="user", email=u + "@example.com")
oa, _ = database.create_organization("OrgA", "ownerA")
ob, _ = database.create_organization("OrgB", "ownerB")
database.add_org_member(oa, "a1", "member", "ownerA")
database.add_org_member(oa, "a2", "member", "ownerA")
database.add_org_member(ob, "b1", "member", "ownerB")


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    return c


def sock(u):
    s = sio.test_client(app, flask_test_client=login(u))
    s.emit("user_online", {"room": "General"})
    s.get_received()
    return s


def sock_keep(u):
    """เชื่อมต่อแล้วเปิดแอป (user_online) โดย "ไม่" ล้างข้อความที่ได้รับ — ใช้ดูสายที่ส่งมาตอนเปิดแอป"""
    s = sio.test_client(app, flask_test_client=login(u))
    s.emit("user_online", {"room": "General"})
    s.emit("webrtc_ready")       # หน้าเว็บลงทะเบียนตัวรับสายเสร็จแล้ว
    return s


def got(s, typ="webrtc_signal"):
    return [m["args"][0] for m in s.get_received() if m["name"] == typ]


# silence real push attempts
RC.send_push_notification = lambda *a, **k: None
RC._rtc_last_offer.clear()

a1, a2, b1 = sock("a1"), sock("a2"), sock("b1")
OFFER = {"sdp": "v=0", "type": "offer"}

# 1) normal same-org call; spoofed sender is ignored
a1.emit("webrtc_signal", {"target": "a2", "sender": "ownerB", "type": "offer", "payload": OFFER, "callType": "video"})
g = got(a2)
check("same-org offer delivered", len(g) == 1 and g[0]["type"] == "offer", str(g))
check("sender taken from session, not payload", bool(g) and g[0]["sender"] == "a1", str(g))
check("callType kept", bool(g) and g[0].get("callType") == "video")

# 2) answer / ice go through
a2.emit("webrtc_signal", {"target": "a1", "type": "answer", "payload": {"sdp": "x", "type": "answer"}})
check("answer delivered", [m["type"] for m in got(a1)] == ["answer"])
a1.emit("webrtc_signal", {"target": "a2", "type": "ice", "payload": {"candidate": "c"}})
check("ice delivered", [m["type"] for m in got(a2)] == ["ice"])

# 2b) 'media' (camera/screen on/off) is relayed with the sender taken from the session
a1.emit("webrtc_signal", {"target": "a2", "sender": "ownerB", "type": "media", "payload": {"video": False}})
g = got(a2)
check("media signal relayed", len(g) == 1 and g[0]["type"] == "media" and g[0]["payload"] == {"video": False} and g[0]["sender"] == "a1", str(g))

# 3) cross-org blocked, both directions
RC._rtc_last_offer.clear()
a1.emit("webrtc_signal", {"target": "b1", "type": "offer", "payload": OFFER})
check("cross-org offer blocked", got(b1) == [])
check("cross-org: caller not told anything either", got(a1) == [])
b1.emit("webrtc_signal", {"target": "a1", "type": "ice", "payload": {"candidate": "c"}})
check("cross-org ice blocked", got(a1) == [])

# 4) invalid type / self / missing target / oversized payload
for name, body in [("unknown type", {"target": "a2", "type": "evil", "payload": 1}),
                   ("self target", {"target": "a1", "type": "offer", "payload": OFFER}),
                   ("no target", {"type": "offer", "payload": OFFER}),
                   ("oversized payload", {"target": "a2", "type": "ice", "payload": {"x": "y" * 30000}})]:
    RC._rtc_last_offer.clear()
    a1.emit("webrtc_signal", body)
    check(f"rejected: {name}", got(a2) == [])
a1.emit("webrtc_signal", "not-a-dict")
check("non-dict ignored (no crash)", True)

# 5) callee NOT in the app: the call is parked (45s), caller keeps waiting, a push notification is sent, and the call is delivered when the callee opens the app
PUSHES = []
RC.send_push_notification = lambda *a, **k: (PUSHES.append((a, k)) or 1)
RC._pending_calls.clear()
RC._rtc_last_offer.clear()
a2.disconnect()
got(a1)
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER, "callType": "video"})
g = got(a1)
check("offline callee => caller told 'ringing_offline' (not dropped)", len(g) == 1 and g[0]["type"] == "ringing_offline" and g[0]["payload"]["notified"] is True, str(g))
check("push sent as a call notification", any(k.get("tag") == "incoming_call" and (k.get("extra") or {}).get("call") for a_, k in PUSHES) and "a1" in PUSHES[-1][0][1], str(PUSHES[-1:]))
check("push opens the app with the caller in the url", "incoming_call=a1" in PUSHES[-1][1].get("url", ""))
check("call parked on the server", "a2" in RC._pending_calls and RC._pending_calls["a2"]["sender"] == "a1")
a1.emit("webrtc_signal", {"target": "a2", "type": "ice", "payload": {"candidate": "c1"}})
a1.emit("webrtc_signal", {"target": "a2", "type": "ice", "payload": {"candidate": "c2"}})
check("caller ICE buffered while waiting", len(RC._pending_calls["a2"]["ice"]) == 2)
a2 = sio.test_client(app, flask_test_client=login("a2"))
a2.emit("user_online", {"room": "General"})      # ซ็อกเก็ตเพิ่งเชื่อมต่อ แต่หน้าเว็บยังไม่พร้อมรับสาย
check("connecting alone does NOT consume the parked call (listener not registered yet)", "a2" in RC._pending_calls and not [m for m in got(a2) if m["type"] == "offer"])
a2.emit("webrtc_ready")                          # หน้าเว็บพร้อมแล้ว → ส่งสาย
g = got(a2)
types = [m["type"] for m in g]
check("callee gets the call when the app opens (offer first, then ICE)", types == ["offer", "ice", "ice"], str(types))
check("late offer carries caller + callType + late flag", g[0]["sender"] == "a1" and g[0].get("callType") == "video" and g[0].get("late") is True, str(g[:1]))
check("parked call removed after delivery", "a2" not in RC._pending_calls)
a2.disconnect()
a2 = sock_keep("a2")
check("delivered only once (no ghost call on reconnect)", [m for m in got(a2) if m["type"] == "offer"] == [])

# caller hangs up before the callee ever opens the app -> nothing delivered, 'missed call' push
RC._rtc_last_offer.clear()
a2.disconnect()
PUSHES.clear()
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER})
got(a1)
a1.emit("webrtc_signal", {"target": "a2", "type": "end", "payload": None})
check("caller cancels -> parked call cleared", "a2" not in RC._pending_calls)
check("caller cancels -> 'missed call' push", any(k.get("tag") == "missed_call" for a_, k in PUSHES), str(PUSHES))
a2 = sock_keep("a2")
check("cancelled call is not delivered later", [m for m in got(a2) if m["type"] == "offer"] == [])

# expired call is not delivered; missed-call push on expiry
RC._rtc_last_offer.clear()
a2.disconnect()
PUSHES.clear()
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER})
got(a1)
RC._pending_calls["a2"]["ts"] -= 100          # pretend 100s passed
a2 = sock_keep("a2")
check("expired call not delivered", [m for m in got(a2) if m["type"] == "offer"] == [])
RC._pending_calls.clear()
# timer-based expiry path
RC._pending_calls["a2"] = {"sender": "a1", "payload": OFFER, "callType": "audio", "ts": 123.0, "ice": []}
PUSHES.clear()
RC._expire_pending("a2", "a1", 123.0)
check("expiry timer: call removed + missed-call push", "a2" not in RC._pending_calls and any(k.get("tag") == "missed_call" for a_, k in PUSHES))
RC._pending_calls["a2"] = {"sender": "a1", "payload": OFFER, "callType": "audio", "ts": 999.0, "ice": []}
RC._expire_pending("a2", "a1", 123.0)       # stale timer (a newer call exists) must not clear it
check("stale expiry timer does not clear a newer call", "a2" in RC._pending_calls)
RC._pending_calls.clear()

# LINE backup + ring-again: the callee is not in the app, has a bound LINE account
LINES = []
RC.send_line_push_notification = lambda *a, **k: LINES.append(a)
_orig_line_id = database.get_line_id_by_username
database.get_line_id_by_username = lambda u: "Ulinebound" if u == "a2" else None
RC._pending_calls.clear()
RC._rtc_last_offer.clear()
RC.send_push_notification = lambda *a, **k: (PUSHES.append((a, k)) or 1)
PUSHES.clear()
a2.disconnect()
got(a1)
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER, "callType": "video"})
g = got(a1)
check("caller told which channels were used (push + LINE)", len(g) == 1 and g[0]["payload"]["notified"] is True and g[0]["payload"]["line"] is True, str(g))
import time as _t
_t.sleep(0.3)
check("LINE call alert sent to the callee", len(LINES) == 1 and LINES[0][0] == "a2" and "a1" in LINES[0][1], str(LINES))
ts0 = RC._pending_calls["a2"]["ts"]
PUSHES.clear()
RC._ring_again("a2", "a1", ts0)
check("ring-again re-sends the call notification (renotify, require interaction)", len(PUSHES) == 1 and PUSHES[0][1]["extra"]["renotify"] is True and PUSHES[0][1]["extra"]["require_interaction"] is True, str(PUSHES))
PUSHES.clear()
RC._ring_again("a2", "a1", ts0 - 5)            # stale timer of an older call
check("stale ring-again timer does nothing", PUSHES == [])
RC._pending_calls.clear()
PUSHES.clear()
RC._ring_again("a2", "a1", ts0)
check("ring-again does nothing once the call is gone", PUSHES == [])
database.get_line_id_by_username = _orig_line_id
RC.send_line_push_notification = lambda *a, **k: None

# push subscription status endpoint
cl = login("a1")
r = cl.get("/api/notifications/subscribed", headers=H).get_json()
check("subscription status endpoint answers", r["ok"] is True and r["count"] == 0 and "server_ready" in r, str(r))
database.add_push_subscription("a1", '{"endpoint":"https://x/y"}')
check("status endpoint sees a stored subscription", cl.get("/api/notifications/subscribed", headers=H).get_json()["count"] == 1)

# no push subscription: still parked, caller told 'notified: false'
RC.send_push_notification = lambda *a, **k: 0
RC._rtc_last_offer.clear()
try:
    a2.disconnect()
except RuntimeError:
    pass                                   # already offline from the previous scenario
got(a1)
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER})
g = got(a1)
check("no push subscription => ringing_offline with notified False", len(g) == 1 and g[0]["type"] == "ringing_offline" and g[0]["payload"]["notified"] is False, str(g))
RC._pending_calls.clear()
RC.send_push_notification = lambda *a, **k: None

# 6) offer rate limit
RC._rtc_last_offer.clear()
a2 = sock("a2")
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER})
a1.emit("webrtc_signal", {"target": "a2", "type": "offer", "payload": OFFER})
check("offer spam throttled (1 delivered)", len([m for m in got(a2) if m["type"] == "offer"]) == 1)

# 7) users without any org: only people they've privately messaged
s1, s2 = sock("solo"), sock("solo2")
RC._rtc_last_offer.clear()
s1.emit("webrtc_signal", {"target": "solo2", "type": "offer", "payload": OFFER})
check("no-org stranger blocked", got(s2) == [])
c = database._get_conn()
c.execute("INSERT INTO private_messages (sender, recipient, text) VALUES ('solo','solo2','hi')")
c.commit()
c.close()
RC._rtc_last_offer.clear()
s1.emit("webrtc_signal", {"target": "solo2", "type": "offer", "payload": OFFER})
check("no-org with DM history allowed", [m["type"] for m in got(s2)] == ["offer"])

# 8) ICE endpoint + provider logic
cl = login("a1")
r = cl.get("/api/webrtc/ice", headers=H)
j = r.get_json()
check("ice endpoint ok", r.status_code == 200 and j["ok"] and any("stun:" in str(s["urls"]) for s in j["iceServers"]))
check("unconfigured => turn_configured False + fallback", j["turn_configured"] is False and j["source"] == "public-fallback")
check("ice endpoint needs login", app.test_client().get("/api/webrtc/ice", headers=H).status_code in (401, 302, 403))

# static TURN
os.environ.update({"TURN_URLS": "turn:t.example.com:3478, turns:t.example.com:5349", "TURN_USERNAME": "u", "TURN_CREDENTIAL": "p"})
v = webrtc_ice.get_ice_config(force=True)
turn = [s for s in v["iceServers"] if s.get("username")]
check("static TURN used", v["turn_configured"] and v["source"] == "static" and turn[0]["urls"] == ["turn:t.example.com:3478", "turns:t.example.com:5349"], str(v))
check("static TURN replaces public fallback", not any("openrelay" in str(s["urls"]) for s in v["iceServers"]))

# coturn shared-secret: credential = base64(hmac-sha1(secret, username))
os.environ.pop("TURN_USERNAME")
os.environ.pop("TURN_CREDENTIAL")
os.environ["TURN_SECRET"] = "s3cret"
v = webrtc_ice.get_ice_config(force=True)
t0 = [s for s in v["iceServers"] if s.get("username")][0]
exp = base64.b64encode(hmac.new(b"s3cret", t0["username"].encode(), hashlib.sha1).digest()).decode()
check("coturn secret creds valid", v["source"] == "coturn-secret" and t0["credential"] == exp and int(t0["username"].split(":")[0]) > 0, str(t0))
os.environ.pop("TURN_URLS")
os.environ.pop("TURN_SECRET")

# Cloudflare (mocked HTTP): STUN entries stripped, TURN kept
import requests  # noqa: E402


class _R:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


_orig_post, _orig_get = requests.post, requests.get
requests.post = lambda url, **k: _R({"iceServers": [
    {"urls": ["stun:stun.cloudflare.com:3478"]},
    {"urls": ["turn:turn.cloudflare.com:3478?transport=udp", "turns:turn.cloudflare.com:5349?transport=tcp"], "username": "cfu", "credential": "cfc"}]})
os.environ.update({"CLOUDFLARE_TURN_KEY_ID": "kid", "CLOUDFLARE_TURN_API_TOKEN": "tok"})
v = webrtc_ice.get_ice_config(force=True)
check("cloudflare TURN parsed", v["source"] == "cloudflare" and any(s.get("username") == "cfu" for s in v["iceServers"]), str(v))
check("cloudflare STUN entry not duplicated", sum(1 for s in v["iceServers"] if "stun.cloudflare.com" in str(s["urls"])) == 0)


def _boom(*a, **k):
    raise ConnectionError("down")


requests.post = _boom
v = webrtc_ice.get_ice_config(force=True)
check("provider outage => fallback, no crash", v["turn_configured"] is False and len(v["iceServers"]) >= 3)
os.environ.pop("CLOUDFLARE_TURN_KEY_ID")
os.environ.pop("CLOUDFLARE_TURN_API_TOKEN")

# Metered (mocked)
requests.get = lambda url, **k: _R([{"urls": "turn:a.relay.metered.ca:80", "username": "mu", "credential": "mc"}])
os.environ.update({"METERED_APP_NAME": "myapp", "METERED_API_KEY": "key"})
v = webrtc_ice.get_ice_config(force=True)
check("metered TURN parsed", v["source"] == "metered" and any(s.get("username") == "mu" for s in v["iceServers"]), str(v))
requests.post, requests.get = _orig_post, _orig_get

# 9) typing indicator ("กำลังพิมพ์")
RC._typing_last.clear()
ta1, ta2, tb1 = sock("a1"), sock("a2"), sock("b1")
rid = database.create_room("TypingRoom", "ownerA", ["ownerA", "a1", "a2"], org_id=oa)
ro = sock("ownerA")
for s in (ta1, ta2, tb1, ro):
    s.get_received()

ta1.emit("user_typing", {"type": "dm", "id": "a2"})
g = got(ta2, "user_typing")
check("dm typing reaches the peer", len(g) == 1 and g[0]["username"] == "a1", str(g))
check("dm typing: chat_id is the typist's username (receiver's DM id)", bool(g) and g[0]["chat_id"] == "a1" and g[0]["chat_type"] == "dm", str(g))
check("dm typing not echoed to typist", got(ta1, "user_typing") == [])
check("dm typing not leaked to others", got(ro, "user_typing") == [] and got(tb1, "user_typing") == [])

RC._typing_last.clear()
ta1.emit("user_typing", {"type": "dm", "id": "b1"})
check("cross-org typing blocked", got(tb1, "user_typing") == [])

RC._typing_last.clear()
ta1.emit("user_typing", {"type": "dm", "id": "a1"})
ta1.emit("user_typing", {"type": "dm", "id": "ai-assistant"})
ta1.emit("user_typing", "garbage")
ta1.emit("user_typing", {"type": "weird", "id": "a2"})
check("self / AI / garbage / unknown type ignored", got(ta1, "user_typing") == [] and got(ta2, "user_typing") == [])

RC._typing_last.clear()
ta1.emit("user_typing", {"type": "room", "id": rid})
gr = got(ta2, "user_typing") + got(ro, "user_typing")
check("room typing reaches the other members", len(gr) == 2 and all(m["chat_id"] == str(rid) and m["chat_type"] == "room" for m in gr), str(gr))
check("room typing not delivered to non-members", got(tb1, "user_typing") == [])

RC._typing_last.clear()
tb1.emit("user_typing", {"type": "room", "id": rid})
check("non-member cannot type into a room", got(ta2, "user_typing") == [] and got(ro, "user_typing") == [])

RC._typing_last.clear()
ta1.emit("user_stopped_typing", {"type": "dm", "id": "a2"})
g = got(ta2, "user_stopped_typing")
check("stopped-typing relayed", len(g) == 1 and g[0]["username"] == "a1" and g[0]["chat_id"] == "a1", str(g))

RC._typing_last.clear()
ta1.emit("user_typing", {"type": "dm", "id": "a2"})
ta1.emit("user_typing", {"type": "dm", "id": "a2"})
ta1.emit("user_typing", {"type": "dm", "id": "a2"})
check("typing spam throttled (1 relayed)", len(got(ta2, "user_typing")) == 1)

RC._typing_last.clear()
ta1.emit("user_typing", {"room_id": rid})   # legacy payload shape
check("legacy payload (room_id only) still works for rooms", len(got(ta2, "user_typing")) == 1)

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
