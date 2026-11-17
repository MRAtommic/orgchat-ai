# -*- coding: utf-8 -*-
"""
scan_all_class_methods.py
Scans the entire webai codebase using AST to find all calls on major services,
managers, singletons, and classes, comparing them against the actual definitions
to catch missing methods/attributes (like invalidate_org_cache, get_organization_by_id, etc.).
"""
import ast
import os
import sys
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WEBAI))

# Pre-import services and inspect attributes
services_to_check = {}

try:
    import database
    services_to_check['database'] = database
except Exception as e:
    print(f"Error importing database: {e}")

try:
    from google_drive_service import GoogleWorkspaceManager, google_manager
    services_to_check['google_manager'] = google_manager
    services_to_check['GoogleWorkspaceManager'] = GoogleWorkspaceManager
except Exception as e:
    print(f"Error importing google_drive_service: {e}")

try:
    from oauth2_service import oauth2_service, GoogleOAuth2Service
    services_to_check['oauth2_service'] = oauth2_service
    services_to_check['GoogleOAuth2Service'] = GoogleOAuth2Service
except Exception as e:
    print(f"Error importing oauth2_service: {e}")

try:
    import rag_engine
    services_to_check['rag_engine'] = rag_engine
except Exception as e:
    print(f"Error importing rag_engine: {e}")

try:
    import settings_manager
    services_to_check['settings_manager'] = settings_manager
except Exception as e:
    print(f"Error importing settings_manager: {e}")

try:
    from db import org_security, org_features
    services_to_check['org_security'] = org_security
    services_to_check['org_features'] = org_features
except Exception as e:
    print(f"Error importing org_security/org_features: {e}")

try:
    import export_service
    services_to_check['export_service'] = export_service
except Exception as e:
    print(f"Error importing export_service: {e}")

try:
    import payment_voucher_service
    services_to_check['payment_voucher_service'] = payment_voucher_service
except Exception as e:
    print(f"Error importing payment_voucher_service: {e}")

try:
    import task_tracker
    services_to_check['task_tracker'] = task_tracker
except Exception as e:
    print(f"Error importing task_tracker: {e}")

try:
    import web_crawler
    services_to_check['web_crawler'] = web_crawler
except Exception as e:
    print(f"Error importing web_crawler: {e}")

try:
    import billing
    services_to_check['billing'] = billing
except Exception as e:
    print(f"Error importing billing: {e}")

more_modules = [
    "ai_providers", "chart_generator", "citation_filter", "line_approvals",
    "line_inbox", "line_rich_menu", "ocr_service", "payment", "peak_service",
    "reconciliation_service", "redis_manager", "secret_vault", "tts_engine",
    "webrtc_ice", "wiki_manager", "notification_db"
]

for mod_name in more_modules:
    try:
        mod = __import__(mod_name)
        services_to_check[mod_name] = mod
    except Exception as e:
        pass


def get_available_attrs(obj):
    attrs = set(dir(obj))
    if hasattr(obj, '__dict__'):
        attrs.update(obj.__dict__.keys())
    if isinstance(obj, type) and hasattr(obj, '__mro__'):
        for cls in obj.__mro__:
            attrs.update(cls.__dict__.keys())
    return attrs


available_cache = {name: get_available_attrs(obj) for name, obj in services_to_check.items()}

# AST Visitor to find object attribute calls
class CallScanner(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.missing = []

    def visit_Attribute(self, node):
        # Matches e.g. service.method or obj.attr
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            attr_name = node.attr
            if obj_name in services_to_check:
                if attr_name not in available_cache[obj_name] and not attr_name.startswith('_'):
                    self.missing.append((node.lineno, obj_name, attr_name))
        self.generic_visit(node)


def main():
    print(f"🔍 Scanning {WEBAI} for missing methods and attributes on {len(services_to_check)} services...")
    total_files = 0
    total_missing = []

    for root, dirs, files in os.walk(WEBAI):
        # Skip tests, venv, pycache
        if any(skip in root for skip in ['tests', '__pycache__', '.venv', 'venv', 'tools']):
            continue
        for f in files:
            if f.endswith('.py'):
                total_files += 1
                fp = os.path.join(root, f)
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        tree = ast.parse(fh.read(), filename=fp)
                    scanner = CallScanner(fp)
                    scanner.visit(tree)
                    for lineno, obj_name, attr in scanner.missing:
                        rel_path = os.path.relpath(fp, WEBAI)
                        total_missing.append((rel_path, lineno, obj_name, attr))
                except Exception as ex:
                    print(f"⚠️ Error parsing {fp}: {ex}")

    print(f"Scanned {total_files} files.")
    if not total_missing:
        print("✅ No missing methods or attributes found across all checked services!")
    else:
        print(f"❌ Found {len(total_missing)} missing attribute/method accesses:")
        for rel_path, lineno, obj_name, attr in total_missing:
            print(f"  {rel_path}:{lineno} -> {obj_name}.{attr} DOES NOT EXIST")

if __name__ == '__main__':
    main()
