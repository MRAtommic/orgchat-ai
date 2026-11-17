# -*- coding: utf-8 -*-
"""
Automated XSS Regression Scanner for OrgChat AI templates and JavaScript files.
Ensures:
1. Jinja2 templates in templates/*.html do not use unsafe '| safe' on user data.
2. static/js/*.js files do not interpolate raw user fields into innerHTML / insertAdjacentHTML.
"""

import os
import re
import pytest

WEB_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_unsafe_jinja_safe_filters():
    """Verify that templates/*.html do not pass unescaped user-controlled text through '| safe'."""
    tpl_dir = os.path.join(WEB_ROOT, "templates")
    assert os.path.exists(tpl_dir), f"templates dir not found at {tpl_dir}"

    suspicious_safe = re.compile(
        r'\{\{\s*([a-zA-Z0-9_.]*(?:title|content|text|name|desc|username|comment|message|bio|note|subject)[a-zA-Z0-9_.]*)\s*\|\s*safe\s*\}\}',
        re.I
    )

    violations = []
    for root, _, files in os.walk(tpl_dir):
        for f in files:
            if not f.endswith(".html"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, WEB_ROOT)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                for line_no, line in enumerate(fp, 1):
                    # Skip known trusted token/icon blocks
                    if "csrf_token" in line or "svg" in line.lower() or "icon" in line.lower():
                        continue
                    m = suspicious_safe.search(line)
                    if m:
                        violations.append(f"{rel}:{line_no} Unsafe '| safe' on {m.group(1)}: {line.strip()[:80]}")

    assert not violations, "Found unsafe '| safe' filters in templates:\n" + "\n".join(violations)


def test_no_raw_user_interpolations_in_js_innerhtml():
    """Verify that critical user attributes are not injected raw into innerHTML / insertAdjacentHTML."""
    js_dir = os.path.join(WEB_ROOT, "static", "js")
    assert os.path.exists(js_dir), f"static/js dir not found at {js_dir}"

    # Dangerous patterns in innerHTML assignments:
    # e.g. innerHTML = `... ${alert.message} ...` or `${opt.text}` without escHtml
    high_risk_patterns = [
        re.compile(r'innerHTML\s*=\s*`[^`]*\$\{(?!escHtml|_safeUrl|_jsq|sanitize|Number|parseInt|JSON\.stringify)(?:alert\.(?:message|hint)|opt\.text|err\.message)[^`]*`'),
    ]

    violations = []
    for root, _, files in os.walk(js_dir):
        for f in files:
            if not f.endswith(".js") or f.endswith(".min.js"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, WEB_ROOT)
            with open(path, "r", encoding="utf-8", errors="ignore") as fp:
                content = fp.read()

            for line_no, line in enumerate(content.splitlines(), 1):
                for pat in high_risk_patterns:
                    if pat.search(line):
                        violations.append(f"{rel}:{line_no} Raw unescaped interpolation: {line.strip()[:100]}")

    assert not violations, "Found high-risk unescaped innerHTML interpolations:\n" + "\n".join(violations)

