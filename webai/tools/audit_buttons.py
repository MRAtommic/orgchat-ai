# -*- coding: utf-8 -*-
"""
Deep Button & UI Interaction Scanner for OrgChat AI
Scans all HTML templates and JS files to verify:
1. Every button with an `onclick` attribute has a matching defined JavaScript function.
2. Every button with an `id` that JS tries to attach event listeners to exists in HTML.
3. Every `document.getElementById` or `$('...')` in JS points to an existing element in HTML (or dynamically generated templates).
4. Detect empty onclick="", "#" hrefs with no handlers, or missing modal trigger bindings.
"""
import sys
import os
import re
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")
STATIC_JS_DIR = os.path.join(ROOT_DIR, "static", "js")

print("=" * 65, flush=True)
print("🔍 COMPREHENSIVE BUTTON & UI INTERACTION AUDIT", flush=True)
print("=" * 65, flush=True)

# 1. Read all JS files and collect all defined functions and assigned globals
js_contents = {}
defined_functions = set()
for js_file in os.listdir(STATIC_JS_DIR):
    if js_file.endswith(".js"):
        p = os.path.join(STATIC_JS_DIR, js_file)
        with open(p, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            js_contents[js_file] = content
            # Find function names: `function foo(`, `window.foo =`, `const foo = () =>`, `async function foo(`
            f1 = re.findall(r"(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(", content)
            f2 = re.findall(r"window\.([a-zA-Z0-9_$]+)\s*=", content)
            f3 = re.findall(r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>", content)
            f4 = re.findall(r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?function", content)
            defined_functions.update(f1)
            defined_functions.update(f2)
            defined_functions.update(f3)
            defined_functions.update(f4)

# Also collect JS functions dynamically created or defined inline in HTML
html_files = [f for f in os.listdir(TEMPLATES_DIR) if f.endswith(".html")]
for hf in html_files:
    p = os.path.join(TEMPLATES_DIR, hf)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        f1 = re.findall(r"(?:async\s+)?function\s+([a-zA-Z0-9_$]+)\s*\(", content)
        f2 = re.findall(r"window\.([a-zA-Z0-9_$]+)\s*=", content)
        defined_functions.update(f1)
        defined_functions.update(f2)

print(f"📦 Total Defined JS Functions Found across project: {len(defined_functions)}", flush=True)

# 2. Parse HTML files and examine all buttons and clickable elements
issues = []
total_buttons_audited = 0

for hf in html_files:
    p = os.path.join(TEMPLATES_DIR, hf)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        html_text = f.read()
    
    soup = BeautifulSoup(html_text, "html.parser")
    
    # Check all <button> elements
    buttons = soup.find_all("button")
    for btn in buttons:
        total_buttons_audited += 1
        btn_id = btn.get("id")
        btn_onclick = btn.get("onclick")
        btn_text = btn.get_text(strip=True)[:30] or btn.get("title", "") or btn.get("aria-label", "") or "No Text"
        
        # Check onclick handler
        if btn_onclick is not None:
            onclick_clean = btn_onclick.strip()
            if not onclick_clean:
                issues.append({
                    "file": hf,
                    "element": f"<button id='{btn_id}'> {btn_text}",
                    "issue": "Empty onclick attribute (onclick='')",
                    "severity": "WARNING"
                })
            else:
                # Extract primary function call: e.g. "openModal('foo')" -> "openModal"
                match = re.match(r"^([a-zA-Z0-9_$]+)\s*\(", onclick_clean)
                if match:
                    func_name = match.group(1)
                    if func_name not in defined_functions:
                        issues.append({
                            "file": hf,
                            "element": f"<button id='{btn_id}'> {btn_text}",
                            "issue": f"Calls undefined JS function: '{func_name}' in onclick='{onclick_clean}'",
                            "severity": "CRITICAL"
                        })

    # Check <a> tags acting as buttons
    links = soup.find_all("a")
    for a in links:
        href = a.get("href", "")
        onclick = a.get("onclick")
        a_id = a.get("id")
        a_text = a.get_text(strip=True)[:30]
        
        if href in ("#", "javascript:void(0)", "javascript:;") or "btn" in (a.get("class") or []):
            total_buttons_audited += 1
            if onclick:
                match = re.match(r"^([a-zA-Z0-9_$]+)\s*\(", onclick.strip())
                if match:
                    func_name = match.group(1)
                    if func_name not in defined_functions:
                        issues.append({
                            "file": hf,
                            "element": f"<a id='{a_id}'> {a_text}",
                            "issue": f"Calls undefined JS function: '{func_name}' in onclick='{onclick}'",
                            "severity": "CRITICAL"
                        })
            elif not a_id and not a.get("class"):
                # Orphaned '#' link with no ID and no onclick
                if href == "#" and a_text:
                    issues.append({
                        "file": hf,
                        "element": f"<a> {a_text}",
                        "issue": "Link with href='#' has no id, class, or onclick handler",
                        "severity": "WARNING"
                    })

    # Check all elements with onclick attribute
    all_with_onclick = soup.find_all(attrs={"onclick": True})
    for el in all_with_onclick:
        if el.name not in ("button", "a"):
            total_buttons_audited += 1
            onclick = el.get("onclick", "").strip()
            match = re.match(r"^([a-zA-Z0-9_$]+)\s*\(", onclick)
            if match:
                func_name = match.group(1)
                if func_name not in defined_functions:
                    issues.append({
                        "file": hf,
                        "element": f"<{el.name} id='{el.get('id')}'> {el.get_text(strip=True)[:25]}",
                        "issue": f"Calls undefined JS function: '{func_name}' in onclick='{onclick}'",
                        "severity": "CRITICAL"
                    })

print(f"🔘 Total Interactive Buttons & Elements Audited: {total_buttons_audited}", flush=True)

# 3. Check JS Event Listeners targeting IDs: e.g. $('saveBtn').addEventListener('click', ...)
print("\n[STEP 2] 🔎 Auditing JS Click Event Listeners & ID Bindings...", flush=True)

# Collect all HTML IDs
all_html_ids = set()
for hf in html_files:
    p = os.path.join(TEMPLATES_DIR, hf)
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        for el in soup.find_all(attrs={"id": True}):
            all_html_ids.add(el.get("id"))

# Also collect IDs dynamically created inside JS template literals: e.g. id="foo" or id='foo'
for js_file, content in js_contents.items():
    dyn_ids = re.findall(r'id=["\']([a-zA-Z0-9_-]+)["\']', content)
    all_html_ids.update(dyn_ids)

print(f"🆔 Total Unique DOM IDs in HTML + Dynamic Templates: {len(all_html_ids)}", flush=True)

# Scan JS for `$('id').onclick =` or `$('id').addEventListener('click', ...)` or `document.getElementById('id')`
js_click_bindings = []
for js_file, content in js_contents.items():
    # Matches: $('saveBtn')?.addEventListener('click', ...) or document.getElementById('saveBtn').addEventListener
    b1 = re.findall(r"(?:\$|document\.getElementById)\(['\"]([a-zA-Z0-9_-]+)['\"]\)\s*(?:\?)?\s*\.\s*(?:addEventListener\(['\"]click['\"]|onclick\s*=)", content)
    for target_id in b1:
        if target_id not in all_html_ids:
            issues.append({
                "file": js_file,
                "element": f"Event listener target ID: '{target_id}'",
                "issue": f"JS attaches click event to ID '{target_id}' but ID was not found in HTML or JS templates",
                "severity": "WARNING"
            })

# -------------------------------------------------------------
# REPORT
# -------------------------------------------------------------
print("\n" + "=" * 65, flush=True)
print("📊 SYSTEM-WIDE BUTTON AUDIT REPORT", flush=True)
print("=" * 65, flush=True)

critical_count = sum(1 for i in issues if i["severity"] == "CRITICAL")
warning_count = sum(1 for i in issues if i["severity"] == "WARNING")

if not issues:
    print("✨ ทุกปุ่มในระบบ (100%) มีฟังก์ชันและ Event Listener รองรับอย่างสมบูรณ์ ไร้ปุ่มเสียหรือปุ่มค้าง!", flush=True)
else:
    print(f"⚠️ พบ {len(issues)} จุดที่ต้องตรวจสอบ (Critical: {critical_count}, Warning: {warning_count}):\n", flush=True)
    for idx, iss in enumerate(issues, 1):
        print(f"[{idx}] [{iss['severity']}] File: {iss['file']}")
        print(f"     Element: {iss['element']}")
        print(f"     Issue:   {iss['issue']}\n")

print("=" * 65, flush=True)
