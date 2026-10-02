# -*- coding: utf-8 -*-
"""
webai/tests/test_leave.py — Leave Management Unit Tests
Tests leave request lifecycle, overlap detection, approval flow, and quotas.
"""

import sys
from pathlib import Path
WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database

class TestLeave(BaseTestCase):

    def test_leave_creation_and_retrieval(self):
        """Test submitting a leave request and fetching it by ID."""
        leave_id = database.create_leave_request(
            username="john_doe",
            leave_type="sick",
            start_date="2026-04-10",
            end_date="2026-04-11",
            reason="High fever",
            org_id=1
        )
        self.assertIsNotNone(leave_id)

        req = database.get_leave_request(leave_id)
        self.assertIsNotNone(req)
        self.assertEqual(req.get("username"), "john_doe")
        self.assertEqual(req.get("type") or req.get("leave_type"), "sick")
        self.assertEqual(req.get("status"), "pending")

    def test_leave_overlap_detection(self):
        """Test that overlapping leave requests are correctly detected."""
        username = "overlap_user"
        # First leave: April 1 to April 5
        database.create_leave_request(
            username=username,
            leave_type="annual",
            start_date="2026-04-01",
            end_date="2026-04-05",
            reason="Vacation",
            org_id=1
        )

        # Overlapping period: April 3 to April 7
        overlap = database.check_leave_overlap(username, "2026-04-03", "2026-04-07")
        self.assertIsNotNone(overlap)

        # Non-overlapping period: April 10 to April 15
        no_overlap = database.check_leave_overlap(username, "2026-04-10", "2026-04-15")
        self.assertIsNone(no_overlap)

    def test_leave_approval_and_rejection(self):
        """Test approving and rejecting leave requests."""
        username = "charlie"
        req_id = database.create_leave_request(
            username=username,
            leave_type="business",
            start_date="2026-05-01",
            end_date="2026-05-02",
            reason="Client site visit",
            org_id=1
        )

        # Approve
        database.update_leave_status(req_id, "approved", approver="manager_1", note="Have a productive trip")
        req = database.get_leave_request(req_id)
        self.assertEqual(req.get("status"), "approved")
        self.assertEqual(req.get("approved_by"), "manager_1")

        # Reject another request
        req2_id = database.create_leave_request(
            username=username,
            leave_type="vacation",
            start_date="2026-05-10",
            end_date="2026-05-15",
            reason="Personal travel",
            org_id=1
        )
        database.update_leave_status(req2_id, "rejected", approver="manager_1", note="Blackout period")
        req2 = database.get_leave_request(req2_id)
        self.assertEqual(req2.get("status"), "rejected")

if __name__ == "__main__":
    unittest.main()
