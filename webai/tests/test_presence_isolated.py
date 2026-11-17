# -*- coding: utf-8 -*-
import os, subprocess, sys, tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent


def test_presence_scenarios():
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, DB_PATH=str(Path(tmp) / "pr.db"), DATA_DIR=str(Path(tmp) / "data"), VECTOR_BACKEND="python", PYTHONIOENCODING="utf-8")
        for k in ("REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON"):
            env.pop(k, None)
        proc = subprocess.run([sys.executable, str(WEBAI / "tests" / "isolated" / "presence_scenarios.py")], cwd=str(WEBAI), env=env,
                              capture_output=True, text=True, encoding="utf-8", timeout=600)
        out = proc.stdout + proc.stderr
        assert proc.returncode == 0, "\n".join(l for l in out.splitlines() if l.startswith("FAIL"))[-3000:] or out[-3000:]
        assert "ALL PASSED" in proc.stdout
