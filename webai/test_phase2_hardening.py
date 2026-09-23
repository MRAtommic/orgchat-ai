# -*- coding: utf-8 -*-
"""
Phase 2 Hardening & Multi-Scenario Bug Verification Suite
Tests:
  1. Kanban column reindexing & multi-tenant column reordering
  2. Multi-tenant chat directory isolation (no cross-tenant leakage of default org users)
  3. 2FA disable security authorization (cannot bypass with empty password on OAuth/passwordless users)
  4. LINE notifications & bot_enabled filtering for organizations
  5. Inactive user filtering in LINE username & ID mapping
  6. DynamicConnectionWrapper RAII resource management & idempotency
  7. Admin API defensive handling on empty / malformed request bodies
"""
import unittest
import json
import sqlite3
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import database
from app_server import app


class TestPhase2Hardening(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()

    def test_01_kanban_move_and_reorder(self):
        """Verify kanban_move_card performs proper reindexing and kanban_reorder_columns respects org_id."""
        conn = database._get_conn()
        cur = conn.cursor()
        # Create temporary columns and cards
        cur.execute("INSERT INTO kanban_columns (title, position, org_id) VALUES ('Col A', 0, 999)")
        col_a = cur.lastrowid
        cur.execute("INSERT INTO kanban_columns (title, position, org_id) VALUES ('Col B', 1, 999)")
        col_b = cur.lastrowid
        
        cur.execute("INSERT INTO kanban_cards (column_id, title, position) VALUES (?, 'Card 1', 0)", (col_a,))
        c1 = cur.lastrowid
        cur.execute("INSERT INTO kanban_cards (column_id, title, position) VALUES (?, 'Card 2', 1)", (col_a,))
        c2 = cur.lastrowid
        conn.commit()
        conn.close()

        try:
            # Move Card 2 into Col B at position 0
            ok = database.kanban_move_card(c2, col_b, 0)
            self.assertTrue(ok)

            card2 = database.kanban_get_card(c2)
            self.assertEqual(card2["column_id"], col_b)
            self.assertEqual(card2["position"], 0)

            # Reorder columns with org_id filter
            database.kanban_reorder_columns([
                {"id": col_a, "position": 1},
                {"id": col_b, "position": 0}
            ], org_id=999)

            conn = database._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT position FROM kanban_columns WHERE id = ?", (col_b,))
            pos_b = cur.fetchone()[0]
            self.assertEqual(pos_b, 0)
            conn.close()

        finally:
            conn = database._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM kanban_cards WHERE id IN (?, ?)", (c1, c2))
            cur.execute("DELETE FROM kanban_columns WHERE id IN (?, ?)", (col_a, col_b))
            conn.commit()
            conn.close()

    def test_02_chat_directory_tenant_isolation(self):
        """Verify that tenant orgs (org != 1) do not have default hardcoded users injected."""
        with self.client.session_transaction() as sess:
            sess["user"] = "tenant_user_x"
            sess["role"] = "member"
            sess["org_id"] = 999  # Tenant org
            sess["_csrf_token"] = "test_token"

        res = self.client.get("/api/chat/users")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))
        usernames = [u.get("username", "").lower() for u in data.get("users", [])]
        # In tenant org 999, default org 1 users like 'mxmm2547' should NOT be leaked
        self.assertNotIn("mxmm2547", usernames)

    def test_03_2fa_disable_security(self):
        """Verify disable_2fa cannot be called without valid proof for passwordless/OAuth users."""
        conn = database._get_conn()
        cur = conn.cursor()
        # Set up a user without custom_password but with 2FA enabled
        cur.execute("""
            INSERT OR REPLACE INTO user_settings (username, totp_enabled, totp_secret, custom_password)
            VALUES ('oauth_user_test', 1, 'JBSWY3DPEHPK3PXP', NULL)
        """)
        conn.commit()
        conn.close()

        try:
            with self.client.session_transaction() as sess:
                sess["user"] = "oauth_user_test"
                sess["role"] = "user"
                sess["org_id"] = 1
                sess["_csrf_token"] = "csrf123"

            # Attempt to disable 2FA with empty password / empty code
            res = self.client.post("/api/2fa/disable", json={"password": ""}, headers={"X-CSRF-Token": "csrf123"})
            self.assertEqual(res.status_code, 400)
            data = res.get_json()
            self.assertFalse(data.get("ok"))
            self.assertIn("รหัส", data.get("error", ""))
        finally:
            conn = database._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM user_settings WHERE username = 'oauth_user_test'")
            conn.commit()
            conn.close()

    def test_04_line_group_bot_enabled_filter(self):
        """Verify get_line_groups_for_org filters out groups where bot_enabled is 0."""
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO line_group_mappings (group_id, org_id, group_name, owner_username, bot_enabled)
            VALUES ('c_test_grp_enabled', 987, 'Enabled Group', 'admin', 1)
        """)
        cur.execute("""
            INSERT INTO line_group_mappings (group_id, org_id, group_name, owner_username, bot_enabled)
            VALUES ('c_test_grp_disabled', 987, 'Disabled Group', 'admin', 0)
        """)
        conn.commit()
        conn.close()

        try:
            groups = database.get_line_groups_for_org(987, only_enabled=True)
            group_ids = [g["group_id"] for g in groups]
            self.assertIn("c_test_grp_enabled", group_ids)
            self.assertNotIn("c_test_grp_disabled", group_ids)
        finally:
            conn = database._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM line_group_mappings WHERE org_id = 987")
            conn.commit()
            conn.close()

    def test_05_line_inactive_user_filter(self):
        """Verify get_line_id_by_username ignores deactivated users."""
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO user_profiles (username, line_user_id)
            VALUES ('inactive_emp_test', 'U_inactive_12345')
        """)
        cur.execute("""
            INSERT OR REPLACE INTO user_settings (username, is_active)
            VALUES ('inactive_emp_test', 0)
        """)
        conn.commit()
        conn.close()

        try:
            line_id = database.get_line_id_by_username('inactive_emp_test')
            self.assertIsNone(line_id, "Inactive user must not resolve a line_id")

            resolved_user = database.get_username_by_line_id('U_inactive_12345')
            self.assertIsNone(resolved_user, "Inactive user must not resolve username from LINE ID")
        finally:
            conn = database._get_conn()
            cur = conn.cursor()
            cur.execute("DELETE FROM user_profiles WHERE username = 'inactive_emp_test'")
            cur.execute("DELETE FROM user_settings WHERE username = 'inactive_emp_test'")
            conn.commit()
            conn.close()

    def test_06_dynamic_connection_wrapper_raii(self):
        """Verify DynamicConnectionWrapper close is idempotent and context manager cleans up."""
        wrapper = database._get_conn()
        self.assertFalse(wrapper._closed)
        with wrapper as c:
            cur = c.execute("SELECT 1")
            self.assertEqual(cur.fetchone()[0], 1)
        # Exiting context manager closes the wrapper
        self.assertTrue(wrapper._closed)
        # Calling close again is safe and idempotent
        wrapper.close()
        self.assertTrue(wrapper._closed)

    def test_07_admin_endpoints_defensive_body_handling(self):
        """Verify admin endpoints gracefully handle empty/null bodies without 500 error."""
        with self.client.session_transaction() as sess:
            sess["user"] = "admin"
            sess["role"] = "admin"
            sess["org_id"] = 1
            sess["_csrf_token"] = "token_csrf"

        # POST /api/set_key with empty body
        res = self.client.post(
            "/api/set_key",
            data="",
            content_type="application/json",
            headers={"X-CSRF-Token": "token_csrf"}
        )
        self.assertIn(res.status_code, [400, 422])
        self.assertFalse(res.get_json().get("ok"))


if __name__ == "__main__":
    unittest.main()
