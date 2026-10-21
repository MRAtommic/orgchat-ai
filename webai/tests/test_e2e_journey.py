# -*- coding: utf-8 -*-
"""
webai/tests/test_e2e_journey.py — End-to-End QA User Journey Tests
Validates the complete user lifecycle: Org Creation -> Member Onboarding -> Chat -> Leave Workflow -> Finance Claim.
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

class TestE2EJourney(BaseTestCase):

    def test_complete_user_lifecycle(self):
        """User Journey Flow: Create organization, add member, profile setup, chat, leave request, and expense claim."""
        # 1. Organization Setup
        org_name = f"QA Corp {uuid.uuid4().hex[:6]}"
        org_id, slug = database.create_organization(name=org_name, owner_username="qa_owner")
        self.assertIsNotNone(org_id)
        self.assertTrue(slug.startswith("qa-corp"))

        # 2. Member Onboarding & Profile Setup
        username = f"qa_employee_{uuid.uuid4().hex[:4]}"
        database.add_org_member(org_id=org_id, username=username, role="member")
        self.assertTrue(database.is_org_member(org_id, username))

        database.update_user_profile(
            username=username,
            display_name="QA Senior Tester",
            department="Quality Assurance"
        )
        profile = database.get_user_profile(username)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.get("display_name"), "QA Senior Tester")
        self.assertEqual(profile.get("department"), "Quality Assurance")

        # 3. Chat Interaction Flow
        msg_id = database.save_message(
            username=username,
            role="user",
            text="Can you review my vacation schedule and expense report?",
            org_id=org_id
        )
        self.assertIsNotNone(msg_id)

        history = database.get_history(username=username, limit=10, org_id=org_id)
        self.assertTrue(any("Can you review my vacation schedule" in m.get("text", "") for m in history))

        # 4. Leave Application & Approval Flow
        leave_id = database.create_leave_request(
            username=username,
            leave_type="vacation",
            start_date="2026-11-01",
            end_date="2026-11-03",
            reason="Family Vacation",
            org_id=org_id
        )
        self.assertIsNotNone(leave_id)

        # Overlapping leave check must detect conflict
        has_overlap = database.check_leave_overlap(username, "2026-11-02", "2026-11-04")
        self.assertTrue(has_overlap)

        # Manager approves leave
        approved = database.update_leave_status(leave_id, "approved", approver="qa_owner", note="Approved")
        self.assertTrue(approved)

        leave_rec = database.get_leave_request(leave_id)
        self.assertEqual(leave_rec.get("status"), "approved")

        # 5. Finance Expense Claim Submission Flow
        claim_id = database.add_expense_claim(
            line_user_id="U_qa_tester",
            username=username,
            vendor="Taxi Co",
            amount="1500.50",
            expense_date="2026-11-01",
            file_link="https://drive.google.com/test_taxi_slip.jpg"
        )
        self.assertIsNotNone(claim_id)

if __name__ == "__main__":
    unittest.main()
