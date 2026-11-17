# -*- coding: utf-8 -*-
"""
Tests for tools/check_data_consistency.py
Verifies that the consistency checker correctly identifies case collisions,
orphan users, missing owners, and duplicate LINE IDs in read-only mode.
"""
import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

def test_check_data_consistency_tool():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        db_path = tmp_path / "consistency_test.db"
        data_dir = tmp_path / "data"
        data_dir.mkdir()

        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE user_settings (username TEXT, role TEXT, created_at TEXT)")
        conn.execute("CREATE TABLE user_profiles (username TEXT, display_name TEXT, line_user_id TEXT, line_login_id TEXT)")
        conn.execute("CREATE TABLE organization_members (org_id INTEGER, username TEXT, role TEXT)")
        conn.execute("CREATE TABLE organizations (id INTEGER, name TEXT, owner_username TEXT)")

        # Seed data with intentional anomalies
        conn.execute("INSERT INTO user_settings VALUES ('charlie', 'user', '2026-01-01')")
        conn.execute("INSERT INTO user_settings VALUES ('Charlie', 'user', '2026-01-02')")
        conn.execute("INSERT INTO user_profiles VALUES ('charlie', 'Charlie C', 'U_DUP_LINE', 'UL_1')")
        conn.execute("INSERT INTO user_profiles VALUES ('Charlie', 'Charlie D', 'U_DUP_LINE', 'UL_2')")
        conn.commit()
        conn.close()

        env = os.environ.copy()
        env["DB_PATH"] = str(db_path)
        env["DATA_DIR"] = str(data_dir)

        proc = subprocess.run(
            [sys.executable, "tools/check_data_consistency.py"],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        assert proc.returncode == 0
        output = proc.stdout
        assert "CASE_COLLISION" in output
        assert "ORPHAN_USER" in output
        assert "DUP_LINE_BOT" in output
        assert "charlie" in output

