"""
Automated Security Unit & Integration Verification Tests for OrgChat AI
Run this script to verify defensive measures against common web vulnerabilities.
Usage:
    python test_security_defenses.py
"""
import sys
import unittest
import os

# Set environment
os.environ["FLASK_ENV"] = "testing"

try:
    from app_server import create_app
    import database
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_server import create_app
    import database


class SecurityDefensesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_security_headers_present(self):
        """Verify that mandatory HTTP security headers are included in all responses."""
        response = self.client.get("/")
        headers = response.headers
        
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(headers.get("X-Permitted-Cross-Domain-Policies"), "none")
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(headers.get("Server"), "OrgChat-Shield")

    def test_csrf_protection_on_mutating_requests(self):
        """Verify that state-changing POST requests without CSRF token are blocked."""
        with self.client.session_transaction() as sess:
            sess["user"] = "test_sec_user"
            sess["org_id"] = 1

        # Attempt POST without X-CSRF-Token header
        response = self.client.post("/api/posts", json={"display_name": "Attacker"})
        self.assertEqual(response.status_code, 403)
        data = response.get_json()
        self.assertFalse(data.get("ok"))
        self.assertEqual(data.get("error"), "csrf_invalid")

    def test_session_user_agent_fingerprint_protection(self):
        """Verify that changing User-Agent invalidates the session (Session Hijacking defense)."""
        with self.client.session_transaction() as sess:
            sess["user"] = "test_sec_user"
            sess["org_id"] = 1

        # Request 1 with Firefox UA
        res1 = self.client.get("/api/posts", headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/120.0"})
        
        # Request 2 with Chrome UA using the same session
        res2 = self.client.get("/api/posts", headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/120.0"})
        self.assertEqual(res2.status_code, 401)
        data2 = res2.get_json()
        self.assertEqual(data2.get("error"), "session_hijack_detected")

    def test_unauthenticated_api_access_blocked(self):
        """Verify that protected API endpoints return 401 when accessed without session."""
        response = self.client.get("/api/posts")
        self.assertIn(response.status_code, (401, 302, 403))

    def test_password_hashing_security(self):
        """Verify that password hashing uses bcrypt and rejects plaintext match."""
        password = "SecurePassword123!"
        hashed = database.hash_password(password)
        
        # Must be bcrypt hash starting with $2b$ or $2a$
        self.assertTrue(hashed.startswith("$2b$") or hashed.startswith("$2a$"))
        
        # Correct password matches
        self.assertTrue(database.check_password(password, hashed))
        
        # Wrong password fails
        self.assertFalse(database.check_password("WrongPassword123!", hashed))
        
        # Plaintext stored hash comparison must be rejected
        self.assertFalse(database.check_password("plain", "plain"))


    def test_line_webhook_signature_verification(self):
        """Verify LINE Webhook signature validation logic against spoofed payloads."""
        import hmac, hashlib, base64
        from routes.chat import verify_line_signature, LINE_CONFIG_FILE
        
        secret = "test_line_secret_12345"
        payload = b'{"events":[{"type":"message"}]}'
        
        # Calculate valid signature
        hash_obj = hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).digest()
        valid_sig = base64.b64encode(hash_obj).decode('utf-8')
        
        # Temporarily hide line_config.json if it exists to force fallback to os.environ
        temp_renamed = False
        if os.path.exists(LINE_CONFIG_FILE):
            try:
                os.rename(LINE_CONFIG_FILE, LINE_CONFIG_FILE + ".bak_test")
                temp_renamed = True
            except Exception:
                pass

        os.environ["LINE_CHANNEL_SECRET"] = secret
        try:
            # Valid signature must pass
            self.assertTrue(verify_line_signature(payload, valid_sig))
            # Invalid signature must be rejected
            self.assertFalse(verify_line_signature(payload, "invalid_forged_signature_xyz"))
        finally:
            os.environ.pop("LINE_CHANNEL_SECRET", None)
            if temp_renamed and os.path.exists(LINE_CONFIG_FILE + ".bak_test"):
                try:
                    os.rename(LINE_CONFIG_FILE + ".bak_test", LINE_CONFIG_FILE)
                except Exception:
                    pass

    def test_org_admin_permission_isolation(self):
        """Verify non-org-admin users are forbidden (403) from accessing admin endpoints."""
        with self.client.session_transaction() as sess:
            sess["user"] = "regular_employee"
            sess["org_id"] = 1
            sess["is_admin"] = False
            sess["is_org_admin"] = False

        # Regular user accessing admin leave requests
        res = self.client.get("/api/admin/leave/all")
        self.assertIn(res.status_code, (403, 401))

    def test_sql_injection_defense_parameterization(self):
        """Verify database query helpers handle SQL injection payloads safely without syntax error."""
        malicious_input = "' OR '1'='1' -- "
        # Check leave query with malicious string — should return empty list safely without syntax error
        leaves = database.get_user_leaves(malicious_input)
        self.assertEqual(leaves, [])

    def test_json_content_type_enforcement(self):
        """Verify API endpoints respond with application/json Content-Type header."""
        res = self.client.get("/api/ping")
        self.assertIn("application/json", res.headers.get("Content-Type", ""))

    def test_kanban_board_unauthenticated_isolation(self):
        """Verify kanban board API requires session authentication."""
        res = self.client.get("/api/kanban/board")
        self.assertIn(res.status_code, (401, 302, 403))


if __name__ == "__main__":
    print("==========================================================")
    print(" Running Security Defenses Automated Verification Test Suite")
    print("==========================================================")
    unittest.main()

