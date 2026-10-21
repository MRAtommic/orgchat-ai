# -*- coding: utf-8 -*-
"""
webai/tests/test_attendance.py — Attendance Management & Admin Manual Entry Tests
Validates GPS check-in/out, Admin manual record overrides, daily summaries, and deletions.
"""

import sys
import uuid
from pathlib import Path

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database

class TestAttendance(BaseTestCase):

    def setUp(self):
        super().setUp()
        uid = uuid.uuid4().hex[:6]
        self.org_id, _ = database.create_organization(f"Attendance Org {uid}", "Owner")
        self.u_john = f"john_{uid}"
        self.u_sarah = f"sarah_{uid}"

        database.add_org_member(self.org_id, self.u_john, "member")
        database.update_user_profile(self.u_john, display_name="John Doe", department="Engineering")

        database.add_org_member(self.org_id, self.u_sarah, "member")
        database.update_user_profile(self.u_sarah, display_name="Sarah Connor", department="Sales")

    def test_member_attendance_checkin_and_checkout(self):
        """Test regular member check-in and check-out recording."""
        target_date = "2026-10-21"
        
        # Check-in
        res_in = database.record_attendance(
            username=self.u_john,
            org_id=self.org_id,
            check_type="check_in",
            latitude=13.7563,
            longitude=100.5018,
            address="Bangkok Office",
            distance_meters=15.0,
            status="on_time",
            note="Morning arrival",
            custom_date=target_date,
            custom_time="08:55:00"
        )
        self.assertTrue(res_in.get("ok", False) or res_in.get("id") is not None)

        # Check-out
        res_out = database.record_attendance(
            username=self.u_john,
            org_id=self.org_id,
            check_type="check_out",
            latitude=13.7563,
            longitude=100.5018,
            address="Bangkok Office",
            distance_meters=12.0,
            status="on_time",
            note="End of day",
            custom_date=target_date,
            custom_time="17:35:00"
        )
        self.assertTrue(res_out.get("ok", False) or res_out.get("id") is not None)

        # Verify records retrieved
        records = database.get_org_attendance(self.org_id, date_from=target_date, date_to=target_date, username=self.u_john)
        self.assertEqual(len(records), 2)
        types = [r["check_type"] for r in records]
        self.assertIn("check_in", types)
        self.assertIn("check_out", types)

    def test_admin_manual_attendance_entry(self):
        """Test Admin setting or correcting employee attendance manually."""
        target_date = "2026-10-22"
        
        # Admin records check-in and check-out for Sarah
        result = database.set_manual_attendance(
            org_id=self.org_id,
            username=self.u_sarah,
            check_date=target_date,
            check_in_time="09:15",
            check_out_time="18:00",
            status="manual_admin",
            note="Off-site client meeting approved by manager",
            updated_by="Admin"
        )
        self.assertTrue(result.get("ok"))
        self.assertIsNotNone(result.get("check_in_id"))
        self.assertIsNotNone(result.get("check_out_id"))

        # Verify daily attendance status
        daily = database.get_daily_org_attendance(self.org_id, target_date=target_date)
        sarah_record = next((m for m in daily["members"] if m["username"] == self.u_sarah), None)
        self.assertIsNotNone(sarah_record)
        self.assertTrue(sarah_record["attended"])
        self.assertEqual(sarah_record["status"], "manual_admin")
        self.assertGreater(sarah_record["work_duration_hours"], 8.0)

    def test_daily_org_attendance_summary(self):
        """Test daily organization attendance counts, absence tracking, and percentages."""
        target_date = "2026-10-23"

        # John checks in
        database.record_attendance(
            username=self.u_john,
            org_id=self.org_id,
            check_type="check_in",
            latitude=13.75,
            longitude=100.50,
            status="on_time",
            custom_date=target_date,
            custom_time="08:45:00"
        )
        # Sarah does NOT check in (absent)

        daily = database.get_daily_org_attendance(self.org_id, target_date=target_date)
        summary = daily["summary"]
        self.assertEqual(summary["total_members"], 3)
        self.assertEqual(summary["present_count"], 1)
        self.assertEqual(summary["absent_count"], 2)
        self.assertEqual(summary["present_percentage"], round(1/3 * 100, 1))

    def test_delete_attendance_record(self):
        """Test deleting attendance records for a user on a given date."""
        target_date = "2026-10-24"
        database.record_attendance(
            username=self.u_john,
            org_id=self.org_id,
            check_type="check_in",
            latitude=13.75,
            longitude=100.50,
            custom_date=target_date,
            custom_time="09:00:00"
        )
        
        # Verify it exists
        before = database.get_org_attendance(self.org_id, date_from=target_date, date_to=target_date, username=self.u_john)
        self.assertEqual(len(before), 1)

        # Delete
        deleted_count = database.delete_attendance_record(self.org_id, self.u_john, target_date)
        self.assertEqual(deleted_count, 1)

        # Verify it is deleted
        after = database.get_org_attendance(self.org_id, date_from=target_date, date_to=target_date, username=self.u_john)
        self.assertEqual(len(after), 0)

if __name__ == "__main__":
    unittest.main()
