# -*- coding: utf-8 -*-
"""LINE binding: the bot issues a short one-time code (+ magic link); the web settings box accepts only that code; raw LINE user ids are rejected;
the magic-link page can prove identity with Google. Temp DB, LINE + Google mocked."""
import json, os, re, secrets, sys, time
assert os.environ.get("DB_PATH") and os.environ.get("DATA_DIR")
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["GOOGLE_CLIENT_ID"] = "123456789-test.apps.googleusercontent.com"
os.environ["VECTOR_BACKEND"] = "python"
sys.path.insert(0, os.getcwd())
import app_server, database  # noqa: E402
import routes.auth as RA  # noqa: E402
import routes.line_webhook as LW  # noqa: E402
RA._limiter.enabled = False
app = app_server.app
app.config["TESTING"] = True
H = {"User-Agent": "lc-ua"}
PW = "Passw0rd!x"
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


database.admin_create_user("web1", PW, role="user", email="web1@example.com")
database.admin_create_user("web2", PW, role="user", email="web2@example.com")
database.admin_create_user("gonly", secrets.token_urlsafe(12), role="user", email="gonly@example.com")   # no password the user knows
oid, _ = database.create_organization("LC Org", "web1")


def login(u):
    c = app.test_client()
    c.post("/api/login", json={"username": u, "password": PW}, headers=H)
    csrf = c.get("/api/csrf-token", headers=H).get_json()["csrf_token"]
    return c, dict(H, **{"X-CSRF-Token": csrf})


def owner(line_id):
    return database.get_username_by_line_id(line_id)


# ---- 1) the bot's /link reply carries a short code -------------------------------------------------
LINE_A = "U" + "a1" * 16 + "a"
SENT = []
LW.reply_to_line = lambda token, msg, *a, **k: SENT.append(msg)
LW.send_line_push_notification = lambda *a, **k: None
LW.process_line_command("/link", LINE_A, "tok")
card = json.dumps(SENT[-1], ensure_ascii=False) if SENT else ""
m = re.search(r"\b([A-Z2-9]{4})-([A-Z2-9]{4})\b", card)
check("/link reply contains an 8-char code (XXXX-XXXX) next to the magic link", bool(m) and "link_magic?token=" in card, card[:200])
code = (m.group(1) + m.group(2)) if m else "ZZZZZZZZ"

# ---- 2) web settings box: code works (any case, hyphen/space), single use, no password prompt --------
c1, h1 = login("web1")
r = c1.post("/api/user/bind-line-direct", json={"token": f"{code[:4].lower()}-{code[4:].lower()}"}, headers=h1)
check("short code (lower-case with hyphen) binds the logged-in account", r.status_code == 200 and owner(LINE_A) == "web1", f"{r.status_code} {r.get_data(as_text=True)[:150]}")
r = c1.post("/api/user/bind-line-direct", json={"token": code}, headers=h1)
check("the code is single-use", r.status_code == 400)
conn = database._get_conn()
left = conn.execute("SELECT COUNT(*) FROM pending_line_links WHERE line_user_id=?", (LINE_A,)).fetchone()[0]
conn.close()
check("after binding, the magic-link token of that LINE is gone too", left == 0, str(left))

# ---- 3) raw LINE user ids are rejected; junk / expired codes fail -------------------------------------
LINE_V = "U" + "f9" * 16 + "f"
r = c1.post("/api/user/bind-line-direct", json={"line_user_id": LINE_V}, headers=h1)
check("raw LINE User ID is rejected (cannot bind someone else's LINE)", r.status_code == 400 and owner(LINE_V) is None, f"{r.status_code}")
r = c1.post("/api/user/bind-line-direct", json={"token": "ABCD-EFGH"}, headers=h1)
check("unknown code rejected", r.status_code == 400)
database.line_link_create("EXPIRED9", LINE_V)
conn = database._get_conn(); conn.execute("UPDATE pending_line_links SET expires_at=? WHERE token='EXPIRED9'", (time.time() - 5,)); conn.commit(); conn.close()
r = c1.post("/api/user/bind-line-direct", json={"token": "EXPIRED9"}, headers=h1)
check("expired code rejected", r.status_code == 400 and owner(LINE_V) is None)

# ---- 4) a LINE already bound elsewhere asks for confirmation (code is kept until confirmed) ----------
LW.process_line_command("/link", LINE_A, "tok2") if False else None
code2 = database.line_link_new_code(LINE_A)
c2, h2 = login("web2")
r = c2.post("/api/user/bind-line-direct", json={"token": code2}, headers=h2)
check("code for a LINE owned by another account → 409 needs_confirm", r.status_code == 409 and (r.get_json() or {}).get("owner") == "web1", f"{r.status_code}")
r = c2.post("/api/user/bind-line-direct", json={"token": code2, "confirm_move": True}, headers=h2)
check("after confirmation the same code moves it", r.status_code == 200 and owner(LINE_A) == "web2")

# ---- 5) magic-link page: Google button (config present) and endpoint --------------------------------
RA.GOOGLE_AUTH_AVAILABLE = True
page = RA.render_login_page("tok-xyz")
check("link page shows the Google button when Google login is configured", "gBtnWrap" in page and "/line/link_magic/google" in page)
RA.GOOGLE_AUTH_AVAILABLE = False
check("…and hides it when Google login is not configured", "gBtnWrap" not in RA.render_login_page("tok-xyz"))
RA.GOOGLE_AUTH_AVAILABLE = True

LINE_G = "U" + "c3" * 16 + "c"
database.line_link_create("magic-g1", LINE_G)
anon = app.test_client()
state = {"email": "gonly@example.com", "verified": True}


def fake_verify(cred, req, client_id, clock_skew_in_seconds=0):
    if cred == "bad":
        raise ValueError("bad token")
    return {"email": state["email"], "email_verified": state["verified"]}


RA.id_token = type("T", (), {"verify_oauth2_token": staticmethod(fake_verify)})
RA.google_requests = type("R", (), {"Request": staticmethod(lambda: None)})


def g(token="magic-g1", cred="good", **kw):
    return anon.post("/line/link_magic/google", json=dict({"token": token, "credential": cred}, **kw))


r = g(cred="bad")
check("invalid Google credential rejected", r.status_code == 400 and owner(LINE_G) is None)
r = g(token="no-such-token")
check("unknown/expired link token rejected", r.status_code == 400)
state["email"] = "nobody@example.com"
r = g()
check("Google email with no OrgChat account → 404 (no account is created)", r.status_code == 404 and owner(LINE_G) is None)
state["email"] = "gonly@example.com"; state["verified"] = False
r = g()
check("unverified Google email rejected", r.status_code == 400 and owner(LINE_G) is None)
state["verified"] = True
r = g()
check("Google proof binds the bot LINE to the password-less account", r.status_code == 200 and owner(LINE_G) == "gonly" and (r.get_json() or {}).get("html"), f"{r.status_code} {r.get_data(as_text=True)[:150]}")
r = g()
check("link token is single-use after Google binding", r.status_code == 400)
# conflict + confirm via Google
LINE_H = "U" + "d4" * 16 + "d"
database.link_line_user("web1", LINE_H)
database.line_link_create("magic-g2", LINE_H)
r = g(token="magic-g2")
check("Google binding of a LINE owned by another account asks for confirmation", r.status_code == 409 and (r.get_json() or {}).get("owner") == "web1", f"{r.status_code}")
r = g(token="magic-g2", confirm_move=True)
check("…and moves it after confirmation", r.status_code == 200 and owner(LINE_H) == "gonly")

print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
sys.exit(1 if FAILS else 0)
