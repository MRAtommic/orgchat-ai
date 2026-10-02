# -*- coding: utf-8 -*-
"""
webai/tests/test_rbac.py — Role-Based Access Control & Multi-Tenancy Unit Tests
Tests organization data isolation, admin role verification, and IP threat blocking.
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

class TestRBAC(BaseTestCase):

    def test_multi_tenant_organization_isolation(self):
        """Test that data from Organization A is isolated from Organization B."""
        # Create Org A and Org B
        org_a_name = f"Alpha Corp {uuid.uuid4().hex[:6]}"
        org_b_name = f"Beta Corp {uuid.uuid4().hex[:6]}"
        org_a_id, _ = database.create_organization(name=org_a_name, owner_username="alice")
        org_b_id, _ = database.create_organization(name=org_b_name, owner_username="bob")

        # Save private messages in Org A and Org B
        database.save_message(username="alice", role="user", text="Alpha Secret Roadmap", org_id=org_a_id)
        database.save_message(username="bob", role="user", text="Beta Secret Budget", org_id=org_b_id)

        # Retrieve messages scoped to Org A
        history_a = database.get_history(username="alice", limit=10, org_id=org_a_id)
        history_a_texts = [m.get("text") for m in history_a]
        self.assertIn("Alpha Secret Roadmap", history_a_texts)
        self.assertNotIn("Beta Secret Budget", history_a_texts)

        # Retrieve messages scoped to Org B
        history_b = database.get_history(username="bob", limit=10, org_id=org_b_id)
        history_b_texts = [m.get("text") for m in history_b]
        self.assertIn("Beta Secret Budget", history_b_texts)
        self.assertNotIn("Alpha Secret Roadmap", history_b_texts)

    def test_org_admin_role_check(self):
        """Test admin role checks within an organization."""
        org_name = f"Role Corp {uuid.uuid4().hex[:6]}"
        org_id, _ = database.create_organization(name=org_name, owner_username="admin_user")

        # Add regular employee
        database.add_org_member(org_id=org_id, username="staff_user", role="member")

        self.assertTrue(database.is_org_admin(org_id, "admin_user"))
        self.assertFalse(database.is_org_admin(org_id, "staff_user"))

    def test_ip_blacklisting_threat_mitigation(self):
        """Test that malicious IPs can be blacklisted and unblocked."""
        malicious_ip = "203.0.113.42"

        # Initially not blocked
        blocked, _ = database.is_ip_blacklisted(malicious_ip)
        self.assertFalse(blocked)

        # Block IP
        database.block_ip(malicious_ip, reason="Repeated SQL injection attempt", duration_minutes=60)
        blocked, _ = database.is_ip_blacklisted(malicious_ip)
        self.assertTrue(blocked)

        # Verify listed in blacklisted IPs
        blacklisted = database.get_blacklisted_ips()
        ip_list = [b.get("ip_address") for b in blacklisted]
        self.assertIn(malicious_ip, ip_list)

        # Unblock IP
        database.unblock_ip(malicious_ip)
        blocked, _ = database.is_ip_blacklisted(malicious_ip)
        self.assertFalse(blocked)

    def test_org_quota_info(self):
        """Test retrieving organization quota info and plan configuration."""
        org_name = f"Quota Corp {uuid.uuid4().hex[:6]}"
        org_id, _ = database.create_organization(name=org_name, owner_username="quota_owner")
        
        quota = database.get_org_quota_info(org_id)
        self.assertTrue(quota.get("ok"))
        self.assertEqual(quota.get("org_name"), org_name)
        self.assertIn("plan", quota)
        self.assertIn("max_users", quota)
        self.assertIn("member_count", quota)


if __name__ == "__main__":
    unittest.main()
