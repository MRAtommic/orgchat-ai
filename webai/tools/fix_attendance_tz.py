# -*- coding: utf-8 -*-
"""
tools/fix_attendance_tz.py — Safe Migration Script for Pre-fix Attendance Records
Defaults to --dry-run. Requires --apply to modify database.
Automatically backs up table to time_attendance_backup_<timestamp> before modifying.
"""
import sys
from pathlib import Path

# Reuse the robust migration logic from tools.migrate_attendance_tz
tools_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(tools_dir))
import migrate_attendance_tz

if __name__ == "__main__":
    migrate_attendance_tz.main()

