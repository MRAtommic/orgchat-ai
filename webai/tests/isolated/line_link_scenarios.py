# -*- coding: utf-8 -*-
"""LINE linking rules: no auto-link by email, ask before moving a LINE from another account, never fall back to Admin/few. Own process + temp DB."""
import base64, json, os, secrets, sys, time
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "ll-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


for u, em in (("alice", "alice@example.com"), ("bob", "bob@example.com"), ("carol", "carol@example.com")):
    database.admin_create_user(u, PW, role="user", email=em)


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, dict(H, **{"X-CSRF-Token": csrf, "Content-Type": "application/json"})


_N = [0]


def bind(c, h, line_id, **extra):
    """ผูกด้วยโทเค็นที่บอทออกให้ (จำลองด้วย line_link_create) — ช่องกรอก LINE User ID ตรงๆ ถูกเอาออกแล้ว"""
    _N[0] += 1
    tok = f"tok-bind-{_N[0]}"
    database.line_link_create(tok, line_id)
    return c.post("/api/user/bind-line-direct", json=dict({"token": tok}, **extra), headers=h)


def owner(line_id):
    return database.get_username_by_line_id(line_id)


# ---- 1) direct bind (API) -------------------------------------------------
LID = "U" + "a" * 32
ca, ha = login("alice")
cb, hb = login("bob")
r = bind(ca, ha, LID)
check("free LINE binds normally", r.status_code == 200 and owner(LID) == "alice", r.get_data(as_text=True)[:200])
r = bind(ca, ha, LID)
check("re-binding own LINE needs no confirmation", r.status_code == 200 and owner(LID) == "alice")
r = bind(cb, hb, LID)
j = r.get_json() or {}
check("LINE owned by another account → 409 needs_confirm", r.status_code == 409 and j.get("needs_confirm") and j.get("owner") == "alice", str(j))
check("…and nothing moved yet", owner(LID) == "alice")
r = bind(cb, hb, LID, confirm_move=True)
check("with confirm_move the LINE moves", r.status_code == 200 and owner(LID) == "bob", r.get_data(as_text=True)[:200])

# token flavour: the one-time token must survive the 409 so the confirmed retry still works
LID2 = "U" + "b" * 32
# (one account holds one LINE id, so a third account is used here)
cc, hc = login("carol")
dave_owner = database.admin_create_user("dave", PW, role="user", email="dave@example.com")
cd, hd = login("dave")
bind(cd, hd, LID2)
database.line_link_create("tok-move-1", LID2)
r = cc.post("/api/user/bind-line-direct", json={"token": "tok-move-1"}, headers=hc)
check("token bind of an owned LINE → 409, token kept", r.status_code == 409 and database.line_link_get("tok-move-1") is not None)
r = cc.post("/api/user/bind-line-direct", json={"token": "tok-move-1", "confirm_move": True}, headers=hc)
check("confirmed retry with the same token works and consumes it", r.status_code == 200 and owner(LID2) == "carol" and database.line_link_get("tok-move-1") is None)

# ---- 2) web LINE Login callback ---------------------------------------------
def jwt_with(payload):
    b = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")
    return b({"alg": "none"}) + "." + b(payload) + ".sig"


class Resp:
    def __init__(self, code, data):
        self.status_code, self._d = code, data

    def json(self):
        return self._d


class FakeHttp:
    def __init__(self, line_id, email, name="Tester"):
        self.line_id, self.email, self.name = line_id, email, name

    def post(self, url, **k):
        if url.endswith("/token"):
            d = {"access_token": "AT", "id_token": jwt_with({"email": self.email} if self.email else {})}
            return Resp(200, d)
        return Resp(200, {})

    def get(self, url, **k):
        return Resp(200, {"userId": self.line_id, "displayName": self.name})


RA._get_line_http_session = lambda: FakeHttp(CUR["id"], CUR["email"], CUR.get("name", "Tester"))
RA._get_line_login_config = lambda: {"channel_id": "123", "channel_secret": "s"}
CUR = {}


def callback(state_payload):
    st = secrets.token_hex(8)
    database.oauth_state_store(f"line_{st}", dict(state_payload, created_at=time.time(), origin_host="http://localhost:5999"))
    return app.test_client().get(f"/api/line/login-callback?code=c{st}&state={st}")


