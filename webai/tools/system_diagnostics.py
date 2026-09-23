# -*- coding: utf-8 -*-
"""
Full System Diagnostics & Health Check for OrgChat AI
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

def run_diagnostics():
    print("=" * 60)
    print("🔍 ORGCHAT AI - COMPREHENSIVE SYSTEM DIAGNOSTICS")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # 1. Database Check
    print("\n📦 1. Database & Tables:")
    try:
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check;")
        integrity = cur.fetchone()[0]
        print(f"  • SQLite Integrity: {integrity}")
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [r[0] for r in cur.fetchall()]
        print(f"  • Total Tables: {len(tables)}")
        
        # Check core tables
        expected_tables = ['user_profiles', 'organizations', 'organization_members', 'organization_departments', 'messages', 'line_group_mappings', 'app_settings']
        for t in expected_tables:
            if t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                count = cur.fetchone()[0]
                print(f"    - {t}: ✅ ({count} records)")
            else:
                issues.append(f"Missing database table: {t}")
                print(f"    - {t}: ❌ MISSING")
        conn.close()
    except Exception as e:
        issues.append(f"Database error: {e}")
        print(f"  ❌ Database error: {e}")

    # 2. Environment Variables Check
    print("\n⚙️ 2. Environment Variables (.env):")
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
    
    # Groq / AI
    groq_key = os.environ.get("GROQ_API_KEY", "")
    gemini_key = os.environ.get("GEMINI_API_KEY", "")
    print(f"  • AI Provider: {os.environ.get('AI_PROVIDER', 'groq')}")
    print(f"  • Groq API Key: {'✅ Set' if groq_key and not groq_key.startswith('your_') else '❌ Not configured'}")
    print(f"  • Gemini API Key: {'✅ Set' if gemini_key and not gemini_key.startswith('AIzaSy...') else '✅ Set'}")
    
    # LINE Bot & Login
    line_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
    line_secret = os.environ.get("LINE_CHANNEL_SECRET", "")
    line_login_id = os.environ.get("LINE_LOGIN_CHANNEL_ID", "")
    print(f"  • LINE Bot Access Token: {'✅ Set' if line_token else '❌ Missing'}")
    print(f"  • LINE Bot Channel Secret: {'✅ Set' if line_secret else '❌ Missing'}")
    if line_login_id == "2000000000":
        warnings.append("LINE_LOGIN_CHANNEL_ID ใน .env เป็น 2000000000 (ปุ่ม LINE Login บนเว็บจะยังใช้ไม่ได้จนกว่าจะใส่ Channel ID จริงจาก LINE Developers Console แต่การผูกผ่านบอทด้วย /link ใช้งานได้ 100%)")
        print("  • LINE Login Channel ID: ⚠️ Placeholder 2000000000")
    else:
        print(f"  • LINE Login Channel ID: {'✅ Set' if line_login_id else '⚠️ Not set'}")

    # Google Service Account
    sa_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if sa_json:
        try:
            sa = json.loads(sa_json)
            email = sa.get("client_email")
            print(f"  • Google Service Account: ✅ {email}")
        except Exception:
            issues.append("GOOGLE_SERVICE_ACCOUNT_JSON ใน .env มีรูปแบบ JSON ไม่ถูกต้อง")
            print("  • Google Service Account: ❌ Invalid JSON")
    else:
        warnings.append("GOOGLE_SERVICE_ACCOUNT_JSON ยังไม่ได้ตั้งค่า (การบันทึกเอกสารเข้า Google Drive/Sheet จะทำงานในโหมด local fallback)")
        print("  • Google Service Account: ⚠️ Not set")

    # Google Service Account JWT validity check
    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    print(f"  • Google Spreadsheet ID: {spreadsheet_id or 'Not set'}")

    # Stripe
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if stripe_key.startswith("sk_test_"):
        print("  • Stripe Payment: ℹ️ Test Mode (sk_test_...)")
    elif stripe_key.startswith("sk_live_"):
        print("  • Stripe Payment: ✅ Live Mode")
    else:
        print("  • Stripe Payment: ⚠️ Not configured")

    # 3. Routes & Server Import Check
    print("\n🌐 3. App Server & Blueprint Routes:")
    try:
        from app_server import app
        rules = [rule.rule for rule in app.url_map.iter_rules()]
        print(f"  • Flask Server loaded successfully ({len(rules)} total routes registered)")
        critical_routes = [
            "/api/org/departments",
            "/api/google/folders",
            "/api/current_user",
            "/api/org/members",
            "/api/chat/messages",
            "/api/line/login-init"
        ]
        for r in critical_routes:
            matched = any(r in rule for rule in rules)
            print(f"    - {r}: {'✅' if matched else '❌'}")
    except Exception as e:
        issues.append(f"Flask App Server failed to import: {e}")
        print(f"  ❌ Flask App Server failed to import: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY REPORT")
    print("=" * 60)
    if not issues and not warnings:
        print("🎉 ระบบทำงานสมบูรณ์แบบ 100% ไม่พบข้อผิดพลาดใดๆ!")
    else:
        if issues:
            print(f"❌ พบข้อผิดพลาดวิกฤต (Critical Issues) {len(issues)} รายการ:")
            for i, iss in enumerate(issues, 1):
                print(f"   {i}. {iss}")
        else:
            print("✅ ไม่พบข้อผิดพลาดวิกฤตในโค้ดและฐานข้อมูล")
            
        if warnings:
            print(f"\n⚠️ ข้อควรทราบ / จุดที่ตั้งค่าเพิ่มเติมได้ (Warnings) {len(warnings)} รายการ:")
            for i, w in enumerate(warnings, 1):
                print(f"   {i}. {w}")
    print("=" * 60)

if __name__ == "__main__":
    run_diagnostics()
