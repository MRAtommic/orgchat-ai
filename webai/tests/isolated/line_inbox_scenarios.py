# -*- coding: utf-8 -*-
"""Durable LINE inbox: survives restarts, no duplicates, bounded retries. Own process + temp DB."""
import hashlib, hmac, base64, json, os, secrets, sys, threading, time

assert os.environ.get("DB_PATH"), "DB_PATH must point to a temporary database"
os.environ.setdefault("FLASK_SECRET_KEY", secrets.token_hex(16))
os.environ.setdefault("BASE_URL", "http://localhost:5999")
os.environ["LINE_CHANNEL_SECRET"] = "testsecret"
sys.path.insert(0, os.getcwd())

import app_server  # noqa: E402
import database  # noqa: E402
import line_inbox  # noqa: E402
import routes.line_webhook as LW  # noqa: E402

app = app_server.app
FAILS = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond:
        FAILS.append(name)


seen, lock = [], threading.Lock()


def fake_processor(ev):
    with lock:
        seen.append(ev["webhookEventId"])


LW.process_line_event = fake_processor
LW.verify_line_signature = lambda body, sig: hmac.compare_digest(
    base64.b64encode(hmac.new(b"testsecret", body, hashlib.sha256).digest()).decode(), sig or "")


def ev(i, text="hi"):
    return {"type": "message", "webhookEventId": f"E{i}", "replyToken": "rt", "source": {"type": "user", "userId": "U1"},
            "message": {"type": "text", "id": f"M{i}", "text": text}}


def post(events, good_sig=True):
    body = json.dumps({"events": events}).encode()
    sig = base64.b64encode(hmac.new(b"testsecret", body, hashlib.sha256).digest()).decode() if good_sig else "bad"
    return app.test_client().post("/api/line/webhook", data=body, headers={"X-Line-Signature": sig, "Content-Type": "application/json"})


def wait(cond, t=5):
    end = time.time() + t
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


def status(eid):
    c = database._get_conn()
    try:
        r = c.execute("SELECT status, attempts FROM line_event_inbox WHERE event_id=?", (eid,)).fetchone()
        return tuple(r) if r else None
    finally:
        c.close()


def setrow(eid, **kw):
    c = database._get_conn()
    try:
        c.execute("UPDATE line_event_inbox SET " + ",".join(f"{k}=?" for k in kw) + " WHERE event_id=?", (*kw.values(), eid))
        c.commit()
    finally:
        c.close()


# 1. normal flow
r = post([ev(1)])
check("webhook returns 200", r.status_code == 200)
check("event processed once", wait(lambda: seen == ["E1"]), str(seen))
check("event marked done", wait(lambda: status("E1") == ("done", 1)), str(status("E1")))
check("bad signature rejected", post([ev(9)], good_sig=False).status_code == 400)
check("rejected event not stored", status("E9") is None)

# 2. duplicate delivery, even after in-memory dedup cache is wiped (simulates restart)
LW._PROCESSED_WEBHOOK_EVENTS.clear()
post([ev(1)])
time.sleep(0.5)
check("duplicate after 'restart' not processed again", seen == ["E1"], str(seen))

# 3. crash after accept (never processed) -> recovered once
eid, new = line_inbox.accept(ev(2))
check("accept stores new event", new and status("E2") == ("pending", 0))
check("accept reports duplicate", line_inbox.accept(ev(2))[1] is False)
check("fresh pending event not grabbed too early", line_inbox.recover(fake_processor) == 0)
setrow("E2", received_at=time.time() - 60)
check("stranded event recovered", line_inbox.recover(fake_processor) == 1 and wait(lambda: "E2" in seen), str(seen))
check("recovered event marked done", wait(lambda: status("E2") == ("done", 1)), str(status("E2")))
check("recover again does nothing", line_inbox.recover(fake_processor) == 0)

# 4. crash mid-processing (stale 'processing')
line_inbox.accept(ev(3))
setrow("E3", status="processing", attempts=1, started_at=time.time() - 300, received_at=time.time() - 320)
check("stale processing event retried", line_inbox.recover(fake_processor) == 1 and wait(lambda: "E3" in seen))
check("retry counted", wait(lambda: status("E3") == ("done", 2)), str(status("E3")))

# 5. retry cap
line_inbox.accept(ev(4))
setrow("E4", status="processing", attempts=line_inbox.MAX_ATTEMPTS, started_at=time.time() - 300, received_at=time.time() - 320)
before = len(seen)
n = line_inbox.recover(fake_processor)
time.sleep(0.4)
check("event that already used all attempts is not retried again", "E4" not in seen and len(seen) == before, f"n={n}")

# 6. too old
line_inbox.accept(ev(5))
setrow("E5", received_at=time.time() - 3600)
line_inbox.recover(fake_processor)
time.sleep(0.4)
check("very old stranded event expires instead of replying late", "E5" not in seen and status("E5")[0] == "expired", str(status("E5")))

# 7. concurrency: two workers, one event
line_inbox.accept(ev(6))
res = []
ts = [threading.Thread(target=lambda: res.append(line_inbox.run("E6", ev(6), fake_processor))) for _ in range(6)]
[t.start() for t in ts]; [t.join() for t in ts]
check("only one worker processes a given event", sum(1 for x in res if x) == 1 and seen.count("E6") == 1, f"{res} {seen}")

# 8. processor exception recorded, not retried forever
def boom(e):
    raise RuntimeError("x")
line_inbox.accept(ev(7))
line_inbox.run("E7", ev(7), boom)
check("failing processor marks failed", status("E7")[0] == "failed")
setrow("E7", received_at=time.time() - 60)
check("failed event is not auto-retried", line_inbox.recover(fake_processor) == 0)

# 9. multi-event body + fallback when inbox broken
r = post([ev(10), ev(11)])
check("multi-event body processed", wait(lambda: "E10" in seen and "E11" in seen))
orig = line_inbox.accept
line_inbox.accept = lambda e: (_ for _ in ()).throw(RuntimeError("db down"))
post([ev(12)])
check("webhook still processes when inbox DB fails", wait(lambda: "E12" in seen))
line_inbox.accept = orig
check("stats reports counts", isinstance(line_inbox.stats(), dict) and line_inbox.stats().get("done", 0) >= 3)
print("")
print("ALL PASSED" if not FAILS else f"FAILED: {FAILS}")
sys.exit(1 if FAILS else 0)
