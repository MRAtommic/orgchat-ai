# -*- coding: utf-8 -*-
"""Regression: TZ=Asia/Bangkok set inside the process (as .env loading does) made Python on Windows think it was UTC,
so every datetime.now() in the server was 7 hours behind (attendance times, late detection, reminders)."""
import subprocess
import sys
from pathlib import Path

import pytest

WEBAI = Path(__file__).resolve().parent.parent

CODE = r'''
import os, sys, datetime
sys.path.insert(0, os.getcwd())
os.environ["TZ"] = "Asia/Bangkok"          # exactly what load_dotenv(.env) does, before any clock read
import tz_fix
tz_fix.apply()
now = datetime.datetime.now()
expected = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(hours=7)
print("DIFF_MIN", abs((now - expected).total_seconds()) / 60)
'''


@pytest.mark.skipif(sys.platform != "win32", reason="the C-runtime time-zone quirk only exists on Windows")
def test_bangkok_tz_is_applied_not_utc():
    p = subprocess.run([sys.executable, "-c", CODE], cwd=str(WEBAI), capture_output=True, text=True, timeout=60)
    line = next((l for l in p.stdout.splitlines() if l.startswith("DIFF_MIN")), None)
    assert line, p.stdout + p.stderr
    assert float(line.split()[1]) < 2, f"clock is off by {line}"
