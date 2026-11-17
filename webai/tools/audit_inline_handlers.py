# -*- coding: utf-8 -*-
"""OrgChat AI — Inline Event Handler Audit Script (S1)

Scans templates and scripts for inline HTML handlers (onclick, onchange, etc.)
to track CSP modernization progress towards eliminating 'unsafe-inline'.

Usage:
    python tools/audit_inline_handlers.py
"""

import re
from pathlib import Path

WEBAI_DIR = Path(__file__).resolve().parent.parent

INLINE_EVENT_RE = re.compile(
    r'\b(on(?:click|change|input|submit|focus|blur|keydown|keyup|keypress|load|error|scroll|mouseenter|mouseleave))\s*=\s*["\']',
    re.I
)


def audit():
    total = 0
    by_event = {}
    by_file = {}

    targets = list((WEBAI_DIR / "templates").glob("*.html")) + list((WEBAI_DIR / "static" / "js").glob("*.js"))

    for p in targets:
        text = p.read_text(encoding="utf-8", errors="ignore")
        matches = INLINE_EVENT_RE.findall(text)
        if matches:
            count = len(matches)
            total += count
            by_file[p.name] = count
            for m in matches:
                ev = m.lower()
                by_event[ev] = by_event.get(ev, 0) + 1

    print("=" * 60)
    print(f"🔒 CSP Inline Event Handler Audit (S1)")
    print(f"📊 Total inline handlers detected: {total}")
    print("\nTop files with inline handlers:")
    for f, c in sorted(by_file.items(), key=lambda x: -x[1])[:10]:
        print(f"  {f:<30} : {c} handlers")

    print("\nBreakdown by event type:")
    for ev, c in sorted(by_event.items(), key=lambda x: -x[1]):
        print(f"  {ev:<15} : {c}")
    print("=" * 60)
    return total


if __name__ == "__main__":
    audit()

