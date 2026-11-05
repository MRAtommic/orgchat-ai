# -*- coding: utf-8 -*-
"""
webai/tests/test_stripe_flow.py — business logic of /api/billing/webhook
(signature verification is covered in test_hardening.py; here the event is trusted and mocked).
"""
import sys
import uuid
import unittest
from pathlib import Path
from unittest import mock

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

from tests.test_helpers import BaseTestCase
import app_server


class _Event(dict):
    @property
    def id(self):
        return self["id"]


def _event(etype, obj, eid=None):
    return _Event(id=eid or f"evt_{uuid.uuid4().hex}", type=etype, data={"object": obj})


class TestStripeWebhookFlow(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        app_server.app.config["TESTING"] = True
        cls.client = app_server.app.test_client()

    def _post(self, event, org_exists=True):
        import payment, billing, database
        with mock.patch.object(payment, "construct_webhook_event", return_value=event), \
                mock.patch.object(database, "get_org_by_id", return_value={"id": 7} if org_exists else None), \
                mock.patch.object(database, "set_org_stripe_info") as stripe_info, \
                mock.patch.object(billing, "set_org_plan") as set_plan:
            r = self.client.post("/api/billing/webhook", data=b"{}",
                                 headers={"Stripe-Signature": "x"})
        return r, set_plan, stripe_info

    def test_promptpay_checkout_activates_plan(self):
        ev = _event("checkout.session.completed", {
            "id": "cs_1", "customer": "cus_1", "subscription": None,
            "metadata": {"org_id": "7", "plan": "pro", "payment_type": "promptpay", "days": "30"}})
        r, set_plan, info = self._post(ev)
        self.assertEqual(r.status_code, 200)
        set_plan.assert_called_once()
        self.assertEqual(set_plan.call_args[0][:2], (7, "pro"))
        info.assert_called_once()

    def test_duplicate_event_processed_once(self):
        ev = _event("checkout.session.completed", {
            "id": "cs_2", "customer": "cus_1", "subscription": None,
            "metadata": {"org_id": "7", "plan": "pro", "payment_type": "promptpay"}}, eid=f"evt_dup_{uuid.uuid4().hex}")
        _, first, _ = self._post(ev)
        r, second, _ = self._post(ev)
        self.assertEqual(r.status_code, 200)
        first.assert_called_once()
        second.assert_not_called()

    def test_invalid_plan_is_ignored(self):
        for plan in ("free", "enterprise-nonexistent", ""):
            ev = _event("checkout.session.completed", {
                "id": "cs_3", "metadata": {"org_id": "7", "plan": plan, "payment_type": "promptpay"}})
            r, set_plan, _ = self._post(ev)
            self.assertEqual(r.status_code, 200)
            set_plan.assert_not_called()

    def test_missing_org_id_or_unknown_org_ignored(self):
        ev = _event("checkout.session.completed", {"id": "cs_4", "metadata": {"plan": "pro"}})
        r, set_plan, _ = self._post(ev)
        self.assertEqual(r.status_code, 200)
        set_plan.assert_not_called()
        ev = _event("checkout.session.completed", {
            "id": "cs_5", "metadata": {"org_id": "7", "plan": "pro", "payment_type": "promptpay"}})
        r, set_plan, _ = self._post(ev, org_exists=False)
        self.assertEqual(r.status_code, 200)
        set_plan.assert_not_called()

    def test_canceled_subscription_downgrades_to_free(self):
        ev = _event("customer.subscription.updated", {
            "id": "sub_1", "status": "canceled", "customer": "cus_1",
            "metadata": {"org_id": "7", "plan": "pro"}})
        with mock.patch("routes.admin._notify_plan_downgrade_line"):
            r, set_plan, _ = self._post(ev)
        self.assertEqual(r.status_code, 200)
        set_plan.assert_called_once_with(7, "free")


if __name__ == "__main__":
    unittest.main()
