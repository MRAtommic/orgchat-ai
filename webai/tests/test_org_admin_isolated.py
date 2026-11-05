# -*- coding: utf-8 -*-
"""Runs tests/isolated/org_admin_scenarios.py in a separate process with a temporary database,
so it can never write into webai/chat_history.db (unlike the older tests)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent


def test_org_admin_and_2fa_scenarios():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        for k in ("DB_PATH", "REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON"):
            env.pop(k, None)
        env["DB_PATH"] = str(Path(tmp) / "scenario.db")
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run(
            [sys.executable, str(WEBAI / "tests" / "isolated" / "org_admin_scenarios.py")],
            cwd=str(WEBAI), env=env, capture_output=True, text=True, encoding="utf-8", timeout=600,
        )
        out = proc.stdout + proc.stderr
        assert proc.returncode == 0, out[-3000:]
        assert "ALL PASSED" in proc.stdout
