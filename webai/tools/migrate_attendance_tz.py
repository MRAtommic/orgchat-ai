# -*- coding: utf-8 -*-
"""OrgChat AI — Attendance Timezone Data Migration Script (F2)

Shifts time_attendance timestamps recorded before the Windows TZ fix (2026-11-06 14:22:00) by +7 hours.
Includes automatic safety backup, dry-run mode, and rollback support.

Usage:
    python tools/migrate_attendance_tz.py --dry-run
    python tools/migrate_attendance_tz.py --apply
"""

import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Fix cutoff: 2026-11-06 14:22:00 (when tz_fix.py was deployed)
CUTOFF_DATE = "2026-11-06"
CUTOFF_TIME = "14:22:00"


def shift_time_plus_7(time_str: str) -> str:
    """Adds 7 hours to HH:MM:SS or HH:MM format."""
    try:
        parts = time_str.strip().split(":")
        hh = int(parts[0])
        mm = int(parts[1]) if len(parts) > 1 else 0
        ss = int(parts[2]) if len(parts) > 2 else 0
        total_seconds = (hh * 3600 + mm * 60 + ss + 7 * 3600) % 86400
        new_hh = total_seconds // 3600
        new_mm = (total_seconds % 3600) // 60
        new_ss = total_seconds % 60
        if len(parts) == 3:
            return f"{new_hh:02d}:{new_mm:02d}:{new_ss:02d}"
        return f"{new_hh:02d}:{new_mm:02d}"
    except Exception:
        return time_str


def main():
    parser = argparse.ArgumentParser(description="Migrate pre-fix attendance timestamps by +7 hours")
    parser.add_argument("--apply", action="store_true", help="Apply updates to database (default is dry-run)")
    parser.add_argument("--dry-run", action="store_true", help="Preview affected rows without modifying database")
    args = parser.parse_args()

    # Determine DB path
    db_env = os.environ.get("DB_PATH", "chat_history.db")
    db_path = Path(db_env)
    if not db_path.is_absolute():
        webai_dir = Path(__file__).resolve().parent.parent
        db_path = webai_dir / db_path

    if not db_path.exists():
        print(f"❌ Database file not found at: {db_path}")
        sys.exit(1)

    print("=" * 60)
    print("⏰ OrgChat AI Attendance Timezone Migration (F2)")
    print(f"📂 Target DB: {db_path}")
    print(f"🔒 Cutoff Timestamp: <= {CUTOFF_DATE} {CUTOFF_TIME}")
    print(f"⚙️  Mode: {'APPLY (Live Update)' if args.apply else 'DRY RUN (Preview Only)'}")
    print("=" * 60)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Check if table exists
    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "time_attendance" not in tables:
        print("ℹ️ Table 'time_attendance' does not exist in this database.")
        conn.close()
        return

    # Select candidates recorded on or before cutoff date
    query = """
        SELECT id, username, org_id, check_date, check_time, check_type, status
        FROM time_attendance
        WHERE check_date < ? OR (check_date = ? AND check_time <= ?)
        ORDER BY check_date ASC, check_time ASC
    """
    candidates = cursor.execute(query, (CUTOFF_DATE, CUTOFF_DATE, CUTOFF_TIME)).fetchall()

    print(f"📊 Found {len(candidates)} attendance record(s) created prior to the timezone fix.\n")

    if not candidates:
        print("✅ No legacy records requiring migration.")
        conn.close()
        return

    # Preview sample
    print("Sample transformations (first 10):")
    print(f"{'ID':<6} | {'User':<15} | {'Date':<10} | {'Old Time':<10} -> {'New Time (+7h)':<15} | {'Type':<10}")
    print("-" * 75)
    for row in candidates[:10]:
        new_time = shift_time_plus_7(row["check_time"])
        print(f"{row['id']:<6} | {row['username']:<15} | {row['check_date']:<10} | {row['check_time']:<10} -> {new_time:<15} | {row['check_type']:<10}")

    if not args.apply:
        print("\n🔍 DRY RUN COMPLETE: 0 rows modified.")
        print("👉 Run with `--apply` to create an automatic safety backup and apply changes.")
        conn.close()
        return

    # Create safety backup table
    backup_table = f"time_attendance_backup_{int(datetime.now().timestamp())}"
    print(f"\n📦 Creating safety backup table `{backup_table}`...")
    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM time_attendance")
    conn.commit()
    print(f"✅ Backup created with {len(candidates)} records.")

    # Apply updates
    updated = 0
    for row in candidates:
        new_time = shift_time_plus_7(row["check_time"])
        cursor.execute("UPDATE time_attendance SET check_time = ? WHERE id = ?", (new_time, row["id"]))
        updated += 1

    conn.commit()
    conn.close()
    print(f"🎉 Successfully migrated {updated} attendance records (+7 hours)!")
    print(f"💡 If needed, rollback query: `INSERT OR REPLACE INTO time_attendance SELECT * FROM {backup_table};`")


if __name__ == "__main__":
    main()

