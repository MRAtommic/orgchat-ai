# -*- coding: utf-8 -*-
"""
webai/tests/test_security_cso.py — CSO Security Audit & WAF Defense Tests
Validates WAF Auto-Jail, HTTP Security Headers, and Access Controls.
"""

import sys
from pathlib import Path
WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database
import app_server

class TestSecurityCSO(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.app = app_server.app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()

    def test_waf_sqli_defense(self):
        """Verify WAF detects and blocks SQL Injection payload with HTTP 403."""
        resp = self.client.get('/?q=1%20UNION%20SELECT%20NULL--')
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json() or {}
        self.assertEqual(data.get("error"), "waf_blocked")

    def test_waf_path_traversal_defense(self):
        """Verify WAF detects and blocks Path Traversal / LFI payloads."""
        resp = self.client.get('/?file=../../../../etc/passwd')
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json() or {}
        self.assertEqual(data.get("error"), "waf_blocked")

    def test_waf_xss_rce_defense(self):
        """Verify WAF detects and blocks inline script injection."""
        resp = self.client.get('/?name=%3Cscript%3Ealert(document.cookie)%3C/script%3E')
        self.assertEqual(resp.status_code, 403)
        data = resp.get_json() or {}
        self.assertEqual(data.get("error"), "waf_blocked")

    def test_security_headers_enforced(self):
        """Verify strict OWASP security headers on responses."""
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertIn("Content-Security-Policy", resp.headers)

    def test_unauthorized_admin_access_rejected(self):
        """Verify unauthenticated requests to protected admin endpoints are denied."""
        resp = self.client.get('/api/admin/users')
        self.assertIn(resp.status_code, [401, 403, 302])

if __name__ == "__main__":
    unittest.main()
