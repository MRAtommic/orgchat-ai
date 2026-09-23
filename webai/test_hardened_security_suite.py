# -*- coding: utf-8 -*-
"""
test_hardened_security_suite.py
Verification suite for the newly hardened security defenses:
1. Real-time WAF & Threat Auto-Jail
2. Session Invalidation on Password Change (Multi-Device Revocation)
3. Password Policy & Complexity Enforcement
4. Security Center & IP Management
"""

import unittest
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
sys.path.insert(0, str(BASE_DIR))

import app_server
import database

class HardenedSecurityDefenseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = app_server.create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_01_waf_sqli_attack_auto_jail(self):
        """Test that WAF intercepts SQL Injection payload in URL query and auto-blacklists IP."""
        attacker_ip = "198.51.100.44"
        
        # Ensure IP is clean first
        database.unblock_ip(attacker_ip)
        
        # Send SQLi payload
        res = self.client.get(
            "/api/csrf-token?test_param=' UNION SELECT null, username, password FROM users --",
            environ_overrides={'REMOTE_ADDR': attacker_ip}
        )
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data.get("error"), "waf_blocked")
        
        # Verify IP is now in database ip_blacklist
        is_blocked, reason = database.is_ip_blacklisted(attacker_ip)
        self.assertTrue(is_blocked, "Attacker IP must be auto-blacklisted by WAF")
        self.assertIn("SQL Injection", reason)
        
        # Clean up
        database.unblock_ip(attacker_ip)

    def test_02_waf_path_traversal_auto_jail(self):
        """Test that WAF intercepts Path Traversal attack in query and auto-blacklists IP."""
        attacker_ip = "198.51.100.55"
        database.unblock_ip(attacker_ip)
        
        res = self.client.get(
            "/api/csrf-token?file=../../../../etc/passwd",
            environ_overrides={'REMOTE_ADDR': attacker_ip}
        )
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data.get("error"), "waf_blocked")
        
        is_blocked, reason = database.is_ip_blacklisted(attacker_ip)
        self.assertTrue(is_blocked)
        self.assertIn("Path Traversal", reason)
        
        database.unblock_ip(attacker_ip)

    def test_03_session_versioning_and_multi_device_invalidation(self):
        """Test that changing password bumps session_version and invalidates other sessions."""
        test_user = "sec_test_user_sess"
        database.admin_create_user(test_user, "P@ssw0rd123!", role="user")
        
        # Device 1 Session (Old version: 1)
        with self.client.session_transaction() as sess:
            sess["user"] = test_user
            sess["role"] = "user"
            sess["org_id"] = 1
            sess["session_version"] = database.get_user_session_version(test_user)
            sess["_csrf_token"] = "valid_csrf_token_test_123"

        # Valid request passes
        res1 = self.client.get("/api/user/profile", headers={"X-CSRF-Token": "valid_csrf_token_test_123"})
        self.assertIn(res1.status_code, (200, 404)) # Not 401 session_revoked

        # Now simulate password reset on Device 2
        database.increment_user_session_version(test_user)

        # Now Device 1 sends next request -> Must be revoked with 401
        res2 = self.client.get("/api/user/profile", headers={"X-CSRF-Token": "valid_csrf_token_test_123"})
        self.assertEqual(res2.status_code, 401)
        data2 = res2.get_json()
        self.assertEqual(data2.get("error"), "session_revoked")

    def test_04_password_complexity_enforcement(self):
        """Test password policy helper enforces minimum 8 chars, mixed case, number, and symbols."""
        from routes.auth import validate_password_strength
        
        # Too short
        ok, msg = validate_password_strength("123456")
        self.assertFalse(ok)
        
        # Missing uppercase / symbols
        ok, msg = validate_password_strength("password123")
        self.assertFalse(ok)
        
        # Strong password
        ok, msg = validate_password_strength("StrongP@ssw0rd2026!")
        self.assertTrue(ok)

if __name__ == '__main__':
    unittest.main()
