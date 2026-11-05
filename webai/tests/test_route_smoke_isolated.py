# -*- coding: utf-8 -*-
"""Calls every argument-free GET route as an organization admin (separate process, temporary DB)
and fails if any of them answers 5xx. Catches 'no such column', bad return shapes, etc."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent


def test_no_get_route_crashes_for_org_admin():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        for k in ("REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON"):
            env.pop(k, None)
        env["DB_PATH"] = str(Path(tmp) / "smoke.db")
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(WEBAI / "tests" / "isolated" / "route_smoke.py")],
            cwd=str(WEBAI), env=env, capture_output=True, text=True, encoding="utf-8", timeout=900,
        )
        bad = [l for l in proc.stdout.splitlines() if l.startswith("BAD") or l.startswith("routes checked")]
        assert proc.returncode == 0, "\n".join(bad) or (proc.stdout + proc.stderr)[-3000:]
