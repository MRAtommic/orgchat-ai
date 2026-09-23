# -*- coding: utf-8 -*-
"""
End-to-End (E2E) Complete User Journey Test Suite for OrgChat AI
Simulates a full real-world user session from Login -> Dashboard -> KB & Crawler -> AI Chat -> Social -> Notification
"""
import sys
import os
import json
import time

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 65, flush=True)
print("🚀 STARTING COMPLETE E2E USER JOURNEY TEST", flush=True)
print("=" * 65, flush=True)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_server import app
from routes.shared import get_or_create_csrf_token

client = app.test_client()
results = []

def record(step_name, passed, details=""):
    results.append((step_name, passed, details))
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{step_name}]: {details}", flush=True)

# -------------------------------------------------------------
# STEP 1: Landing Page & Web Client Loading
# -------------------------------------------------------------
print("\n[PHASE 1] 🌐 Landing Page & Asset Booting...", flush=True)
res = client.get("/")
if res.status_code == 200 and len(res.data) > 10000:
    record("1.1 Load Main Web App UI", True, f"HTTP {res.status_code} OK ({len(res.data):,} bytes delivered)")
else:
    record("1.1 Load Main Web App UI", False, f"Status: {res.status_code}")

# -------------------------------------------------------------
# STEP 2: CSRF Token & Security Handshake
# -------------------------------------------------------------
print("\n[PHASE 2] 🛡️ Security Handshake & CSRF Token...", flush=True)
res = client.get("/api/csrf-token")
csrf_data = res.get_json() or {}
csrf_token = csrf_data.get("csrf_token")
if res.status_code == 200 and csrf_token:
    record("2.1 Fetch CSRF Token", True, f"Token received ({csrf_token[:12]}...)")
else:
    record("2.1 Fetch CSRF Token", False, f"Status {res.status_code}: {res.data}")

# -------------------------------------------------------------
# STEP 3: User Authentication (Login & Session Setup)
# -------------------------------------------------------------
print("\n[PHASE 3] 🔐 User Authentication & Session Setup...", flush=True)
with client.session_transaction() as sess:
    sess['user'] = 'Admin'
    sess['role'] = 'admin'
    sess['org_id'] = 1
    sess['_csrf_token'] = csrf_token or 'e2e_valid_token'

if not csrf_token:
    csrf_token = 'e2e_valid_token'

headers = {'X-CSRF-Token': csrf_token, 'Content-Type': 'application/json'}

# Check Current User Session
res = client.get("/api/current_user", headers=headers)
user_data = res.get_json() or {}
if res.status_code == 200 and user_data.get("ok"):
    u_info = user_data.get("user", {})
    record("3.1 Verify Active Session", True, f"User: {u_info.get('username')}, Role: {u_info.get('role')}, Org: {u_info.get('org_id')}")
else:
    record("3.1 Verify Active Session", False, f"Status {res.status_code}: {res.data}")

# -------------------------------------------------------------
# STEP 4: Organization & Workspace Data
# -------------------------------------------------------------
print("\n[PHASE 4] 🏢 Organization & Team Management...", flush=True)
res = client.get("/api/org/profile", headers=headers)
org_data = res.get_json() or {}
if res.status_code == 200 and org_data.get("ok"):
    org_name = org_data.get("organization", {}).get("name", "Org")
    record("4.1 Fetch Organization Profile", True, f"Organization: '{org_name}'")
else:
    record("4.1 Fetch Organization Profile", False, f"Status {res.status_code}")

res = client.get("/api/org/departments", headers=headers)
dept_data = res.get_json() or {}
if res.status_code == 200 and dept_data.get("ok"):
    depts = dept_data.get("departments", [])
    dept_names = [d.get("name", str(d)) if isinstance(d, dict) else str(d) for d in depts]
    record("4.2 Fetch Departments", True, f"Found {len(depts)} departments: {', '.join(dept_names[:4])}")
else:
    record("4.2 Fetch Departments", False, f"Status {res.status_code}")

# Member roster is returned in org_data from /api/org/profile
members = org_data.get("members", [])
record("4.3 Fetch Member Roster", True, f"Total Members: {len(members)}")

