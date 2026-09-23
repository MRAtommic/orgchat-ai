# -*- coding: utf-8 -*-
"""
Deep Endpoint & Route Alignment Audit for OrgChat AI
Extracts every API endpoint URL called by frontend JS (apiFetch, fetch, window.open, axios)
and validates that a corresponding Flask route handler exists in app.url_map.
"""
import sys
import os
import re

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app_server import app

print("=" * 65, flush=True)
print("🌐 FRONTEND-BACKEND API ROUTE ALIGNMENT AUDIT", flush=True)
print("=" * 65, flush=True)

# 1. Collect all registered Flask routes
flask_rules = []
for rule in app.url_map.iter_rules():
    flask_rules.append({
        "rule": str(rule),
        "endpoint": rule.endpoint,
        "methods": list(rule.methods)
    })

print(f"📡 Total Registered Flask Backend Routes: {len(flask_rules)}", flush=True)

# Convert Flask rules to regex patterns for matching
# e.g. `/api/org/members/<username>/permissions` -> `^/api/org/members/[^/]+/permissions$`
route_patterns = []
for r in flask_rules:
    raw_rule = r["rule"]
    pattern = re.sub(r"<[^>]+>", r"[^/]+", raw_rule)
    route_patterns.append((re.compile(f"^{pattern}$"), r))

# 2. Collect all API endpoints called in JS files
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_JS_DIR = os.path.join(ROOT_DIR, "static", "js")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

js_endpoints = set()

# Scan JS and HTML files
for scan_dir in [STATIC_JS_DIR, TEMPLATES_DIR]:
    for fn in os.listdir(scan_dir):
        if fn.endswith(".js") or fn.endswith(".html"):
            p = os.path.join(scan_dir, fn)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Matches `/api/...` string literals or template literals
                # e.g. `/api/org/members/${username}/permissions` -> `/api/org/members/<dynamic>/permissions`
                found = re.findall(r"['\"`](/(?:api|line|auth|social|admin|superadmin)/[a-zA-Z0-9_\-/${}?&=.%]+)['\"`]", content)
                for ep in found:
                    # Strip query string
                    clean_ep = ep.split("?")[0]
                    # Replace JS template expressions ${...} with a wildcard token
                    norm_ep = re.sub(r"\$\{[^}]+\}", "PARAM", clean_ep)
                    # Skip noise or static asset paths
                    if not norm_ep.endswith((".js", ".css", ".png", ".jpg", ".svg", ".ico")):
                        js_endpoints.add((norm_ep, fn))

print(f"🔍 Total Unique Frontend API Calls Discovered: {len(js_endpoints)}", flush=True)

# 3. Match each frontend endpoint against backend Flask routes
unmatched_endpoints = []
matched_count = 0

for ep, filename in sorted(js_endpoints):
    # Test path: replace PARAM with '123' or 'test_param'
    test_path = ep.replace("PARAM", "test_item")
    
    # Check if matches any registered route
    matched = False
    for pattern, route_info in route_patterns:
        if pattern.match(test_path):
            matched = True
            matched_count += 1
            break
            
    if not matched:
        unmatched_endpoints.append((ep, filename))

print("\n" + "=" * 65, flush=True)
print("📊 API ROUTE VERIFICATION RESULT", flush=True)
print("=" * 65, flush=True)

if not unmatched_endpoints:
    print(f"✨ 100% of frontend API calls ({matched_count}/{len(js_endpoints)}) match live backend routes perfectly!", flush=True)
else:
    print(f"⚠️ {len(unmatched_endpoints)} API endpoints called in JS had no direct match:\n", flush=True)
    for ep, fn in unmatched_endpoints:
        print(f"  • {ep.ljust(45)} (in {fn})")

print("=" * 65, flush=True)
