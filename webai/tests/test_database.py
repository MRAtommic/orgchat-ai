# -*- coding: utf-8 -*-
"""
webai/tests/test_database.py — Database CRUD & Model Unit Tests
Tests core database operations across users, orgs, messages, leave, and migrations.
"""

import sys
from pathlib import Path

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database

class TestDatabase(BaseTestCase):

    def test_migrations_applied(self):
        """Verify that all initial migrations are applied to the test DB."""
        history = database.get_migration_history()
        self.assertGreaterEqual(len(history), 4)
        versions = [h["version"] for h in history]
        self.assertIn("001_initial_tracking", versions)
        self.assertIn("002_composite_indexes", versions)
        self.assertIn("003_leave_requests_indexes", versions)
        self.assertIn("004_security_events_indexes", versions)

    def test_user_profile_crud(self):
        """Test saving and retrieving user profile."""
        username = "test_user_01"
        database.update_user_profile(
            username=username,
            display_name="Test Employee",
            department="Engineering"
        )
        profile = database.get_user_profile(username)
        self.assertIsNotNone(profile)
        self.assertEqual(profile.get("display_name"), "Test Employee")
        self.assertEqual(profile.get("department"), "Engineering")

    def test_organization_crud(self):
        """Test organization creation, membership, and retrieval."""
        import uuid
        org_name = f"Test Corp {uuid.uuid4().hex[:6]}"
        org_id, slug = database.create_organization(name=org_name, owner_username="owner_01")
        self.assertIsNotNone(org_id)
        self.assertTrue(slug.startswith("test-corp"))

        # Add member
        database.add_org_member(org_id=org_id, username="member_01", role="member")
        members = database.get_org_members(org_id)
        usernames = [m.get("username") for m in members]
        self.assertIn("member_01", usernames)

        # Check membership
        self.assertTrue(database.is_org_member(org_id, "member_01"))
        member_obj = next((m for m in members if m.get("username") == "member_01"), None)
        self.assertIsNotNone(member_obj)
        self.assertEqual(member_obj.get("role"), "member")

    def test_chat_message_flow(self):
        """Test saving and fetching chat messages."""
        msg_id = database.save_message(
            username="alice",
            role="user",
            text="Hello OrgChat!",
            org_id=1
        )
        self.assertIsNotNone(msg_id)

        history = database.get_history(username="alice", limit=10, org_id=1)
        self.assertTrue(any("Hello OrgChat!" in m.get("text", "") for m in history))

    def test_leave_request_crud(self):
        """Test leave creation, approval, and quota tracking."""
        leave_id = database.create_leave_request(
            username="bob",
            leave_type="vacation",
            start_date="2026-03-01",
            end_date="2026-03-03",
            reason="Holiday trip",
            org_id=1
        )
        self.assertIsNotNone(leave_id)

        # Approve leave
        database.update_leave_status(leave_id, "approved", approver="admin", note="Approved by HR")
        leave = database.get_leave_request(leave_id)
        self.assertEqual(leave.get("status"), "approved")
        self.assertEqual(leave.get("approved_by"), "admin")

    def test_audit_log_signing(self):
        """Test security audit log generation with HMAC integrity signature."""
        database.log_event(
            action="USER_LOGIN_SUCCESS",
            details="User logged in via Web UI",
            user="alice",
            org_id=1
        )
        logs = database.get_audit_logs(org_id=1, limit=5)
        self.assertGreaterEqual(len(logs), 1)
        latest = logs[0]
        self.assertEqual(latest.get("action"), "USER_LOGIN_SUCCESS")
        self.assertEqual(latest.get("username"), "alice")

if __name__ == "__main__":
    unittest.main()