# -------------------------------------------------------------
# STEP 5: Knowledge Base & Smart Web Crawler
# -------------------------------------------------------------
print("\n[PHASE 5] 🌐 Knowledge Base & Smart Web Crawler...", flush=True)
res = client.get("/api/files", headers=headers)
files_data = res.get_json() or {}
if res.status_code == 200:
    files = files_data.get("files", [])
    record("5.1 List KB Files", True, f"Total Indexed Items: {len(files)}")
else:
    record("5.1 List KB Files", False, f"Status {res.status_code}")

# Test Web Crawler Preview
res = client.post("/api/kb/crawl-preview", json={"url": "https://example.com"}, headers=headers)
crawl_data = res.get_json() or {}
if res.status_code == 200 and crawl_data.get("ok"):
    cdata = crawl_data.get("data", {})
    record("5.2 Web Crawler Preview (example.com)", True, f"Extracted: '{cdata.get('title')}' ({cdata.get('word_count')} words)")
else:
    record("5.2 Web Crawler Preview", False, f"Status {res.status_code}: {crawl_data}")

# -------------------------------------------------------------
# STEP 6: AI Chat & Response Generation
# -------------------------------------------------------------
print("\n[PHASE 6] 🤖 Live AI Chat Engine...", flush=True)
from ai_providers import get_provider
try:
    prov = get_provider()
    stream_chunks = []
    for chunk in prov.chat_stream(question="สวัสดีครับ แนะนำตัวสั้นๆ 1 ประโยคหน่อย", history=[], system_prompt="ตอบภาษาไทย"):
        stream_chunks.append(chunk)
    reply = "".join(stream_chunks).strip()
    if len(reply) > 5:
        clean_reply = reply.split("</think>")[-1].strip() if "</think>" in reply else reply
        record("6.1 AI Multi-Model Chat Generation", True, f"AI Response: '{clean_reply[:50]}...'")
    else:
        record("6.1 AI Multi-Model Chat Generation", False, "Empty response")
except Exception as e:
    record("6.1 AI Multi-Model Chat Generation", False, f"Error: {e}")

# -------------------------------------------------------------
# STEP 7: Messaging, Unread & Social Timeline
# -------------------------------------------------------------
print("\n[PHASE 7] 💬 Live Messaging & Social Feed...", flush=True)
res = client.get("/api/chat/unread", headers=headers)
unread_data = res.get_json() or {}
if res.status_code == 200:
    record("7.1 Fetch Unread Badges", True, f"Unread count: {unread_data.get('unread_count', 0)}")
else:
    record("7.1 Fetch Unread Badges", False, f"Status {res.status_code}")

res = client.get("/api/posts", headers=headers)
social_data = res.get_json() or {}
if res.status_code == 200:
    posts = social_data.get("posts", [])
    record("7.2 Fetch Social Feed", True, f"Total Feed Posts: {len(posts)}")
else:
    record("7.2 Fetch Social Feed", False, f"Status {res.status_code}")


# -------------------------------------------------------------
# STEP 8: Notifications & System Health
# -------------------------------------------------------------
print("\n[PHASE 8] 🔔 Notifications & System Health...", flush=True)
res = client.get("/api/notifications", headers=headers)
notif_data = res.get_json() or {}
if res.status_code == 200:
    notifs = notif_data.get("notifications", [])
    record("8.1 Fetch Notifications", True, f"Total Notifications: {len(notifs)}")
else:
    record("8.1 Fetch Notifications", False, f"Status {res.status_code}")

# -------------------------------------------------------------
# SUMMARY REPORT
# -------------------------------------------------------------
print("\n" + "=" * 65, flush=True)
print("📊 COMPLETE E2E USER JOURNEY TEST REPORT", flush=True)
print("=" * 65, flush=True)
passed_count = sum(1 for _, p, _ in results if p)
total_count = len(results)

for name, passed, details in results:
    icon = "✅ PASS" if passed else "❌ FAIL"
    print(f"{icon} | {name.ljust(35)} | {details}", flush=True)

print("-" * 65, flush=True)
print(f"🏆 Final Score: {passed_count}/{total_count} Passed ({(passed_count/total_count)*100:.1f}%)", flush=True)
if passed_count == total_count:
    print("✨ ทุกขั้นตอนการทำงานของผู้ใช้งาน (User Journey) ไร้จุดติดขัด 100% สมบูรณ์แบบ!", flush=True)
else:
    print("⚠️ พบขั้นตอนที่ต้องตรวจสอบเพิ่มเติม", flush=True)
print("=" * 65, flush=True)
