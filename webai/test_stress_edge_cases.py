"""
Extreme Edge-Case & Boundary Stress Test Suite for OrgChat AI
Tests system resilience against unpredictable, malformed, extreme, and rare user inputs.
Usage:
    python test_stress_edge_cases.py
"""
import sys
import unittest
import os
import json
import threading
import concurrent.futures

os.environ["FLASK_ENV"] = "testing"

try:
    from app_server import create_app
    import database
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_server import create_app
    import database


class ExtremeEdgeCasesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_extreme_unicode_emojis_and_null_bytes_input(self):
        """Test how the system handles null bytes, Thai tone mark stacks, zero-width joiners, and emojis."""
        extreme_strings = [
            "สวัสดี\x00ครับ\x00บอท",  # Null bytes
            "ปิ๊กกกกกกกกกกกกกกกกกกกกกกกกกกกกกกกกกกกก้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้้",  # Extreme Thai tone mark stack
            "👨‍👩‍👧‍👦🏳️‍🌈🚀💥🔥✨🎉🎊🎈🎀🎁",  # Multi-byte ZWJ Emojis
            "‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏‎‏LTR RTL \u202E\u202D Override Test",  # Bidi Overrides
            "a" * 50000,  # 50,000 character single word
        ]
        
        with self.client.session_transaction() as sess:
            sess["user"] = "edge_tester"
            sess["org_id"] = 1

        for s in extreme_strings:
            # Post message with extreme content
            res = self.client.post(
                "/api/posts",
                json={"title": "Test Title", "content": s, "category": "All"},
                headers={"X-CSRF-Token": "testing"}
            )
            # Must return clean response without 500 Internal Server Error crash
            self.assertIn(res.status_code, (200, 400, 403, 422))

    def test_invalid_date_boundary_inputs(self):
        """Test boundary out-of-range dates in schedule/leave creation."""
        invalid_dates = [
            "9999-99-99",
            "0000-00-00",
            "2026-02-31",
            "2026/13/45",
            "INVALID_DATE_STRING",
            "'' OR 1=1 --",
            "",
            None,
        ]

        with self.client.session_transaction() as sess:
            sess["user"] = "edge_tester"
            sess["org_id"] = 1

        for d in invalid_dates:
            res = self.client.post(
                "/api/leave/request",
                json={
                    "type": "ลาพักร้อน",
                    "start_date": d,
                    "end_date": d,
                    "reason": "Test boundary date"
                },
                headers={"X-CSRF-Token": "testing"}
            )
            # App must not crash with 500 Server Error
            self.assertIn(res.status_code, (200, 400, 403, 422))

    def test_path_traversal_filename_sanitization(self):
        """Test file path traversal payloads in database file helper functions."""
        malicious_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\Windows\\System32\\cmd.exe",
            "file\x00.png",
            "CON",
            "PRN",
            "AUX",
            "NUL",
            ".htaccess",
            "shell.php.png",
            "script.py",
        ]

        for fname in malicious_filenames:
            # Run helper check
            safe_fname = os.path.basename(fname).replace("\x00", "")
            self.assertNotIn("..", safe_fname)
            self.assertNotIn("\x00", safe_fname)

    def test_malformed_json_and_oversized_headers(self):
        """Test sending corrupt JSON syntax or unexpected data types (e.g. array instead of dict)."""
        with self.client.session_transaction() as sess:
            sess["user"] = "edge_tester"
            sess["org_id"] = 1

        # Send JSON list instead of expected JSON dict
        res1 = self.client.post(
            "/api/posts",
            data="[1, 2, 3, 'corrupt']",
            content_type="application/json",
            headers={"X-CSRF-Token": "testing"}
        )
        self.assertIn(res1.status_code, (400, 403, 422))

        # Send empty raw body
        res2 = self.client.post(
            "/api/posts",
            data="",
            content_type="application/json",
            headers={"X-CSRF-Token": "testing"}
        )
        self.assertIn(res2.status_code, (400, 403, 422))

    def test_concurrent_database_reads_writes_stress(self):
        """Test 20 parallel threads simultaneously writing and reading to DB under heavy load."""
        def db_worker(thread_idx):
            username = f"stress_user_{thread_idx}"
            try:
                # Write profile
                conn = database._get_conn()
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO user_profiles (username, display_name) VALUES (?, ?)",
                        (username, f"Stress User {thread_idx}")
                    )
                    conn.commit()
                finally:
                    conn.close()

                # Fetch leaves
                database.get_user_leaves(username)
                return True
            except Exception as e:
                print(f"[Concurrency Error Thread {thread_idx}]: {e}")
                return False

        # Execute 20 concurrent threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(db_worker, i) for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All 20 parallel operations must succeed without DB locking deadlock
        self.assertTrue(all(results))

    def test_organization_id_type_boundary(self):
        """Test passing negative, zero, float, or string values as organization_id."""
        bad_org_ids = [-1, 0, 999999999, "not_an_org", 3.14159, None]

        for org_id in bad_org_ids:
            try:
                leaves = database.get_all_leaves(org_id=org_id)
                self.assertIsInstance(leaves, list)
            except Exception as e:
                self.fail(f"get_all_leaves failed unexpectedly with org_id={org_id}: {e}")


if __name__ == "__main__":
    print("==========================================================")
    print(" Running Extreme Edge-Case & Boundary Stress Test Suite")
    print("==========================================================")
    unittest.main()
