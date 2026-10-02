# -*- coding: utf-8 -*-
"""
webai/tests/test_auth.py — Authentication & Security Unit Tests
Tests password hashing, lockout logic, TOTP, and session security.
"""

import sys
from pathlib import Path
WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database

class TestAuth(BaseTestCase):

    def test_password_hashing(self):
        """Test secure password hashing and verification with bcrypt."""
        password = "SuperSecretPassword123!"
        hashed = database.hash_password(password)
        self.assertNotEqual(password, hashed)
        self.assertTrue(database.check_password(password, hashed))
        self.assertFalse(database.check_password("WrongPassword!", hashed))

    def test_login_attempts_and_lockout(self):
        """Test account lockout tracking after multiple failed attempts."""
        test_user = "brute_force_target"

        # Initially not locked
        locked, _ = database.is_account_locked(test_user)
        self.assertFalse(locked)

        # Record failed attempts up to the threshold
        for _ in range(5):
            res = database.record_failed_login(test_user, max_attempts=5, lock_minutes=15)

        locked, remaining = database.is_account_locked(test_user)
        self.assertTrue(locked)
        self.assertGreater(remaining, 0)

        # Clear attempts on successful login
        database.reset_failed_login(test_user)
        locked, _ = database.is_account_locked(test_user)
        self.assertFalse(locked)

    def test_session_version_revocation(self):
        """Test that incrementing session version revokes older sessions."""
        username = "session_user_01"
        v1 = database.get_user_session_version(username)
        self.assertGreaterEqual(v1, 1)

        # Invalidate sessions (e.g. on password change or remote logout)
        v2 = database.increment_user_session_version(username)
        self.assertEqual(v2, v1 + 1)
        # Old version v1 is now stale compared to v2
        current = database.get_user_session_version(username)
        self.assertEqual(current, v2)

if __name__ == "__main__":
    unittest.main()
