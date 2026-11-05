import unittest
import sqlite3
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.schema import init_db
from db.migrations import run_migrations, MIGRATIONS


class TestFreshDBMigrations(unittest.TestCase):
    def test_fresh_database_runs_all_migrations_without_error(self):
        """U0-4: Verify a fresh SQLite database completes all migrations cleanly."""
        conn = sqlite3.connect(":memory:")
        try:
            # 1. Initialize schema (which internally calls run_migrations)
            init_db(conn)

            # 2. Check _migrations table to ensure all migrations were applied
            cur = conn.cursor()
            cur.execute("SELECT version FROM _migrations")
            applied_in_db = [row[0] for row in cur.fetchall()]
            expected_versions = [m[0] for m in MIGRATIONS]
            self.assertEqual(len(applied_in_db), len(expected_versions))

            # 3. Running run_migrations again should be idempotent (return 0 new)
            applied_again = run_migrations(conn)
            self.assertEqual(len(applied_again), 0)

            # 4. Verify leave_requests table has org_id column and index works
            cur.execute("PRAGMA table_info(leave_requests)")
            cols = [row[1] for row in cur.fetchall()]
            self.assertIn("org_id", cols, "leave_requests must have org_id column")

            # 5. Verify index exists
            cur.execute("PRAGMA index_list(leave_requests)")
            indexes = [row[1] for row in cur.fetchall()]
            self.assertIn("idx_leave_org_user", indexes)
            self.assertIn("idx_leave_org_status", indexes)
        finally:
            conn.close()


if __name__ == '__main__':
    unittest.main()
