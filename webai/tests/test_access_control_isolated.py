# -*- coding: utf-8 -*-
"""Cross-tenant / permission regression scenarios (separate process, temp DB + temp DATA_DIR)."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent


def test_access_control_scenarios():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        for k in ("REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON"):
            env.pop(k, None)
        env["DB_PATH"] = str(Path(tmp) / "ac.db")
        env["DATA_DIR"] = str(Path(tmp) / "data")
        env["VECTOR_BACKEND"] = "python"
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run([sys.executable, str(WEBAI / "tests" / "isolated" / "access_control_scenarios.py")],
                              cwd=str(WEBAI), env=env, capture_output=True, text=True, encoding="utf-8", timeout=600)
        out = proc.stdout + proc.stderr
        assert proc.returncode == 0, "\n".join(l for l in out.splitlines() if l.startswith("FAIL"))[-3000:] or out[-3000:]
        assert "ALL PASSED" in proc.stdout
