# -*- coding: utf-8 -*-
"""
run_all_tests_individually.py
Runs every single test_*.py in tests/ individually (one by one) to avoid OpenBLAS/memory issues,
and records the exact summary line and status for the complete audit report.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent
TESTS_DIR = WEBAI / "tests"

test_files = sorted([f.name for f in TESTS_DIR.glob("test_*.py")])

print(f"🚀 Found {len(test_files)} test files to execute individually...\n")

results = []
failures = []

for idx, tf in enumerate(test_files, 1):
    test_path = TESTS_DIR / tf
    cmd = [sys.executable, "-m", "pytest", str(test_path), "-q"]
    t0 = time.time()
    try:
        proc = subprocess.run(cmd, cwd=str(WEBAI), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        dur = round(time.time() - t0, 2)
        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        last_line = lines[-1] if lines else "No output"
        # Find summary line if last line is warning
        for l in reversed(lines):
            if "passed" in l or "failed" in l or "error" in l:
                last_line = l
                break
        status = "PASSED" if proc.returncode == 0 else "FAILED"
        print(f"[{idx:02d}/{len(test_files)}] {tf} -> {status} ({dur}s) | {last_line}")
        results.append((tf, status, dur, last_line))
        if proc.returncode != 0:
            failures.append((tf, out, err))
    except subprocess.TimeoutExpired:
        print(f"[{idx:02d}/{len(test_files)}] {tf} -> TIMEOUT (120s)")
        results.append((tf, "TIMEOUT", 120, "Timeout after 120s"))
        failures.append((tf, "Timeout", ""))
    except Exception as e:
        print(f"[{idx:02d}/{len(test_files)}] {tf} -> ERROR ({e})")
        results.append((tf, "ERROR", 0, str(e)))
        failures.append((tf, str(e), ""))

print(f"\n==========================================")
print(f"Total: {len(test_files)} | Passed: {len(results) - len(failures)} | Failed: {len(failures)}")
print(f"==========================================")

if failures:
    print("\nFailures Detail:")
    for tf, out, err in failures:
        print(f"\n--- {tf} ---")
        print(out[-1500:])
        if err:
            print("STDERR:", err[-500:])