# 2a) login mode, LINE not linked anywhere, email matches an existing account → refused, no link, no new account
CUR.update(id="U" + "c" * 32, email="alice@example.com", name="Mallory")
before = len(database.admin_get_all_users()) if hasattr(database, "admin_get_all_users") else None
r = callback({"username": None, "mode": "login"})
body = r.get_data(as_text=True)
check("LINE email matching an existing account does NOT auto-link / log in", r.status_code == 403 and owner(CUR["id"]) is None, f"{r.status_code} {owner(CUR['id'])}")
check("…and explains what to do", "เชื่อม LINE" in body)
with app.test_client() as c2:
    r = c2.get("/api/me", headers=H)
    check("…and no session was created", r.status_code in (401, 403) or not (r.get_json() or {}).get("ok"), str(r.status_code))
if before is not None:
    check("…and no duplicate account was created", len(database.admin_get_all_users()) == before)

# 2b) login mode with an already-linked LINE still works
r = callback({"username": None, "mode": "login"}) if False else None
CUR.update(id=LID, email=None, name="Bob")
r = callback({"username": None, "mode": "login"})
check("already-linked LINE can still log in", r.status_code in (302, 303) and "login_success=line" in r.headers.get("Location", ""), f"{r.status_code} {r.headers.get('Location')}")

# 2c) link mode: LINE belongs to bob, alice links → confirm page, nothing moved
CUR.update(id=LID, email=None, name="Bob")
r = callback({"username": "alice", "mode": "link"})
body = r.get_data(as_text=True)
check("linking an owned LINE shows the confirmation page", r.status_code == 200 and "confirm-move" in body and "bob" in body, f"{r.status_code}")
check("…and nothing moved yet (2c)", owner(LID) == "bob", str(owner(LID)))
import re
m = re.search(r'token:("[^"]+")', body)
tok = json.loads(m.group(1)) if m else None
check("confirmation page carries a token", bool(tok))

anon = app.test_client()
r = anon.post("/api/line/confirm-move", json={"token": "nope"})
check("unknown token rejected", r.status_code == 400)
r = anon.post("/api/line/confirm-move", json={"token": tok})
check("valid token moves the LINE to alice", r.status_code == 200 and owner(LID) == "alice", r.get_data(as_text=True)[:200])
r = anon.post("/api/line/confirm-move", json={"token": tok})
check("token is single-use", r.status_code == 400)

# wrong logged-in user cannot use someone else's token
CUR.update(id=LID, email=None)
r = callback({"username": "bob", "mode": "link"})
tok2 = json.loads(re.search(r'token:("[^"]+")', r.get_data(as_text=True)).group(1))
r = ca.post("/api/line/confirm-move", json={"token": tok2}, headers=ha)     # alice (logged in) tries bob's token
check("a token cannot be used by a different logged-in account", r.status_code == 403 and owner(LID) == "alice", f"{r.status_code} {owner(LID)}")

# expired token
database.oauth_state_store("linemove_old", {"username": "bob", "line_user_id": LID, "from": "alice", "expires_at": time.time() - 5})
r = anon.post("/api/line/confirm-move", json={"token": "old"})
check("expired token rejected", r.status_code == 400 and owner(LID) == "alice")

# 2d) link mode, LINE free → links directly as before
CUR.update(id="U" + "d" * 32, email=None)
r = callback({"username": "alice", "mode": "link"})
check("linking a free LINE works without a prompt", r.status_code == 200 and owner(CUR["id"]) == "alice" and "confirm-move" not in r.get_data(as_text=True))

# 2e) LINE ที่ยังไม่ผูกบัญชีใด: ห้ามสร้างบัญชีเปล่า/ห้ามล็อกอินเป็นคนอื่น → ขึ้นหน้าแจ้งให้ล็อกอินวิธีเดิมแล้วเชื่อม (403)
CUR.update(id="U" + "e" * 32, email=None, name="Newbie")
orig = database.admin_create_user
database.admin_create_user = lambda *a, **k: False
r = callback({"username": None, "mode": "login"})
database.admin_create_user = orig
check("unlinked LINE → 403 guidance page, no empty account, not a login as few/Admin", r.status_code == 403 and database.get_username_by_line_id(CUR["id"]) is None and "login_success" not in r.headers.get("Location", ""), f"{r.status_code}")
with app.test_client() as c3:
    check("…and no session", not (c3.get("/api/me", headers=H).get_json() or {}).get("ok"))

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
