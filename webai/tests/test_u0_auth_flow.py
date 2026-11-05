import unittest
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tests.test_helpers import BaseTestCase
from app_server import create_app
import database


class TestU0AuthFlow(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ["TESTING"] = "1"
        os.environ["FLASK_SECRET_KEY"] = "test-secret-key-for-u0-auth-flow-32b"
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.app.config["WTF_CSRF_ENABLED"] = False

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.client = self.app.test_client()

    def test_ua_minor_version_change_does_not_wipe_session(self):
        """U0-1: Minor browser update or minor version drift does not invalidate session."""
        ua_v1 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.109 Safari/537.36"
        ua_v2 = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.215 Safari/537.36"

        with self.client.session_transaction() as sess:
            sess["user"] = "testuser_u0"
            sess["role"] = "user"
            sess["org_id"] = 1
            sess["org_role"] = "member"

        # Request 1 with ua_v1
        res1 = self.client.get("/api/me", headers={"User-Agent": ua_v1})
        self.assertEqual(res1.status_code, 200)

        # Request 2 with ua_v2 (minor version change)
        res2 = self.client.get("/api/me", headers={"User-Agent": ua_v2})
        self.assertEqual(res2.status_code, 200, "Minor Chrome version update must not wipe session")

    def test_ua_different_os_or_browser_triggers_session_hijack_defense(self):
        """U0-1: Cross-platform / cross-browser session reuse is blocked."""
        ua_desktop = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ua_mobile = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1"

        with self.client.session_transaction() as sess:
            sess["user"] = "testuser_u0_hijack"
            sess["role"] = "user"
            sess["org_id"] = 1
            sess["org_role"] = "member"

        # Establish session on Desktop
        res1 = self.client.get("/api/me", headers={"User-Agent": ua_desktop})
        self.assertEqual(res1.status_code, 200)

        # Subsequent request from Mobile iPhone with stolen session cookie
        res2 = self.client.get("/api/me", headers={"User-Agent": ua_mobile})
        self.assertEqual(res2.status_code, 401)
        data = res2.get_json()
        self.assertEqual(data.get("error"), "session_hijack_detected")
        self.assertIn("ตรวจพบการเข้าสู่ระบบจากอุปกรณ์หรือเบราว์เซอร์อื่น", data.get("message", ""))

    def test_org_signup_then_immediate_authenticated_navigation(self):
        """U0-1: Signing up automatically sets a valid session that navigates to home without 401."""
        rnd = os.urandom(4).hex()
        username = f"u0_user_{rnd}"
        org_name = f"U0 Org {rnd}"
        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

        # 1. POST signup
        res = self.client.post("/api/org/signup", json={
            "org_name": org_name,
            "username": username,
            "display_name": "U0 Tester",
            "password": "Password1234!",
            "confirm_password": "Password1234!"
        }, headers={"User-Agent": ua})

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data.get("ok"))

        # 2. Subsequent navigation /api/me works with same UA
        res_me = self.client.get("/api/me", headers={"User-Agent": ua})
        self.assertEqual(res_me.status_code, 200)
        me_data = res_me.get_json()
        self.assertEqual(me_data.get("user"), username)


    def test_decode_jwt_payload_unverified(self):
        """Verify unverified JWT payload decoder correctly parses claims without pyjwt."""
        from routes.auth import _decode_jwt_payload_unverified
        import base64
        import json
        header = base64.urlsafe_b64encode(json.dumps({"alg": "none"}).encode()).decode().rstrip("=")
        payload = base64.urlsafe_b64encode(json.dumps({
            "sub": "U1234567890",
            "email": "mxmm2547@gmail.com",
            "name": "Few"
        }).encode()).decode().rstrip("=")
        fake_jwt = f"{header}.{payload}."
        
        claims = _decode_jwt_payload_unverified(fake_jwt)
        self.assertEqual(claims.get("email"), "mxmm2547@gmail.com")
        self.assertEqual(claims.get("sub"), "U1234567890")

    def test_line_login_matches_existing_account_by_email(self):
        """Verify LINE login callback matches existing user account by email and binds new line_user_id."""
        from unittest.mock import patch, MagicMock
        from routes.auth import _store_oauth_state
        import base64
        import json

        rnd = os.urandom(4).hex()
        uname = f"exuser_{rnd}"
        uemail = f"user_{rnd}@example.com"
        newline_id = f"U_line_{rnd}"
        
        # 1. Create existing user with email in DB
        database.admin_create_user(
            username=uname,
            password="Password123!",
            role="superadmin",
            display_name="Existing Superadmin",
            email=uemail
        )
        
        # 2. Store OAuth state
        state_key = f"st_{rnd}"
        _store_oauth_state(f"line_{state_key}", {"username": None, "mode": "login"})
        
        # 3. Create mock id_token with email
        h = base64.urlsafe_b64encode(b'{"alg":"none"}').decode().rstrip("=")
        p = base64.urlsafe_b64encode(json.dumps({"sub": newline_id, "email": uemail}).encode()).decode().rstrip("=")
        id_token = f"{h}.{p}."

        mock_token_resp = MagicMock()
        mock_token_resp.status_code = 200
        mock_token_resp.json.return_value = {
            "access_token": "mock_access_token",
            "id_token": id_token
        }

        mock_prof_resp = MagicMock()
        mock_prof_resp.status_code = 200
        mock_prof_resp.json.return_value = {
            "userId": newline_id,
            "displayName": "Few From LINE"
        }

        with patch("routes.auth._get_line_login_config", return_value={"channel_id": "123456", "channel_secret": "sec"}), \
             patch("routes.auth._get_line_http_session") as mock_http_fn:
            mock_session = MagicMock()
            mock_session.post.return_value = mock_token_resp
            mock_session.get.return_value = mock_prof_resp
            mock_http_fn.return_value = mock_session

            res = self.client.get(f"/api/line/login-callback?code=mock_code&state={state_key}")
            self.assertEqual(res.status_code, 302)

            # 4. Assert session is logged into the existing account
            with self.client.session_transaction() as sess:
                self.assertEqual(sess.get("user"), uname)
                self.assertEqual(sess.get("role"), "superadmin")

            # 5. Assert database linked the LINE ID to existing account
            linked_user = database.get_username_by_line_id(newline_id)
            self.assertEqual(linked_user, uname)


    def test_login_with_username_or_email_accesses_same_account(self):
        """Verify user can log in with username OR email and both enter the exact same canonical account."""
        rnd = os.urandom(4).hex()
        uname = f"dual_user_{rnd}"
        uemail = f"dual_{rnd}@company.com"
        upassword = "SecurePassword123!"

        # Create user
        database.admin_create_user(
            username=uname,
            password=upassword,
            role="admin",
            display_name="Dual Login User",
            email=uemail
        )

        ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"

        # 1. Login with Username
        res_by_name = self.client.post("/api/login", json={
            "username": uname,
            "password": upassword
        }, headers={"User-Agent": ua})
        self.assertEqual(res_by_name.status_code, 200)
        data_by_name = res_by_name.get_json()
        self.assertTrue(data_by_name.get("ok"))
        self.assertEqual(data_by_name.get("user"), uname)

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user"), uname)

        # Logout
        self.client.post("/api/logout")

        # 2. Login with Email
        res_by_email = self.client.post("/api/login", json={
            "username": uemail,
            "password": upassword
        }, headers={"User-Agent": ua})
        self.assertEqual(res_by_email.status_code, 200)
        data_by_email = res_by_email.get_json()
        self.assertTrue(data_by_email.get("ok"))
        self.assertEqual(data_by_email.get("user"), uname, "Must resolve to canonical username, not create separate account")

        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get("user"), uname)

        # 3. Verify no phantom account was created for the email address in user_settings
        conn = database._get_conn()
        c = conn.cursor()
        c.execute("SELECT 1 FROM user_settings WHERE username = ?", (uemail,))
        phantom = c.fetchone()
        conn.close()
        self.assertIsNone(phantom, "Login by email must never create a phantom user_settings row for the email")


if __name__ == '__main__':
    unittest.main()
