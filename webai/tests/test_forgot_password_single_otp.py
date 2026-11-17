# -*- coding: utf-8 -*-
"""ลืมรหัสผ่าน: อีเมลกับ LINE ต้องได้ OTP ตัวเดียวกัน และ OTP เก่าของบัญชีเดียวกันต้องถูกยกเลิก (ใช้ DB ชั่วคราว ไม่ยิงบริการจริง)"""
import os, subprocess, sys, textwrap
from pathlib import Path

SCRIPT = textwrap.dedent(r'''
    import os, sys, tempfile
    tmp = tempfile.mkdtemp(prefix="otp_")
    os.environ["DB_PATH"] = os.path.join(tmp, "t.db")
    os.environ["DATA_DIR"] = tmp
    os.environ["VECTOR_BACKEND"] = "python"
    for k in ("GROQ_API_KEY","GEMINI_API_KEY","LINE_CHANNEL_ACCESS_TOKEN","LINE_CHANNEL_SECRET","SMTP_HOST","SMTP_USER","SMTP_PASSWORD"):
        os.environ[k] = ""
    sys.path.insert(0, os.getcwd())
    import database
    from routes import auth as A
    FAILS = []
    def check(n, ok, d=""):
        print(("PASS " if ok else "FAIL ") + n + ((" :: " + str(d)) if d and not ok else ""))
        if not ok: FAILS.append(n)

    # --- DB level: ขอผ่านอีเมล แล้วขอผ่านชื่อผู้ใช้ → ต้องเหลือรหัสเดียวที่ใช้ได้ ---
    o1 = database.create_reset_otp("bob@example.com", "bob")
    o2 = database.create_reset_otp("bob@orgchat.ai", "bob")
    ok_old, _ = database.verify_and_consume_reset_otp("bob", o1, "NewPassw0rd!x") if o1 != o2 else (False, "")
    check("older OTP of the same account is invalidated", o1 == o2 or not ok_old)
    conn = database._get_conn()
    n = conn.execute("SELECT COUNT(*) FROM password_reset_otps WHERE username='bob'").fetchone()[0]
    conn.close()
    check("only one active OTP row per user", n <= 1, n)

    # --- API level: ส่งทั้งอีเมลและ LINE ด้วยรหัสเดียวกัน ---
    SENT = {}
    A.send_reset_password_email = lambda to, otp, url="": (SENT.setdefault("email", otp) and True, "")
    database.get_line_user_id_for_username = lambda u: "Uline123"
    class _R:
        status_code = 200; text = "ok"
    import requests
    def _post(url, headers=None, json=None, timeout=None):
        SENT["line"] = json["messages"][0]["text"]; return _R()
    requests.post = _post
    A.billing._get_line_token = lambda: "tok"
    database.get_user_by_email = lambda e: {"username": "carol", "email": e}
    database.get_user_setting = lambda u, *a, **k: {"username": u, "email": "carol@example.com"} if u == "carol" else {}
    database.create_reset_token = lambda u: "tok123"
    from flask import Flask
    app = Flask(__name__); app.secret_key = "x"
    app.register_blueprint(A.auth_bp)
    try:
        A._limiter.enabled = False
    except Exception:
        pass
    with app.test_client() as c:
        r = c.post("/api/auth/forgot-password", json={"username": "carol"})
        j = r.get_json() or {}
        check("request ok", r.status_code == 200 and j.get("ok"), (r.status_code, j))
        otp_email = SENT.get("email")
        line_text = SENT.get("line", "")
        check("both channels were used", bool(otp_email) and bool(line_text), SENT)
        check("LINE message carries the SAME otp as the email", bool(otp_email) and otp_email in line_text, (otp_email, line_text[:80]))
        check("response says all channels share one code", "รหัสเดียวกัน" in (j.get("message") or ""), j.get("message"))
    print("ALL PASSED" if not FAILS else "FAILED: " + ", ".join(FAILS))
''')


def test_forgot_password_single_otp():
    root = Path(__file__).resolve().parent.parent
    p = subprocess.run([sys.executable, "-c", SCRIPT], cwd=str(root), capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=240)
    out = (p.stdout or "") + (p.stderr or "")
    fails = [l for l in out.splitlines() if l.startswith("FAIL")]
    assert "ALL PASSED" in out and not fails, "\n".join(fails) or out[-3000:]
