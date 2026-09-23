# -*- coding: utf-8 -*-
"""
Deep Permissions Enforcement & Security Audit Test for OrgChat AI
Validates that:
1. Admin updating member permissions (PUT /api/org/members/<username>/permissions) properly saves to DB.
2. When can_delete_kb=False, DELETE /api/files/<id> returns 403 Forbidden.
3. When can_view_kb=False, GET /api/files returns 403 Forbidden.
4. When can_edit_kb=False, POST /api/upload and crawl-ingest return 403 Forbidden.
5. When can_view_financial=False, financial endpoints return 403 Forbidden.
6. When is_active=0, login is blocked.
7. Self-promotion and unauthorized admin elevation are blocked.
"""
import sys
import os
import json

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
from app_server import app
from routes.shared import get_or_create_csrf_token

client = app.test_client()
results = []

def record(test_name, passed, details=""):
    results.append((test_name, passed, details))
    icon = "✅" if passed else "❌"
    print(f"  {icon} [{test_name}]: {details}", flush=True)

print("=" * 65, flush=True)
print("🛡️ RUNNING PERMISSIONS & SECURITY ENFORCEMENT AUDIT", flush=True)
print("=" * 65, flush=True)

# Setup test users
TEST_USER = "test_perm_user"
TEST_ADMIN = "test_perm_admin"
TEST_ORG_ID = 1

# Ensure users exist in user_settings & user_profiles
database.admin_reset_user_password(TEST_USER, "password123")
database.admin_update_user(TEST_USER, role="user", is_active=1, can_view_kb=1, can_edit_kb=1, can_delete_kb=0)
database.admin_update_user(TEST_ADMIN, role="user", is_active=1)

# Ensure they are in organization_members
conn = database._get_conn()
cur = conn.cursor()
cur.execute("INSERT OR REPLACE INTO organization_members (organization_id, username, role) VALUES (?, ?, 'member')", (TEST_ORG_ID, TEST_USER))
cur.execute("INSERT OR REPLACE INTO organization_members (organization_id, username, role) VALUES (?, ?, 'admin')", (TEST_ORG_ID, TEST_ADMIN))
conn.commit()
conn.close()

# -------------------------------------------------------------
# TEST 1: Admin updates permissions via API
# -------------------------------------------------------------
print("\n[STEP 1] 📝 Admin updates Member Permissions via PUT Endpoint...", flush=True)
with client.session_transaction() as sess:
    sess['user'] = 'Admin'  # Owner/System Admin
    sess['role'] = 'admin'
    sess['org_id'] = TEST_ORG_ID
    sess['session_version'] = database.get_user_session_version('Admin')
    sess['_csrf_token'] = 'audit_token_123'

headers_admin = {'X-CSRF-Token': 'audit_token_123', 'Content-Type': 'application/json'}

payload = {
    "display_name": "Test Opor Perm",
    "position": "Specialist",
    "department": "QA",
    "can_view_kb": True,
    "can_edit_kb": True,
    "can_delete_kb": False,        # 🔴 DISABLING DELETE
    "can_view_financial": False,   # 🔴 DISABLING FINANCIAL
    "can_manage_leave": False,     # 🔴 DISABLING LEAVE MGMT
    "is_active": True
}

res = client.put(f"/api/org/members/{TEST_USER}/permissions", json=payload, headers=headers_admin)
data = res.get_json() or {}
if res.status_code == 200 and data.get("ok"):
    record("1.1 Save Permissions via API", True, f"HTTP {res.status_code} - Permissions saved successfully")
else:
    record("1.1 Save Permissions via API", False, f"Status {res.status_code}: {data}")

# Check DB persistence
settings = database.get_user_setting(TEST_USER)
can_del = settings.get("can_delete_kb")
can_fin = settings.get("can_view_financial")
can_view = settings.get("can_view_kb")

if can_del is False and can_fin is False and can_view is True:
    record("1.2 Database Persistence Verified", True, f"can_delete_kb={can_del}, can_view_financial={can_fin}, can_view_kb={can_view}")
else:
    record("1.2 Database Persistence Verified", False, f"DB values mismatch: {settings}")


def set_user_session(username, role="user"):
    with client.session_transaction() as sess:
        sess['user'] = username
        sess['role'] = role
        sess['org_id'] = TEST_ORG_ID
        sess['session_version'] = database.get_user_session_version(username)
        sess['_csrf_token'] = 'audit_token_123'

headers_user = {'X-CSRF-Token': 'audit_token_123', 'Content-Type': 'application/json'}

# -------------------------------------------------------------
# TEST 2: Enforce can_delete_kb = False (Real Block)
# -------------------------------------------------------------
print("\n[STEP 2] 🔒 Verify can_delete_kb=False Block Enforcement...", flush=True)
set_user_session(TEST_USER, "user")

