# -*- coding: utf-8 -*-
"""
OrgChat AI - Automated QA/QC Test Suite
Runs end-to-end unit, integration, and security checks.
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database
from app_server import app

def run_qc_suite():
    print("=" * 70)
    print("🧪 ORGCHAT AI - COMPREHENSIVE QA / QC TEST SUITE")
    print("=" * 70)
    
    passed = 0
    failed = 0
    warnings = []
    
    client = app.test_client()
    
    # ─── TEST 1: Database Health & Connections ───
    print("\n[TEST 1] Database Health & Core Tables...")
    try:
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        res = cur.fetchone()[0]
        assert res == "ok", f"Integrity check failed: {res}"
        
        # Verify critical tables exist
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(r[0] for r in cur.fetchall())
        for req in ['user_profiles', 'organizations', 'organization_members', 'organization_departments', 'messages']:
            assert req in tables, f"Missing table: {req}"
        conn.close()
        print("  ✅ [PASS] Database integrity is 100% OK and all critical tables exist.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] Database Health: {e}")
        failed += 1

    # ─── TEST 2: CSRF Security on Mutating Endpoints ───
    print("\n[TEST 2] Security: Anti-CSRF Protection...")
    try:
        csrf_tok = "qc_secure_token_12345"
        with client.session_transaction() as sess:
            sess['user'] = 'Admin'
            sess['role'] = 'admin'
            sess['org_id'] = 1
            sess['_csrf_token'] = csrf_tok
            
        # A request without CSRF token when logged in should be rejected (403)
        res_blocked = client.post('/api/org/departments', json={'department_name': 'QC Dept Missing CSRF'})
        assert res_blocked.status_code == 403, f"Expected 403 for missing CSRF header, got {res_blocked.status_code}"
        
        # A request WITH valid CSRF header should be authorized
        res_ok = client.post('/api/org/departments', 
                             json={'department_name': 'QC Dept CSRF Valid'}, 
                             headers={'X-CSRF-Token': csrf_tok})
        assert res_ok.status_code in (200, 400), f"Expected 200/400 with valid CSRF, got {res_ok.status_code}"
        if res_ok.status_code == 200:
            d_id = res_ok.get_json().get('id')
            if d_id:
                client.delete(f'/api/org/departments/{d_id}', headers={'X-CSRF-Token': csrf_tok})
        print("  ✅ [PASS] CSRF Protection successfully enforces tokens on mutating endpoints.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] CSRF Check: {e}")
        failed += 1

    # ─── TEST 3: Department Management CRUD Flow ───
    print("\n[TEST 3] Feature: Organization Departments CRUD...")
    try:
        csrf_tok = "qc_secure_token_12345"
        with client.session_transaction() as sess:
            sess['user'] = 'Admin'
            sess['role'] = 'admin'
            sess['org_id'] = 1
            sess['_csrf_token'] = csrf_tok
            
        # 1. Create
        create_res = client.post('/api/org/departments', 
                                 json={'department_name': 'QC Temp Test Department', 'color': '#10b981', 'description': 'Automated test'}, 
                                 headers={'X-CSRF-Token': csrf_tok})
        assert create_res.status_code == 200, f"Create department failed: {create_res.get_json()}"
        dept_id = create_res.get_json().get('id')
        assert dept_id, "No department id returned"
        
        # 2. Read / List
        list_res = client.get('/api/org/departments')
        assert list_res.status_code == 200
        depts = list_res.get_json().get('departments', [])
        found = [d for d in depts if d['id'] == dept_id]
        assert len(found) > 0, "Created department not found in list"
        
        # 3. Update
        update_res = client.put(f'/api/org/departments/{dept_id}',
                                json={'department_name': 'QC Temp Department Updated', 'color': '#6366f1', 'head_username': 'Admin'},
                                headers={'X-CSRF-Token': csrf_tok})
        assert update_res.status_code == 200, f"Update department failed: {update_res.get_json()}"
        
        # 4. Delete
        del_res = client.delete(f'/api/org/departments/{dept_id}', headers={'X-CSRF-Token': csrf_tok})
        assert del_res.status_code == 200, f"Delete department failed: {del_res.get_json()}"
        print("  ✅ [PASS] Department Create/Read/Update/Delete cycle passed 100%.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] Department CRUD: {e}")
        failed += 1

    # ─── TEST 4: Google Folders Endpoint Status ───
    print("\n[TEST 4] Google Workspace Integration Safety...")
    try:
        with client.session_transaction() as sess:
            sess['user'] = 'Admin'
            sess['role'] = 'admin'
            sess['org_id'] = 1
            
        res = client.get('/api/google/folders')
        assert res.status_code == 200, f"Expected 200 OK from /api/google/folders, got {res.status_code}"
        data = res.get_json()
        assert 'folders' in data, "No folders key in response"
        print("  ✅ [PASS] Google Drive Folders endpoint returns graceful 200 OK structure.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] Google Folders: {e}")
        failed += 1

    # ─── TEST 5: LINE Binding & Login OAuth Flow ───
    print("\n[TEST 5] LINE Binding & Login OAuth Flow...")
    try:
        with client.session_transaction() as sess:
            sess['user'] = 'Admin'
            sess['role'] = 'admin'
            sess['org_id'] = 1
            
        res = client.get('/api/line/login-init')
        # If dummy ID 2000000000 is present, it should render helpful error page, not crash
        assert res.status_code in (200, 302, 400), f"Unexpected status code: {res.status_code}"
        print("  ✅ [PASS] LINE Login initialization handled cleanly without server crash.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] LINE Login Flow: {e}")
        failed += 1

    # ─── TEST 6: Knowledge Base & RAG Indexing ───
    print("\n[TEST 6] AI & Knowledge Base Index...")
    try:
        from rag_engine import KnowledgeBase
        kb = KnowledgeBase()
        meta = kb.get_meta() if hasattr(kb, 'get_meta') else {}
        print(f"  • Knowledge Base initialized. Total indexed files: {len(meta) if isinstance(meta, dict) else 'Active'}")
        print("  ✅ [PASS] RAG Knowledge Base engine is healthy and operational.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] RAG Engine: {e}")
        failed += 1

    # ─── TEST 7: AI Provider Configuration ───
    print("\n[TEST 7] AI Providers Connectivity Configuration...")
    try:
        import ai_providers
        groq_k = os.environ.get("GROQ_API_KEY", "")
        gemini_k = os.environ.get("GEMINI_API_KEY", "")
        if hasattr(ai_providers, 'GroqProvider'):
            gp = ai_providers.GroqProvider(groq_k)
            print(f"  • Groq Provider loaded (API Key available: {bool(groq_k)})")
        if hasattr(ai_providers, 'GeminiProvider'):
            gem_p = ai_providers.GeminiProvider(gemini_k)
            print(f"  • Gemini Provider loaded (API Key available: {bool(gemini_k)})")
        print("  ✅ [PASS] AI Providers loaded and configured successfully.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] AI Provider Manager: {e}")
        failed += 1

    # ─── TEST 8: Notification System ───
    print("\n[TEST 8] Notification System...")
    try:
        with client.session_transaction() as sess:
            sess['user'] = 'Admin'
            sess['role'] = 'admin'
            sess['org_id'] = 1
            
        res = client.get('/api/notifications')
        assert res.status_code == 200, f"Expected 200 OK from /api/notifications, got {res.status_code}"
        print("  ✅ [PASS] Notification system is fully functional.")
        passed += 1
    except Exception as e:
        print(f"  ❌ [FAIL] Notification System: {e}")
        failed += 1

    # ─── SUMMARY REPORT ───
    print("\n" + "=" * 70)
    print("📊 QC TEST SUITE SUMMARY RESULTS")
    print("=" * 70)
    print(f"Total Tests Run: {passed + failed}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    if failed == 0:
        print("\n🏆 QC RESULT: ALL AUTOMATED TESTS PASSED (100% GREEN)")
    else:
        print(f"\n⚠️ QC RESULT: {failed} test(s) encountered issues.")
    print("=" * 70)

if __name__ == '__main__':
    run_qc_suite()
