# -*- coding: utf-8 -*-
"""OrgChat AI — Isolated Per-File Test Runner (T1)

Runs pytest on each test file in a separate Python process to prevent OpenBLAS / numpy / torch
memory allocation failures on memory-constrained systems.

Usage:
    python tools/run_tests.py                     # Run all 34 test files
    python tools/run_tests.py auth                # Run only matching tests (e.g. test_auth.py, test_u0_auth_flow.py)
    python tools/run_tests.py --fail-fast         # Stop immediately upon first failure
    python tools/run_tests.py --timeout 90        # Timeout per file in seconds (default 60)
"""

import argparse
import glob
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def get_test_files(test_dir: Path, filter_pattern: str | None = None) -> list[Path]:
    files = sorted(test_dir.glob("test_*.py"))
    if filter_pattern:
        pat = filter_pattern.lower()
        files = [f for f in files if pat in f.name.lower() or pat in str(f).lower()]
    return files


def run_single_test_file(
    py_exec: str,
    test_path: Path,
    timeout_sec: int = 60
) -> tuple[int, str, float, str]:
    """Runs a single test file in an isolated subprocess.
    Returns: (exit_code, summary_line, elapsed_seconds, full_output)
    """
    env = dict(os.environ)
    env["VECTOR_BACKEND"] = "python"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    # Never leak sensitive environment from real .env during tests
    for k in ("GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "REDIS_URL", "STRIPE_SECRET_KEY"):
        env.pop(k, None)

    cmd = [
        py_exec,
        "-m",
        "pytest",
        "-q",
        "-p",
        "no:cacheprovider",
        "--disable-warnings",
        str(test_path)
    ]

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=timeout_sec
        )
        elapsed = time.time() - t0
        output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        exit_code = proc.returncode
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return 124, f"TIMEOUT after {timeout_sec}s", elapsed, f"Command timed out after {timeout_sec}s"
    except Exception as e:
        elapsed = time.time() - t0
        return 1, f"ERROR: {e}", elapsed, str(e)

    # Extract pytest summary line (e.g. "3 passed, 1 skipped in 1.23s" or "no tests ran")
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    summary = "completed"
    for ln in reversed(lines):
        if any(term in ln for term in ("passed", "failed", "error", "skipped", "no tests ran")):
            summary = ln
            break

    return exit_code, summary, elapsed, output


def main():
    parser = argparse.ArgumentParser(description="OrgChat AI Isolated Test Runner")
    parser.add_argument("filter", nargs="?", default=None, help="Filter pattern for test file name")
    parser.add_argument("-x", "--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("-t", "--timeout", type=int, default=60, help="Timeout in seconds per file (default: 60)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print full output of failing tests")
    args = parser.parse_args()

    # Determine base directories
    script_dir = Path(__file__).resolve().parent
    webai_dir = script_dir.parent
    tests_dir = webai_dir / "tests"

    if not tests_dir.is_dir():
        print(f"[ERROR] Tests directory not found: {tests_dir}")
        sys.exit(1)

    os.chdir(webai_dir)
    test_files = get_test_files(tests_dir, args.filter)

    if not test_files:
        print(f"[!] No test files found matching pattern: {args.filter or '*'}")
        sys.exit(0)

    total_files = len(test_files)
    print(f"\n========================================================")
    print(f"🚀 OrgChat AI Test Runner (Isolated Subprocess Mode)")
    print(f"📂 Found {total_files} test file(s) in {tests_dir.name}/")
    print(f"⏱️  Timeout: {args.timeout}s per file | Fail-fast: {args.fail_fast}")
    print(f"========================================================\n")

    results = []
    failed_reports = []
    overall_start = time.time()

    for idx, f in enumerate(test_files, start=1):
        rel_name = f.relative_to(webai_dir).as_posix()
        prefix = f"[{idx:2d}/{total_files:2d}] {rel_name:<36}"
        print(prefix, end=" ... ", flush=True)

        code, summary, elapsed, full_out = run_single_test_file(
            sys.executable,
            f,
            timeout_sec=args.timeout
        )

        # Simplify summary line for clean console reporting
        # e.g. "3 passed, 1 warning in 0.76s" -> "3 passed"
        clean_sum = re.sub(r",\s*\d+\s*warning[s]?", "", summary)
        clean_sum = re.sub(r"in\s+[0-9\.]+s", "", clean_sum).strip()
        clean_sum = re.sub(r"=+", "", clean_sum).strip()

        if code == 0:
            status_icon = "✅ PASS"
            results.append((rel_name, True, elapsed, clean_sum))
            print(f"{status_icon} ({elapsed:4.1f}s) {clean_sum}")
        elif code == 5:
            # Pytest code 5 = no tests collected
            status_icon = "⚠️ EMPTY"
            results.append((rel_name, True, elapsed, "no tests collected"))
            print(f"{status_icon} ({elapsed:4.1f}s) no tests collected")
        else:
            status_icon = "❌ FAIL"
            results.append((rel_name, False, elapsed, clean_sum))
            print(f"{status_icon} ({elapsed:4.1f}s) {clean_sum}")
            failed_reports.append((rel_name, full_out))
            if args.fail_fast:
                print("\n[!] Stopping early due to --fail-fast flag.")
                break

    total_time = time.time() - overall_start
    passed_count = sum(1 for _, ok, _, _ in results if ok)
    failed_count = sum(1 for _, ok, _, _ in results if not ok)

    print(f"\n========================================================")
    print(f"📊 Summary: {passed_count}/{len(results)} files passed in {total_time:.1f}s")
    if failed_count > 0:
        print(f"❌ {failed_count} file(s) failed:")
        for name, ok, el, sm in results:
            if not ok:
                print(f"   • {name} ({el:.1f}s) -> {sm}")

        if args.verbose or failed_count <= 2:
            print("\n--- Failure Diagnostics ---")
            for name, out in failed_reports:
                print(f"\n[FAILED: {name}]")
                # Print last 25 lines of output
                out_lines = out.splitlines()
                diag_lines = out_lines[-25:] if len(out_lines) > 25 else out_lines
                print("\n".join(diag_lines))

        print(f"========================================================\n")
        sys.exit(1)
    else:
        print(f"🎉 ALL {passed_count} TEST FILES PASSED CLEANLY!")
        print(f"========================================================\n")
        sys.exit(0)


if __name__ == "__main__":
    main()

