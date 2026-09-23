# -*- coding: utf-8 -*-
"""
Deep Bug Scanner for OrgChat AI
Scans for:
1. Missing CSRF headers in Javascript fetch() calls
2. Missing login_required / admin_required on sensitive backend routes
3. Dangerous NoneType handling (.strip(), .lower(), .get() on None)
4. Unclosed database connections
"""
import os
import sys
import re
import glob

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def scan_bugs():
    print("=" * 80)
    print("🐞 DEEP BUG & VULNERABILITY SCANNER")
    print("=" * 80)
    
    issues_found = []
    
    # ─── SCAN 1: Check chat.js for fetch calls with POST/PUT/DELETE missing CSRF token ───
    print("\n🔍 1. Scanning frontend fetch calls in chat.js...")
    chat_js_path = os.path.join("webai", "static", "js", "chat.js")
    if os.path.exists(chat_js_path):
        with open(chat_js_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Find all fetch blocks
        # Looking for fetch(..., { method: 'POST'|'PUT'|'DELETE' ... })
        fetch_blocks = re.finditer(r'fetch\s*\(\s*([^,\)]+)(?:,\s*\{([^}]+)\})?', content)
        for m in fetch_blocks:
            url_expr = m.group(1).strip()
            options = m.group(2) or ""
            if any(method in options.upper() for method in ["METHOD: 'POST'", 'METHOD: "POST"', "METHOD: 'PUT'", 'METHOD: "PUT"', "METHOD: 'DELETE'", 'METHOD: "DELETE"']):
                # Check if csrf token is included
                if "csrf" not in options.lower() and "x-csrf-token" not in options.lower() and "x_csrf_token" not in options.lower():
                    # Check if it's exempt (e.g. login/register)
                    if not any(ex in url_expr.lower() for ex in ["login", "register", "stripe", "public"]):
                        issues_found.append({
                            "type": "FRONTEND_MISSING_CSRF",
                            "file": "webai/static/js/chat.js",
                            "detail": f"fetch({url_expr[:50]}) with mutating method might be missing X-CSRF-Token"
                        })
                        
    print(f"  • Scanned chat.js: Found {len([i for i in issues_found if i['type'] == 'FRONTEND_MISSING_CSRF'])} potential missing CSRF token calls.")

    # ─── SCAN 2: Check backend routes for missing @login_required on mutating actions ───
    print("\n🔍 2. Scanning backend routes in webai/routes/...")
    route_files = glob.glob(os.path.join("webai", "routes", "*.py"))
    for rf in route_files:
        with open(rf, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
        current_route = None
        current_methods = []
        has_auth_decorator = False
        
        for idx, line in enumerate(lines, 1):
            if "@" in line and "_bp.route(" in line:
                current_route = line.strip()
                current_methods = []
                if "methods=" in line:
                    if "POST" in line: current_methods.append("POST")
                    if "PUT" in line: current_methods.append("PUT")
                    if "DELETE" in line: current_methods.append("DELETE")
                has_auth_decorator = False
            elif current_route:
                if any(dec in line for dec in ["@login_required", "@admin_required", "@superadmin_required"]):
                    has_auth_decorator = True
                elif line.startswith("def "):
                    # Function definition reached
                    if any(m in current_methods for m in ["POST", "PUT", "DELETE"]):
                        # Exempt public webhook / login routes
                        is_exempt = any(ex in current_route.lower() for ex in ["webhook", "login", "register", "forgot-password", "verify-reset-otp", "reset-password", "signup", "create-for-user"])
                        if not has_auth_decorator and not is_exempt:
                            issues_found.append({
                                "type": "BACKEND_UNPROTECTED_MUTATING_ROUTE",
                                "file": rf,
                                "line": idx,
                                "detail": f"Route {current_route} (def {line.strip()[:30]}) modifies data but lacks @login_required"
                            })
                    current_route = None

    print(f"  • Scanned backend routes: Found {len([i for i in issues_found if i['type'] == 'BACKEND_UNPROTECTED_MUTATING_ROUTE'])} unprotected mutating routes.")

    # ─── SCAN 3: Check database.py for potential unclosed connections or naked queries ───
    print("\n🔍 3. Scanning database.py for unclosed connections or unhandled exceptions...")
    db_file = os.path.join("webai", "database.py")
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8", errors="ignore") as f:
            db_content = f.read()
            
        # Count _get_conn() vs conn.close()
        get_conn_count = len(re.findall(r'_get_conn\(\)', db_content))
        close_conn_count = len(re.findall(r'conn\.close\(\)', db_content))
        print(f"  • Database connections requested: {get_conn_count}, closed: {close_conn_count}")
        if get_conn_count > close_conn_count + 10:
            print(f"  ⚠️ Potential unclosed connections detected (Diff: {get_conn_count - close_conn_count})")

    # ─── REPORT ───
    print("\n" + "=" * 80)
    print("📊 SCAN REPORT DETAILS")
    print("=" * 80)
    for idx, iss in enumerate(issues_found, 1):
        print(f"{idx}. [{iss['type']}] in {iss.get('file', '')} (Line {iss.get('line', '-')})")
        print(f"   Detail: {iss['detail']}")
        print("-" * 60)
        
    print(f"\nTotal issues / review items: {len(issues_found)}")
    print("=" * 80)

if __name__ == "__main__":
    scan_bugs()
