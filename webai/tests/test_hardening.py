# -*- coding: utf-8 -*-
"""
webai/tests/test_hardening.py — regression tests for production hardening:
LINE webhook signature, Stripe webhook signature, CORS-in-production, Kanban tenant isolation.
"""
import base64
import hashlib
import hmac
import importlib
import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

from tests.test_helpers import BaseTestCase
import database
import app_server

LINE_SECRET = "unit-test-line-secret"


def _line_sig(body: bytes, secret: str = LINE_SECRET) -> str:
    return base64.b64encode(hmac.new(secret.encode(), body, hashlib.sha256).digest()).decode()


class TestLineSignature(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        app_server.app.config["TESTING"] = True
        cls.client = app_server.app.test_client()

    def _patched(self):
        import routes.line_webhook as lw
        return mock.patch.object(lw, "get_line_config", return_value={"channel_secret": LINE_SECRET})

    def test_valid_signature_accepted(self):
        import routes.line_webhook as lw
        body = b'{"events": []}'
        with self._patched():
            self.assertTrue(lw.verify_line_signature(body, _line_sig(body)))

    def test_wrong_or_tampered_signature_rejected(self):
        import routes.line_webhook as lw
        body = b'{"events": []}'
        with self._patched():
            self.assertFalse(lw.verify_line_signature(body, _line_sig(body, "other-secret")))
            self.assertFalse(lw.verify_line_signature(b'{"events": [1]}', _line_sig(body)))
            self.assertFalse(lw.verify_line_signature(body, ""))
            self.assertFalse(lw.verify_line_signature(body, None))

    def test_missing_secret_rejects_everything(self):
        import routes.line_webhook as lw
        body = b"{}"
        with mock.patch.object(lw, "get_line_config", return_value={}), \
                mock.patch.dict(os.environ, {"LINE_CHANNEL_SECRET": ""}):
            self.assertFalse(lw.verify_line_signature(body, _line_sig(body)))

    def test_endpoint_rejects_bad_and_missing_signature(self):
        body = b'{"events": []}'
        with self._patched():
            r = self.client.post("/api/line/webhook", data=body, content_type="application/json")
            self.assertEqual(r.status_code, 400)
            r = self.client.post("/api/line/webhook", data=body, content_type="application/json",
                                 headers={"X-Line-Signature": "bogus"})
            self.assertEqual(r.status_code, 400)


class TestStripeWebhook(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        app_server.app.config["TESTING"] = True
        cls.client = app_server.app.test_client()

    def test_invalid_signature_rejected(self):
        r = self.client.post("/api/billing/webhook", data=b"{}", content_type="application/json",
                             headers={"Stripe-Signature": "t=1,v1=bad"})
        self.assertEqual(r.status_code, 400)

    def test_missing_webhook_secret_rejected(self):
        import payment
        with mock.patch.object(payment, "WEBHOOK_SECRET", ""):
            with self.assertRaises(ValueError):
                payment.construct_webhook_event(b"{}", "t=1,v1=x")

    def test_validly_signed_event_passes_verification(self):
        import payment
        payload = json.dumps({"id": "evt_test", "object": "event", "type": "ping",
                              "data": {"object": {}}}).encode()
        ts = "1700000000"
        secret = "whsec_unit_test"
        sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
        with mock.patch.object(payment, "WEBHOOK_SECRET", secret), \
                mock.patch("time.time", return_value=int(ts)):
            event = payment.construct_webhook_event(payload, f"t={ts},v1={sig}")
        self.assertEqual(event["id"], "evt_test")


class TestCorsProduction(unittest.TestCase):
    def _build(self, env):
        import routes.shared as shared
        with mock.patch.dict(os.environ, env, clear=False):
            for k in ("CORS_ALLOWED_ORIGINS", "BASE_URL", "APP_ENV", "FLASK_ENV",
                      "RAILWAY_ENVIRONMENT", "RAILWAY_ENVIRONMENT_NAME", "RAILWAY_STATIC_URL"):
                if k not in env:
                    os.environ.pop(k, None)
            return shared._build_cors_origins()

    def test_production_without_base_url_fails(self):
        with self.assertRaises(RuntimeError):
            self._build({"APP_ENV": "production"})

    def test_production_wildcard_fails(self):
        with self.assertRaises(RuntimeError):
            self._build({"APP_ENV": "production", "CORS_ALLOWED_ORIGINS": "*"})

    def test_railway_is_treated_as_production(self):
        with self.assertRaises(RuntimeError):
            self._build({"RAILWAY_ENVIRONMENT": "production"})

    def test_production_with_base_url_ok(self):
        self.assertEqual(self._build({"APP_ENV": "production", "BASE_URL": "https://a.example/"}),
                         ["https://a.example"])

    def test_dev_fallback_still_wildcard(self):
        self.assertEqual(self._build({"APP_ENV": "development"}), "*")


class TestKanbanTenantIsolation(BaseTestCase):
    def test_get_column_never_returns_other_orgs_or_fake_columns(self):
        a = database.kanban_add_column("A-col", org_id=101)
        b = database.kanban_add_column("B-col", org_id=202)
        self.assertEqual(database.kanban_get_column(a, org_id=101)["title"], "A-col")
        self.assertIsNone(database.kanban_get_column(b, org_id=101))
        self.assertIsNone(database.kanban_get_column(999999, org_id=101))

    def test_update_card_keeps_labels_and_color(self):
        col = database.kanban_add_column("c", org_id=101)
        cid = database.kanban_add_card(col, "t")
        database.kanban_update_card(cid, labels="bug", color="#fff")
        card = database.kanban_get_card(cid)
        self.assertEqual(card["labels"], "bug")
        self.assertEqual(card["color"], "#fff")


class TestLineFlexSplit(unittest.TestCase):
    """routes/line_flex.py was split out of line_webhook.py — old import paths must keep working."""
    def test_reexports_are_same_objects(self):
        import routes.line_flex as flex
        import routes.line_webhook as lw
        import routes.chat as chat
        for name in ("create_expense_flex_bubble", "create_leave_approval_flex_bubble",
                     "clean_flex_payload", "extract_smart_amount"):
            self.assertIs(getattr(lw, name), getattr(flex, name))
            if hasattr(chat, name):
                self.assertIs(getattr(chat, name), getattr(flex, name))

    def test_extract_smart_amount(self):
        from routes.line_flex import extract_smart_amount
        self.assertEqual(extract_smart_amount({"net_amount": "1,250.50"}), 1250.5)


if __name__ == "__main__":
    unittest.main()
