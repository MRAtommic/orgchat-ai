# -*- coding: utf-8 -*-
"""
cleanup_test_users.py — Safe cleanup of automated test users
==============================================================
Removes 98 mock/stress/test users while strictly preserving all 14 real user accounts.
"""

import os
import sys

# Ensure webai directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database

REAL_USERS = {
    'admin',
    'Admin',
    'AI-Assistant',
    'superadmin',
    'feweiei2004',
    'few12345',
    'nicha',
    'nichatongyou301147',
    'mxmm2547',
    'mxmm2547@gmail.com',
    's6606021631050',
    'klon2547',
    'khnk63007',
    'hum'
}

def run_cleanup():
    print("=" * 60)
    print("🧹 Safe Cleanup of Test Users")
    print("=" * 60)

    with database._get_conn() as conn:
        cur = conn.cursor()
        
        # 1. Fetch all users from database
        cur.execute("""
            SELECT username FROM user_settings 
            UNION SELECT username FROM user_profiles 
            UNION SELECT username FROM organization_members
        """)
        all_users = set(r[0] for r in cur.fetchall())
        test_users = sorted(list(all_users - REAL_USERS))
        
        if not test_users:
            print("✅ No test users found. Database is already clean.")
            return

        print(f"Preserving {len(all_users - set(test_users))} REAL users: {sorted(all_users - set(test_users))}")
        print(f"Removing {len(test_users)} TEST users...")

        # 2. Delete from tables with 'username' column
        user_col_tables = [
            'user_settings', 'user_profiles', 'organization_members',
            'room_members', 'time_attendance', 'leave_requests',
            'likes', 'post_reactions', 'notifications',
            'password_reset_tokens', 'user_google_tokens'
        ]

        total_deleted = 0
        for tbl in user_col_tables:
            try:
                placeholders = ','.join(['?'] * len(test_users))
                cur.execute(f"DELETE FROM `{tbl}` WHERE username IN ({placeholders})", test_users)
                row_count = cur.rowcount
                total_deleted += row_count
                if row_count > 0:
                    print(f"  - Deleted {row_count} rows from `{tbl}`")
            except Exception as e:
                # Table might not exist or might not have username column
                pass

        # 3. Delete from tables with 'author' column
        for tbl in ['posts', 'comments']:
            try:
                placeholders = ','.join(['?'] * len(test_users))
                cur.execute(f"DELETE FROM `{tbl}` WHERE author IN ({placeholders})", test_users)
                row_count = cur.rowcount
                total_deleted += row_count
                if row_count > 0:
                    print(f"  - Deleted {row_count} rows from `{tbl}`")
            except Exception:
                pass

        # 4. Delete test logs from drive_logs
        try:
            placeholders = ','.join(['?'] * len(test_users))
            cur.execute(f"DELETE FROM `drive_logs` WHERE user_id IN ({placeholders})", test_users)
            row_count = cur.rowcount
            total_deleted += row_count
            if row_count > 0:
                print(f"  - Deleted {row_count} rows from `drive_logs`")
        except Exception:
            pass

        print(f"✅ Successfully deleted {len(test_users)} test users ({total_deleted} related records cleared).")

    # 5. Optimize & checkpoint WAL
    checkpoint_res = database.optimize_and_checkpoint_db()
    print(f"🧹 Database WAL checkpoint & vacuum: {checkpoint_res}")
    print("=" * 60)

if __name__ == "__main__":
    run_cleanup()
