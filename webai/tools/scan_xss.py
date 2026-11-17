"""
Automated XSS Scanner for OrgChat AI templates and JavaScript files.
Scans:
1. templates/*.html for unsafe '| safe' filters on user data or unquoted/unjsoned variables in scripts.
2. static/js/*.js for unescaped innerHTML / insertAdjacentHTML string interpolations.
"""

import os
import re
import sys

WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scan_templates():
    """Scan Jinja templates in templates/ for potentially unsafe '| safe' usage."""
    tpl_dir = os.path.join(WEB_ROOT, 'templates')
    findings = []
    if not os.path.exists(tpl_dir):
        return findings

    # Suspicious user input properties passed to | safe
    suspicious_safe = re.compile(
        r'\{\{\s*([a-zA-Z0-9_.]*(?:title|content|text|name|desc|username|comment|message|bio|note|subject)[a-zA-Z0-9_.]*)\s*\|\s*safe\s*\}\}',
        re.I
    )

    for root, _, files in os.walk(tpl_dir):
        for f in files:
            if not f.endswith('.html'):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, WEB_ROOT)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                for line_no, line in enumerate(fp, 1):
                    # Exclude known sanitized fields or trusted layout blocks
                    if 'csrf_token' in line or 'svg' in line.lower() or 'icon' in line.lower():
                        continue
                    m = suspicious_safe.search(line)
                    if m:
                        findings.append({
                            'file': rel,
                            'line': line_no,
                            'matched': m.group(0),
                            'snippet': line.strip()[:100]
                        })
    return findings


def scan_javascript():
    """Scan static/js/*.js for innerHTML and insertAdjacentHTML with raw unescaped variables."""
    js_dir = os.path.join(WEB_ROOT, 'static', 'js')
    findings = []
    if not os.path.exists(js_dir):
        return findings

    # Detect innerHTML / insertAdjacentHTML assignments with template literals
    # We look for unescaped property access like ${u.name}, ${item.title}, ${s.desc}
    # where neither escHtml, escapeHtml, _safeUrl, _jsq, sanitize, Number() or encodeURIComponent wraps it.
    raw_var_pattern = re.compile(r'\$\{([a-zA-Z0-9_]+(?:\.[a-zA-Z0-9_]+)+)\}')

    safe_wrappers = ('escHtml', 'escapeHtml', '_safeUrl', '_jsq', 'sanitize', 'Number',
                     'encodeURIComponent', 'parseInt', 'parseFloat', 'JSON.stringify')

    # Ignored properties that are typically booleans, colors, CSS classes, timestamps, or system icons
    safe_props = {'id', 'length', 'count', 'size', 'icon', 'bg', 'color', 'border', 'class',
                  'status', 'type', 'created_at', 'updated_at', 'timestamp', 'date', 'role',
                  'width', 'height', 'top', 'left', 'key'}

    for root, _, files in os.walk(js_dir):
        for f in files:
            if not f.endswith('.js') or f.endswith('.min.js'):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, WEB_ROOT)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                content = fp.read()

            for line_no, line in enumerate(content.splitlines(), 1):
                # Only check lines involving HTML insertion or template literals
                if 'innerHTML' not in line and 'insertAdjacentHTML' not in line and '`' not in line:
                    continue
                matches = raw_var_pattern.findall(line)
                for var in matches:
                    prop = var.split('.')[-1].lower()
                    if prop in safe_props:
                        continue
                    # Check if line contains a safe wrapper for this variable
                    if any(w in line for w in safe_wrappers):
                        # Verify if this specific var is wrapped
                        wrapped = any(f'{w}({var}' in line or f'{w}({var})' in line for w in safe_wrappers)
                        if wrapped:
                            continue
                    findings.append({
                        'file': rel,
                        'line': line_no,
                        'variable': var,
                        'snippet': line.strip()[:100]
                    })
    return findings


if __name__ == '__main__':
    print("=== Scanning Templates for Unsafe Filters ===")
    t_findings = scan_templates()
    print(f"Found {len(t_findings)} potential template issues.")
    for f in t_findings[:10]:
        print(f"  {f['file']}:{f['line']} -> {f['matched']}")

    print("\n=== Scanning JavaScript for Unescaped innerHTML Variables ===")
    j_findings = scan_javascript()
    print(f"Found {len(j_findings)} potential JS template interpolation candidates.")
    for f in j_findings[:15]:
        print(f"  {f['file']}:{f['line']} -> ${{{f['variable']}}}")

