# -*- coding: utf-8 -*-
"""
webai/tests/test_finance.py — Finance, Slip Upload & Offline Queue Unit Tests
Tests expense claim creation, offline upload syncing, and file SHA-256 integrity verification.
"""

import os
import sys
import tempfile
from pathlib import Path

WEBAI_DIR = Path(__file__).parent.parent.absolute()
if str(WEBAI_DIR) not in sys.path:
    sys.path.insert(0, str(WEBAI_DIR))

import unittest
from tests.test_helpers import BaseTestCase
import database

class TestFinance(BaseTestCase):

    def test_expense_claim_creation(self):
        """Test adding an expense claim record."""
        claim_id = database.add_expense_claim(
            line_user_id="U1234567890",
            username="employee_01",
            vendor="Office Depot",
            amount="1500.00",
            expense_date="2026-03-15",
            file_link="https://drive.google.com/test_slip.jpg"
        )
        self.assertIsNotNone(claim_id)

    def test_offline_upload_queue_lifecycle(self):
        """Test adding an upload to offline queue and marking it synced."""
        upload_id = database.add_offline_upload(
            org_id=1,
            username="employee_01",
            original_filename="slip_001.jpg",
            local_filepath="/tmp/slip_001.jpg",
            mimetype="image/jpeg",
            verification_status="verified"
        )
        self.assertIsNotNone(upload_id)

        # Check pending queue
        pending = database.get_pending_offline_uploads(limit=10)
        self.assertTrue(any(p.get("id") == upload_id for p in pending))

        # Mark as synced
        database.update_offline_upload_status(
            upload_id=upload_id,
            sync_status="synced",
            drive_link="https://drive.google.com/uploaded_slip_001.jpg",
            sheets_row=12
        )

        # Ensure it is no longer pending
        pending_after = database.get_pending_offline_uploads(limit=10)
        self.assertFalse(any(p.get("id") == upload_id for p in pending_after))

    def test_file_integrity_verification(self):
        """Test file registration and SHA-256 tamper-evident integrity check."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f:
            f.write(b"%PDF-1.4 test slip content for integrity check")
            f_path = f.name

        try:
            # Register file
            registered = database.register_file_integrity(f_path, category="slips")
            self.assertTrue(registered)

            # Verify untampered file
            valid, msg = database.verify_file_integrity(f_path)
            self.assertTrue(valid)

            # Tamper file content
            with open(f_path, "ab") as f:
                f.write(b"TAMPERED_DATA_ATTACHED")

            # Verify tampered file triggers integrity mismatch
            tampered_valid, msg = database.verify_file_integrity(f_path)
            self.assertFalse(tampered_valid)
            self.assertIn("Tampered", msg)
        finally:
            if os.path.exists(f_path):
                os.remove(f_path)

if __name__ == "__main__":
    unittest.main()
