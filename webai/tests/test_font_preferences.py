# -*- coding: utf-8 -*-
"""
webai/tests/test_font_preferences.py — User UI & Font Preferences Verification
Tests:
1. Database schema migration: ui_font, ui_font_size, ui_accent columns in user_settings
2. get_user_ui_prefs and set_user_ui_prefs functions
3. Strict allowlist validation against CSS injection / XSS attacks
4. Per-user isolation (User A choosing Kanit does not alter User B)
5. Route POST /api/profile/ui-prefs requires login (401 when unauthenticated)
6. Route POST /api/profile/ui-prefs updates preferences for authenticated user
7. Route GET /api/me returns ui_prefs
"""

import sys
import unittest
from pathlib import Path

WEBAI_DIR = Path(__file__).resolve().parent.parent
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

from tests.test_helpers import BaseTestCase
import database
from app_server import app


class TestFontPreferences(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.client = app.test_client()

    def test_schema_has_ui_preference_columns(self):
        """Test that user_settings table has ui_font, ui_font_size, and ui_accent columns."""
        conn = database._get_conn()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        self.assertIn("ui_font", columns)
        self.assertIn("ui_font_size", columns)
        self.assertIn("ui_accent", columns)

    def test_set_and_get_user_ui_prefs(self):
        """Test setting and retrieving valid UI preferences for a user."""
        username = "alice_designer"
        ok, msg = database.set_user_ui_prefs(
            username=username,
            font="Kanit",
            size="large",
            accent="emerald"
        )
        self.assertTrue(ok, f"Failed to set ui prefs: {msg}")

        prefs = database.get_user_ui_prefs(username)
        self.assertEqual(prefs["font"], "Kanit")
        self.assertEqual(prefs["size"], "large")
        self.assertEqual(prefs["accent"], "emerald")

    def test_user_isolation(self):
        """Test that preferences are isolated per user (User A != User B)."""
        user_a = "user_kanit"
        user_b = "user_mitr"

        database.set_user_ui_prefs(user_a, font="Kanit", size="xl", accent="purple")
        database.set_user_ui_prefs(user_b, font="Mitr", size="small", accent="amber")

        prefs_a = database.get_user_ui_prefs(user_a)
        prefs_b = database.get_user_ui_prefs(user_b)

        self.assertEqual(prefs_a["font"], "Kanit")
        self.assertEqual(prefs_a["size"], "xl")
        self.assertEqual(prefs_a["accent"], "purple")

        self.assertEqual(prefs_b["font"], "Mitr")
        self.assertEqual(prefs_b["size"], "small")
        self.assertEqual(prefs_b["accent"], "amber")

    def test_allowlist_rejection_for_injection_attempts(self):
        """Test strict rejection of invalid or malicious inputs (CSS injection prevention)."""
        malicious_inputs = [
            "x;}body{display:none",
            "Kanit'; DROP TABLE users; --",
            "<script>alert(1)</script>",
            "Comic Sans MS",
            "Wingdings"
        ]

        for bad_font in malicious_inputs:
            ok, err = database.set_user_ui_prefs("attacker", font=bad_font)
            self.assertFalse(ok, f"Should have rejected bad font: {bad_font}")
            self.assertIn("Invalid font", err)

        # Malicious size
        ok, err = database.set_user_ui_prefs("attacker", size="huge-font; font-size: 1000px;")
        self.assertFalse(ok)
        self.assertIn("Invalid font size", err)

        # Malicious accent
        ok, err = database.set_user_ui_prefs("attacker", accent="red-alert-injection")
        self.assertFalse(ok)
        self.assertIn("Invalid accent color", err)

    def _get_csrf_headers(self):
        res = self.client.get("/api/csrf-token")
        csrf = res.get_json().get("csrf_token") if res.status_code == 200 else ""
        return {"X-CSRF-Token": csrf}

    def test_unauthenticated_api_returns_401(self):
        """Calling /api/profile/ui-prefs without authentication must return 401."""
        res = self.client.post("/api/profile/ui-prefs", json={"font": "Kanit"})
        self.assertEqual(res.status_code, 401)

    def test_authenticated_api_updates_prefs(self):
        """Authenticated user can update their UI preferences via API."""
        with self.client.session_transaction() as sess:
            sess["user"] = "bob_tester"
            sess["role"] = "user"

        headers = self._get_csrf_headers()
        res = self.client.post(
            "/api/profile/ui-prefs",
            json={"font": "Prompt", "size": "normal", "accent": "blue"},
            headers=headers
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data["ui_prefs"]["font"], "Prompt")
        self.assertEqual(data["ui_prefs"]["size"], "normal")
        self.assertEqual(data["ui_prefs"]["accent"], "blue")

        # Verify GET /api/profile/ui-prefs
        get_res = self.client.get("/api/profile/ui-prefs")
        self.assertEqual(get_res.status_code, 200)
        get_data = get_res.get_json()
        self.assertEqual(get_data["ui_prefs"]["font"], "Prompt")

    def test_api_me_returns_ui_prefs(self):
        """Verify that /api/me returns user's ui_prefs."""
        username = "carol_user"
        database.set_user_ui_prefs(username, font="Chakra Petch", size="xl", accent="rose")

        with self.client.session_transaction() as sess:
            sess["user"] = username
            sess["role"] = "user"

        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        self.assertIn("ui_prefs", data)
        self.assertEqual(data["ui_prefs"]["font"], "Chakra Petch")
        self.assertEqual(data["ui_prefs"]["size"], "xl")
        self.assertEqual(data["ui_prefs"]["accent"], "rose")

    def test_api_rejects_invalid_font_with_400(self):
        """Verify that API rejects invalid font with HTTP 400."""
        with self.client.session_transaction() as sess:
            sess["user"] = "hacker_test"
            sess["role"] = "user"

        headers = self._get_csrf_headers()
        res = self.client.post(
            "/api/profile/ui-prefs",
            json={"font": "evil-font-family;}</style>"},
            headers=headers
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data.get("ok"))


if __name__ == "__main__":
    unittest.main()
