# -*- coding: utf-8 -*-
"""Simple uptime monitor with alerts. Run every few minutes (see install_scheduled_tasks.ps1).

Checks   : http://127.0.0.1:<PORT>/health  (the app)  and  <BASE_URL>/health  (the public tunnel, if https)
Alerts   : after FAIL_THRESHOLD consecutive failures -> one DOWN alert; when it recovers -> one UP alert.
Channels : e-mail via the SMTP_* settings already in .env (to ALERT_EMAIL or SMTP_USER),
           optional LINE push when ALERT_LINE_USER_ID is set (uses LINE_CHANNEL_ACCESS_TOKEN),
           always appended to healthcheck.log next to this file.
State    : healthcheck_state.json (consecutive failures, whether a DOWN alert is open) - nothing secret.
Exit code: 0 healthy, 2 unhealthy.
"""
import json
import os
import smtplib
import socket
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEBAI = HERE.parent
try:
    from dotenv import load_dotenv
    load_dotenv(WEBAI / ".env")
except Exception:
    pass

STATE = HERE / "healthcheck_state.json"
LOG = HERE / "healthcheck.log"
FAIL_THRESHOLD = int(os.environ.get("HEALTH_FAIL_THRESHOLD", "2"))
TIMEOUT = 12


def log(msg):
    line = f"{datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        if LOG.stat().st_size > 1_000_000:  # keep the log small
            LOG.write_text("\n".join(LOG.read_text(encoding="utf-8").splitlines()[-2000:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def check(url):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "orgchat-healthcheck"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            ok = 200 <= r.status < 400
            return ok, f"HTTP {r.status} in {time.time() - t0:.1f}s"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except (urllib.error.URLError, socket.timeout, ConnectionError, OSError) as e:
        return False, f"{type(e).__name__}: {getattr(e, 'reason', e)}"


def send_email(subject, body):
    server, user, pw = (os.environ.get(k, "").strip() for k in ("SMTP_SERVER", "SMTP_USER", "SMTP_PASSWORD"))
    to = os.environ.get("ALERT_EMAIL", "").strip() or user
    if not (server and user and pw and to):
        return False
    port = int(os.environ.get("SMTP_PORT", "587") or 587)
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"], msg["From"], msg["To"] = subject, os.environ.get("SMTP_SENDER", user) or user, to
    try:
        s = smtplib.SMTP_SSL(server, port, timeout=15) if port == 465 else smtplib.SMTP(server, port, timeout=15)
        if port != 465:
            s.starttls()
        s.login(user, pw)
        s.sendmail(msg["From"], [to], msg.as_string())
        s.quit()
        return True
    except Exception as e:
        log(f"e-mail alert failed: {e}")
        return False


def send_line(text):
    tok, uid = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip(), os.environ.get("ALERT_LINE_USER_ID", "").strip()
    if not (tok and uid):
        return False
    try:
        data = json.dumps({"to": uid, "messages": [{"type": "text", "text": text[:900]}]}).encode("utf-8")
        req = urllib.request.Request("https://api.line.me/v2/bot/message/push", data=data, method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
        urllib.request.urlopen(req, timeout=15).read()
        return True
    except Exception as e:
        log(f"LINE alert failed: {e}")
        return False


def alert(subject, body):
    sent = [n for n, f in (("email", lambda: send_email(subject, body)), ("line", lambda: send_line(subject + "\n" + body))) if f()]
    log(f"ALERT '{subject}' sent via: {', '.join(sent) or 'log only (configure SMTP_* or ALERT_LINE_USER_ID)'}")


def main():
    port = os.environ.get("PORT", "5005").strip() or "5005"
    targets = [("app", f"http://127.0.0.1:{port}/health")]
    base = os.environ.get("BASE_URL", "").strip().rstrip("/")
    if base.startswith("https://"):
        targets.append(("public", base + "/health"))
    results = {n: check(u) for n, u in targets}
    healthy = all(ok for ok, _ in results.values())
    detail = "; ".join(f"{n}: {'OK' if ok else 'FAIL'} ({d})" for n, (ok, d) in results.items())

    try:
        st = json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        st = {"fails": 0, "down_alerted": False}
    if healthy:
        if st.get("down_alerted"):
            alert("OrgChat กลับมาใช้งานได้แล้ว", f"{datetime.now():%Y-%m-%d %H:%M:%S}\n{detail}")
        st = {"fails": 0, "down_alerted": False}
        log("healthy - " + detail)
    else:
        st["fails"] = st.get("fails", 0) + 1
        log(f"UNHEALTHY ({st['fails']}/{FAIL_THRESHOLD}) - {detail}")
        if st["fails"] >= FAIL_THRESHOLD and not st.get("down_alerted"):
            alert("OrgChat ล่ม / เข้าไม่ได้", f"{datetime.now():%Y-%m-%d %H:%M:%S}\n{detail}\nตรวจสอบว่าโปรแกรม app_server.py และ cloudflared ยังทำงานอยู่")
            st["down_alerted"] = True
    try:
        STATE.write_text(json.dumps(st), encoding="utf-8")
    except Exception:
        pass
    return 0 if healthy else 2


if __name__ == "__main__":
    sys.exit(main())