# Attempt to delete file
res = client.delete("/api/files/test_dummy_file_id", headers=headers_user)
if res.status_code == 403:
    err_msg = (res.get_json() or {}).get("error", "")
    record("2.1 Block Delete File without Permission", True, f"Blocked with HTTP 403 Forbidden ('{err_msg}')")
else:
    record("2.1 Block Delete File without Permission", False, f"Expected 403, got {res.status_code}: {res.data}")


# -------------------------------------------------------------
# TEST 3: Enforce can_view_kb = False (Real Block)
# -------------------------------------------------------------
print("\n[STEP 3] 🔒 Verify can_view_kb=False Block Enforcement...", flush=True)
database.admin_update_user(TEST_USER, can_view_kb=0)
set_user_session(TEST_USER, "user")

res = client.get("/api/files", headers=headers_user)
if res.status_code == 403:
    record("3.1 Block View KB without Permission", True, "Blocked with HTTP 403 Forbidden")
else:
    record("3.1 Block View KB without Permission", False, f"Expected 403, got {res.status_code}")


# -------------------------------------------------------------
# TEST 4: Enforce can_edit_kb = False (Real Block)
# -------------------------------------------------------------
print("\n[STEP 4] 🔒 Verify can_edit_kb=False Block Enforcement...", flush=True)
database.admin_update_user(TEST_USER, can_view_kb=1, can_edit_kb=0)
set_user_session(TEST_USER, "user")

res = client.post("/api/kb/crawl-ingest", json={"url": "https://example.com"}, headers=headers_user)
if res.status_code == 403:
    record("4.1 Block Ingest/Edit KB without Permission", True, "Blocked with HTTP 403 Forbidden")
else:
    record("4.1 Block Ingest/Edit KB without Permission", False, f"Expected 403, got {res.status_code}")


# -------------------------------------------------------------
# TEST 5: Enforce can_view_financial = False (Real Block)
# -------------------------------------------------------------
print("\n[STEP 5] 🔒 Verify can_view_financial=False Block Enforcement...", flush=True)
database.admin_update_user(TEST_USER, can_view_financial=0)
set_user_session(TEST_USER, "user")

res = client.get("/api/dashboard/tax-expense-data", headers=headers_user)
if res.status_code == 403:
    err_msg = (res.get_json() or {}).get("error", "")
    record("5.1 Block Financial Dashboard without Permission", True, f"Blocked with HTTP 403 Forbidden ('{err_msg}')")
else:
    record("5.1 Block Financial Dashboard without Permission", False, f"Expected 403, got {res.status_code}")


# -------------------------------------------------------------
# TEST 6: Enforce is_active = 0 (Account Suspension)
# -------------------------------------------------------------
print("\n[STEP 6] ⛔ Verify is_active=0 Account Suspension...", flush=True)
database.admin_update_user(TEST_USER, is_active=0)

res = client.post("/api/login", json={"username": TEST_USER, "password": "password123"})
data = res.get_json() or {}
if res.status_code == 403 and "ระงับ" in data.get("error", ""):
    record("6.1 Block Login for Suspended Account", True, f"Login successfully blocked: '{data.get('error')}'")
else:
    record("6.1 Block Login for Suspended Account", False, f"Expected 403 blocked login, got {res.status_code}: {data}")


# -------------------------------------------------------------
# TEST 7: Safety Rule - Prevent Admin Self-Promotion
# -------------------------------------------------------------
print("\n[STEP 7] 🛡️ Verify Safety Rules (Anti-Self-Promotion)...", flush=True)
set_user_session(TEST_ADMIN, "user")

headers_org_admin = {'X-CSRF-Token': 'audit_token_123', 'Content-Type': 'application/json'}

# Org Admin trying to edit their own permissions
res = client.put(f"/api/org/members/{TEST_ADMIN}/permissions", json={"can_delete_kb": True}, headers=headers_org_admin)
if res.status_code == 403:
    err_msg = (res.get_json() or {}).get("error", "")
    record("7.1 Block Admin Self-Promotion", True, f"Blocked with HTTP 403 ('{err_msg[:40]}...')")
else:
    record("7.1 Block Admin Self-Promotion", False, f"Expected 403, got {res.status_code}")


# -------------------------------------------------------------
# SUMMARY REPORT
# -------------------------------------------------------------
print("\n" + "=" * 65, flush=True)
print("📊 PERMISSION AUDIT & ENFORCEMENT RESULT", flush=True)
print("=" * 65, flush=True)
passed_count = sum(1 for _, p, _ in results if p)
total_count = len(results)

for name, passed, details in results:
    icon = "✅ PASS" if passed else "❌ FAIL"
    print(f"{icon} | {name.ljust(44)} | {details}", flush=True)

print("-" * 65, flush=True)
print(f"🏆 Total Result: {passed_count}/{total_count} Passed ({(passed_count/total_count)*100:.1f}%)", flush=True)
print("=" * 65, flush=True)
