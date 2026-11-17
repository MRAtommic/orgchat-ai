# -*- coding: utf-8 -*-
"""OrgChat AI — Scenario A: New User Journey Test Runner
Tests end-to-end user onboarding: Register -> Create Org -> Invite Member -> Upload 3 product documents -> RAG queries & citations.
Runs in an isolated subprocess with ephemeral temp DB and DATA_DIR.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

WEBAI = Path(__file__).resolve().parent.parent


def test_scenario_a_new_user_journey():
    with tempfile.TemporaryDirectory(prefix="scenario_a_") as tmp:
        env = dict(
            os.environ,
            DB_PATH=str(Path(tmp) / "scenario_a.db"),
            DATA_DIR=str(Path(tmp) / "data"),
            VECTOR_BACKEND="python",
            AI_EMBEDDING_PROVIDER="local",
            PYTHONIOENCODING="utf-8"
        )
        for k in ("REDIS_URL", "GOOGLE_SERVICE_ACCOUNT_JSON", "GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"):
            env.pop(k, None)

        proc = subprocess.run(
            [sys.executable, str(WEBAI / "tests" / "isolated" / "scenario_a_user_journey_scenarios.py")],
            cwd=str(WEBAI),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300
        )
        out = proc.stdout + proc.stderr
        assert proc.returncode == 0, "\n".join(l for l in out.splitlines() if l.startswith("FAIL"))[-3000:] or out[-3000:]
        assert "ALL PASSED" in proc.stdout

