# -*- coding: utf-8 -*-
"""
tools/audit_attendance_tz.py — Read-only Attendance Timezone Audit Tool
Checks time_attendance records created before tz_fix deployment (2026-11-06 14:22:00).
Usage:
    python tools/audit_attendance_tz.py [path_to_db]
"""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

CUTOFF_DATE = "2026-11-06"
CUTOFF_TIME = "14:22:00"


def audit_attendance_tz(db_path: Path) -> dict:
    if not db_path.exists():
        return {"error": f"Database not found: {db_path}"}

    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    if "time_attendance" not in tables:
        conn.close()
        return {"total": 0, "legacy_candidates": 0, "suspicious_early_morning": 0, "rows": []}

    query = """
        SELECT id, username, org_id, check_date, check_time, check_type, status, created_at
        FROM time_attendance
        WHERE check_date < ? OR (check_date = ? AND check_time <= ?)
        ORDER BY check_date ASC, check_time ASC
    """
    candidates = cursor.execute(query, (CUTOFF_DATE, CUTOFF_DATE, CUTOFF_TIME)).fetchall()
    
    suspicious = []
    for row in candidates:
        # Check if check_time falls into early morning UTC shift (e.g. 00:00 - 05:59 representing 07:00 - 12:59 Thai time)
        ctime = row["check_time"] or ""
        hour = int(ctime.split(":")[0]) if ":" in ctime else -1
        is_suspicious = 0 <= hour <= 5
        suspicious.append({
            "id": row["id"],
            "username": row["username"],
            "check_date": row["check_date"],
            "check_time": row["check_time"],
            "check_type": row["check_type"],
            "status": row["status"],
            "created_at": row["created_at"],
            "suspicious_utc_shift": is_suspicious,
        })

    conn.close()
    return {
        "total": len(candidates),
        "suspicious_early_morning": sum(1 for r in suspicious if r["suspicious_utc_shift"]),
        "rows": suspicious,
    }


def main():
    parser = argparse.ArgumentParser(description="Read-only audit of attendance timezone discrepancy")
    parser.add_argument("db_path", nargs="?", default=os.environ.get("DB_PATH", "chat_history.db"), help="Path to SQLite database")
    args = parser.parse_args()

    db_path = Path(args.db_path)
    res = audit_attendance_tz(db_path)
    if "error" in res:
        print(f"❌ {res['error']}")
        sys.exit(1)

    print("=" * 65)
    print("📋 Attendance Timezone Audit Report (Read-Only)")
    print(f"📂 Database: {db_path}")
    print(f"⏰ Cutoff: <= {CUTOFF_DATE} {CUTOFF_TIME}")
    print(f"📊 Pre-cutoff Records: {res['total']}")
    print(f"⚠️  Likely UTC-shifted records (00:00 - 05:59): {res['suspicious_early_morning']}")
    print("=" * 65)

    if res["rows"]:
        print(f"{'ID':<6} | {'User':<15} | {'Date':<10} | {'Time':<8} | {'Suspicious?':<12}")
        print("-" * 65)
        for r in res["rows"][:15]:
            flag = "⚠️ YES (UTC)" if r["suspicious_utc_shift"] else "No"
            print(f"{r['id']:<6} | {r['username']:<15} | {r['check_date']:<10} | {r['check_time']:<8} | {flag:<12}")

    print("\n✅ Audit complete. Database was not modified.")


if __name__ == "__main__":
    main()

