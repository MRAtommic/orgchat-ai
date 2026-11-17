# -*- coding: utf-8 -*-
"""
Audits getComputedStyle().display across 6 viewport widths (375, 390, 768, 1024, 1360, 1920)
using headless Chrome via Playwright against an isolated test server.
"""
import os
import sys
import time
import socket
import tempfile
import subprocess
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

WEBAI = Path(__file__).resolve().parent.parent

def get_free_port():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    p = s.getsockname()[1]
    s.close()
    return p

port = get_free_port()
tmp = tempfile.mkdtemp(prefix="qa_css_audit_")
db_p = Path(tmp) / "css_audit.db"
data_p = Path(tmp) / "data"

env = dict(os.environ)
env["DB_PATH"] = str(db_p)
env["DATA_DIR"] = str(data_p)
env["VECTOR_BACKEND"] = "python"
env["TEST_PORT"] = str(port)
env["SKIP_SYNC"] = "1"
env["RATELIMIT_ENABLED"] = "false"
for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "REDIS_URL", "STRIPE_SECRET_KEY"):
    env.pop(k, None)

# Initialize seed DB
subprocess.run([sys.executable, "-c", f"""
import sys
sys.path.insert(0, r"{WEBAI}")
import database
database.init_db()
database.admin_create_user("auditor", "Passw0rd!123", role="admin", email="audit@test.com", display_name="Auditor")
oid, _ = database.create_organization("Audit Corp", "auditor")
"""], cwd=str(WEBAI), env=env, check=True)

# Launch test server
log_p = Path(tmp) / "srv.log"
log_f = open(log_p, "w", encoding="utf-8")
srv = subprocess.Popen([sys.executable, "app_server.py"], cwd=str(WEBAI), env=env, stdout=log_f, stderr=subprocess.STDOUT)

base_url = f"http://127.0.0.1:{port}"
ready = False
for _ in range(40):
    time.sleep(0.5)
    try:
        with urllib.request.urlopen(f"{base_url}/login", timeout=1) as r:
            if r.status == 200:
                ready = True
                break
    except Exception:
        pass

if not ready:
    srv.kill()
    print("Failed to start server")
    sys.exit(1)

pw = sync_playwright().start()
browser = None
for ch in ["chrome", "msedge", None]:
    try:
        if ch:
            browser = pw.chromium.launch(channel=ch, headless=True)
        else:
            browser = pw.chromium.launch(headless=True)
        if browser:
            break
    except Exception:
        pass

if not browser:
    print("Failed to launch browser")
    srv.kill()
    pw.stop()
    sys.exit(1)

context = browser.new_context()
page = context.new_page()

# Login
page.goto(f"{base_url}/login")
page.fill("#loginUsername", "auditor")
page.fill("#loginPassword", "Passw0rd!123")
page.click("#loginBtn")
page.wait_for_url(f"{base_url}/", timeout=10000)
time.sleep(1)

viewports = [
    (375, 667, "Mobile (iPhone SE)"),
    (390, 844, "Mobile (iPhone 12/13/14)"),
    (768, 1024, "Tablet (iPad Mini)"),
    (1024, 768, "Tablet / Small Desktop"),
    (1360, 900, "Desktop HD"),
    (1920, 1080, "Desktop FHD")
]

# Elements to test:
# 1. Desktop sidebar/split panel in login/register
# 2. Header action buttons with `hidden sm:inline` or `hidden md:flex`
# 3. .view.hidden vs active view
test_queries = [
    ("[class~='hidden'][class*='sm:inline']", "Span label with 'hidden sm:inline'"),
    ("[class~='hidden'][class*='md:flex']", "Element with 'hidden md:flex'"),
    ("[class~='hidden'][class*='lg:flex']", "Element with 'hidden lg:flex'"),
    ("#navSidebar", "Navigation Sidebar (#navSidebar)"),
    (".view.hidden", "Inactive SPA View (.view.hidden)")
]

results = []

for w, h, label in viewports:
    page.set_viewport_size({"width": w, "height": h})
    time.sleep(0.3)
    
    for sel, desc in test_queries:
        ret = page.evaluate(f"""() => {{
            const el = document.querySelector("{sel}");
            if (!el) return {{display: "NOT_FOUND", info: ""}};
            return {{
                display: window.getComputedStyle(el).display,
                info: `${{el.tagName}}#${{el.id}} (${{el.className.substring(0, 30)}})`
            }};
        }}""")
        disp = ret["display"]
        if w == 375 and disp != "none" and "hidden" in desc:
            print(f"DEBUG LEAK on 375px: {desc} -> {ret['info']} has display='{disp}'")
        results.append((desc, w, label, disp))

print("\n### ตารางผลการตรวจสอบ Computed Display ของ Element บน 6 ขนาดหน้าจอจริง\n")
print("| Element / คำอธิบาย | ความกว้าง (px) | ประเภทอุปกรณ์ | getComputedStyle().display | สถานะ |")
print("|---|---|---|---|---|")

for desc, w, label, disp in results:
    if "hidden md:flex" in desc:
        ok = (disp == "none") if w < 768 else (disp in ("flex", "inline-flex", "block"))
    elif "hidden sm:inline" in desc or "ส่งออก CSV" in desc:
        ok = (disp == "none") if w < 640 else (disp in ("inline", "inline-block", "block"))
    elif "hidden lg:flex" in desc:
        ok = (disp == "none") if w < 1024 else (disp in ("flex", "inline-flex", "block"))
    elif ".view.hidden" in desc:
        ok = (disp == "none")
    else:
        ok = (disp != "NOT_FOUND")
    
    st = "✅ ถูกต้อง" if ok else "❌ ผิดพลาด"
    print(f"| {desc} | {w}px | {label} | `{disp}` | {st} |")

browser.close()
pw.stop()
srv.terminate()
srv.wait()

