# -*- coding: utf-8 -*-
"""Run Section 12 test files individually and print exact pytest summary lines."""
import os
import sys
import time
import subprocess
from pathlib import Path

files = [
    "tests/test_auth.py",
    "tests/test_u0_auth_flow.py",
    "tests/test_line_link_isolated.py",
    "tests/test_line_link_code_isolated.py",
    "tests/test_google_oauth_isolated.py",
    "tests/test_google_disconnect_isolated.py",
    "tests/test_line_file_search_isolated.py",
    "tests/test_kb_concurrent_ingest_isolated.py",
    "tests/test_citation_filter.py",
    "tests/test_line_plain_text.py",
    "tests/test_font_preferences.py",
    "tests/test_rag_followup.py",
    "tests/test_presence_isolated.py",
    "tests/test_calls_isolated.py",
    "tests/test_chat_send_isolated.py",
]

env = dict(os.environ)
env["VECTOR_BACKEND"] = "python"
env["PYTHONUNBUFFERED"] = "1"
env["PYTHONDONTWRITEBYTECODE"] = "1"
for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "REDIS_URL", "STRIPE_SECRET_KEY"):
    env.pop(k, None)

print("| ไฟล์ทดสอบ | เอาต์พุตสรุปจริงของ pytest | เวลา (วินาที) | สถานะ |")
print("|---|---|---|---|")

for f in files:
    t0 = time.time()
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--disable-warnings", f],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env
    )
    elapsed = round(time.time() - t0, 2)
    out_lines = [l.strip() for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    # Extract the summary line (usually the last or second to last line)
    summary = out_lines[-1] if out_lines else "NO OUTPUT"
    for l in reversed(out_lines):
        if "passed" in l or "failed" in l or "error" in l:
            summary = l
            break
    status = "✅ PASS" if proc.returncode == 0 else "❌ FAIL"
    print(f"| `{f}` | `{summary}` | {elapsed}s | {status} |")

