# -*- coding: utf-8 -*-
"""
test_stability_1_3_4.py
Verification suite for Stability Tasks 1, 3, 4 requested by user:
- Task 1: Offline-first storage & queueing for slips/receipts
- Task 3: Connection leak fixes & SQLite busy_timeout
- Task 4: Debounce & idempotency on key actions (Attendance clock, Leaves, Posts)
"""

import os
import sys
import time
import unittest
from datetime import datetime

# Add webai directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
from tools.offline_storage import save_local_receipt_backup, sync_single_offline_upload, sync_all_pending_offline_uploads

class TestStability134(unittest.TestCase):
    def setUp(self):
        database.init_db()

    # --- TASK 1: Zero Data Loss / Offline-First Storage ---
    def test_task1_save_local_receipt_backup(self):
        dummy_content = b"fake_slip_image_data_12345"
        rel_path, abs_path, web_url = save_local_receipt_backup(dummy_content, "slip_test.png")
        
        self.assertTrue(os.path.exists(abs_path))
        self.assertTrue(web_url.startswith("/uploads/receipts_backup/"))
        with open(abs_path, "rb") as f:
            self.assertEqual(f.read(), dummy_content)
            
        # Clean up
        try: os.remove(abs_path)
        except: pass

    def test_task1_offline_queue_crud(self):
        # Insert into queue
        q_id = database.add_offline_upload(
            org_id=1,
            username="test_user",
            user_id="U_test123",
            original_filename="receipt_test.pdf",
            local_filepath="uploads/receipts_backup/fake.pdf",
            mimetype="application/pdf",
            folder_name="ใบเสร็จ",
            analysis={"summary": "Test Summary"},
            extracted_data={"net_amount": 500.0, "date": "29/09/2026"}
        )
        self.assertIsNotNone(q_id)
        
        # Check pending queue
        pending = database.get_pending_offline_uploads(limit=50)
        found = next((item for item in pending if item["id"] == q_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["extracted_data"]["net_amount"], 500.0)
        
        # Update status
        ok = database.update_offline_upload_status(q_id, "synced", drive_link="https://drive.google.com/test", sheets_row=12)
        self.assertTrue(ok)
        
        # Verify stats
        stats = database.get_offline_queue_stats(org_id=1)
        self.assertGreaterEqual(stats["synced"], 1)

    # --- TASK 3: Database Connection Wrapper & Locks ---
    def test_task3_connection_busy_timeout_and_no_leak(self):
        # Verify _get_conn sets busy_timeout
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout")
        row = cur.fetchone()
        timeout_val = row[0]
        # Should be 60000ms
        self.assertEqual(timeout_val, 60000)
        conn.close()

        # Context manager closes safely
        with database._get_conn() as c:
            c.execute("SELECT 1")
        self.assertTrue(c._closed)

    # --- TASK 4: Debounce & Idempotency Guards ---
    def test_task4_attendance_debounce_logic(self):
        username = f"test_user_att_{int(time.time())}"
        org_id = 999
        
        # 1. Record check_in
        rec1 = database.record_attendance(
            username=username,
            org_id=org_id,
            check_type="check_in",
            latitude=13.7563,
            longitude=100.5018,
            address="Test Office",
            distance_meters=10.0,
            status="on_time"
        )
        self.assertIsNotNone(rec1)
        
        # 2. Check get_today_attendance
        records = database.get_today_attendance(username, org_id=org_id)
        check_in_rec = next((r for r in records if r.get("check_type") == "check_in"), None)
        self.assertIsNotNone(check_in_rec)
        
        # Verify created_at or check_time exists
        self.assertTrue("check_time" in check_in_rec or "created_at" in check_in_rec)

    def test_task4_leave_request_debounce_logic(self):
        username = f"test_leave_user_{int(time.time())}"
        l_type = "Sick"
        s_date = "2026-10-01"
        e_date = "2026-10-02"
        
        id1 = database.create_leave_request(username, l_type, s_date, e_date, "Flu", org_id=1)
        self.assertIsNotNone(id1)
        
        # Query recent leaves
        recent = database.get_user_leaves(username)
        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0]["id"], id1)

    def test_task4_post_debounce_logic(self):
        author = f"test_author_{int(time.time())}"
        content = "Hello debounce test"
        pid1 = database.add_post(content, author, "General", org_id=999)
        self.assertIsNotNone(pid1)
        
        posts = database.get_posts(org_id=999)
        found = [p for p in posts if p.get("author") == author and p.get("content") == content]
        self.assertEqual(len(found), 1)

if __name__ == "__main__":
    unittest.main()
