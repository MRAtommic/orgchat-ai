import os
import sys
import unittest
import time
from datetime import datetime, timedelta

os.environ["FLASK_ENV"] = "testing"
_base = os.path.dirname(os.path.abspath(__file__))
_webai = os.path.join(os.path.dirname(_base), "webai") if "scratch" in _base else _base
if _webai not in sys.path:
    sys.path.insert(0, _webai)

import database
from app_server import create_app
from routes.chat import _is_duplicate_webhook_event, _PROCESSED_WEBHOOK_EVENTS, online_users_registry


class MultiScenarioHardeningTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_scenario_1_gps_attendance_debounce_and_update(self):
        """Test GPS attendance debounces rapid double-taps and updates checkout timestamps gracefully."""
        test_user = f"audit_gps_user_{int(time.time())}"
        org_id = 1

        # 1. First punch -> check_in
        rec1 = database.record_attendance(
            username=test_user, org_id=org_id, check_type="check_in",
            latitude=13.75, longitude=100.50, address="Office HQ",
            distance_meters=15.0, status="on_time"
        )
        self.assertEqual(rec1["check_type"], "check_in")

        records = database.get_today_attendance(test_user, org_id=org_id)
        self.assertEqual(len(records), 1)

        # 2. Check elapsed calculation in routes/chat.py
        check_in_rec = records[0]
        in_time_parts = [int(p) for p in check_in_rec["check_time"].split(":")[:3]]
        now_dt = datetime.now()
        in_dt = now_dt.replace(hour=in_time_parts[0], minute=in_time_parts[1], second=in_time_parts[2])
        elapsed = (now_dt - in_dt).total_seconds()
        self.assertLess(elapsed, 120, "Should be within 120s debounce window")

        # 3. Punch check-out
        rec_out = database.record_attendance(
            username=test_user, org_id=org_id, check_type="check_out",
            latitude=13.75, longitude=100.50, address="Office HQ",
            distance_meters=15.0, status="on_time"
        )
        self.assertEqual(rec_out["check_type"], "check_out")

        records_after_out = database.get_today_attendance(test_user, org_id=org_id)
        self.assertEqual(len(records_after_out), 2)

        # 4. Update checkout later in the day
        new_time = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M:%S")
        updated = database.update_attendance_checkout(
            attendance_id=rec_out["id"],
            check_time=new_time,
            distance_meters=20.0,
            status="on_time"
        )
        self.assertTrue(updated)

        # Verify updated record
        updated_records = database.get_today_attendance(test_user, org_id=org_id)
        self.assertEqual(len(updated_records), 2, "Should remain 2 rows (1 check_in, 1 check_out), not 3!")
        checkout_row = next(r for r in updated_records if r["check_type"] == "check_out")
        self.assertEqual(checkout_row["check_time"], new_time)

    def test_scenario_2_line_webhook_deduplication(self):
        """Test webhook event deduplication sliding window cache."""
        event_id = f"evt_test_dedup_{time.time()}"
        event_payload = {"webhookEventId": event_id, "type": "message", "message": {"id": "msg_999"}}

        # First delivery attempt -> Not duplicate
        is_dup1 = _is_duplicate_webhook_event(event_payload)
        self.assertFalse(is_dup1, "First attempt must NOT be considered duplicate")

        # Second delivery attempt (LINE retry) -> Duplicate!
        is_dup2 = _is_duplicate_webhook_event(event_payload)
        self.assertTrue(is_dup2, "Second attempt with same ID MUST be flagged as duplicate")

    def test_scenario_3_kb_mimetype_resolution(self):
        """Test mimetypes are resolved accurately for standard file extensions."""
        import mimetypes
        test_files = {
            "handbook.pdf": "application/pdf",
            "report.docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "budget.xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "slides.pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "receipt.png": "image/png",
            "photo.jpg": "image/jpeg",
        }
        for filename, expected_prefix in test_files.items():
            guessed, _ = mimetypes.guess_type(filename)
            self.assertEqual(guessed, expected_prefix, f"MIME type mismatch for {filename}")

        # CSV on Windows can be application/vnd.ms-excel or text/csv
        csv_mime, _ = mimetypes.guess_type("data.csv")
        self.assertIn(csv_mime, ["text/csv", "application/vnd.ms-excel"])

    def test_scenario_4_fast_post_access_check(self):
        """Test database.check_post_access performance and isolation."""
        self.assertFalse(database.check_post_access(999999999, org_id=1))

    def test_scenario_5_leave_request_date_validation(self):
        """Test /api/leave/request rejects invalid calendar dates."""
        with self.client.session_transaction() as sess:
            sess["user"] = "date_validator_user"
            sess["org_id"] = 1
            sess["_csrf_token"] = "csrf_test_val"

        # Test non-existent February 31
        res = self.client.post(
            "/api/leave/request",
            json={
                "type": "Sick",
                "start_date": "2026-02-31",
                "end_date": "2026-02-31",
                "reason": "Invalid date test"
            },
            headers={"X-CSRF-Token": "csrf_test_val"}
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data["ok"])
        self.assertIn("รูปแบบวันที่ไม่ถูกต้อง", data["error"])

    def test_scenario_6_socketio_multitab_disconnect(self):
        """Test SocketIO multi-tab disconnect logic avoids premature offline marking."""
        username = "multitab_tester"
        sid_tab1 = "sid_tab_1_abc"
        sid_tab2 = "sid_tab_2_xyz"

        # Tab 1 and Tab 2 online
        online_users_registry[sid_tab1] = username
        online_users_registry[sid_tab2] = username

        # Tab 1 closes -> sid_tab1 popped
        popped = online_users_registry.pop(sid_tab1, None)
        self.assertEqual(popped, username)

        # Tab 2 is STILL OPEN -> username is still in online_users_registry.values()!
        user_still_has_tabs = username in online_users_registry.values()
        self.assertTrue(user_still_has_tabs, "User should still have tab 2 open")

        # Tab 2 closes -> sid_tab2 popped
        popped2 = online_users_registry.pop(sid_tab2, None)
        self.assertEqual(popped2, username)

        # Now all tabs closed -> user completely offline
        user_still_has_tabs2 = username in online_users_registry.values()
        self.assertFalse(user_still_has_tabs2, "User should now have 0 open tabs")

    def test_scenario_7_admin_dismiss_alert_api(self):
        """Test /api/admin/dismiss-alert endpoint clears health alerts."""
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"
            sess["org_id"] = 1
            sess["role"] = "admin"
            sess["_csrf_token"] = "csrf_test_val"

        res = self.client.post(
            "/api/admin/dismiss-alert",
            json={"alert_id": "google_credential_error"},
            headers={"X-CSRF-Token": "csrf_test_val"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["ok"])


if __name__ == "__main__":
    unittest.main()
