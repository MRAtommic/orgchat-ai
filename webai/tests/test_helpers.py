# -*- coding: utf-8 -*-
"""
webai/tests/test_helpers.py — Shared Test Utilities & Fixtures
Provides isolated database instances and authenticated test clients.
"""

import os
import sys
from pathlib import Path
import sqlite3
import tempfile
import unittest

# Ensure webai is in sys.path
BASE_DIR = Path(__file__).parent.parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import database

class BaseTestCase(unittest.TestCase):
    """Base test case providing isolated test database setup."""

    @classmethod
    def setUpClass(cls):
        # Create unique temporary test DB
        cls.temp_db_fd, cls.temp_db_path = tempfile.mkstemp(suffix="_test.db")
        cls.orig_db_path = database.DB_PATH
        database.DB_PATH = cls.temp_db_path

        # Initialize schema and run migrations
        database.init_db()

    @classmethod
    def tearDownClass(cls):
        database.DB_PATH = cls.orig_db_path
        try:
            os.close(cls.temp_db_fd)
            if os.path.exists(cls.temp_db_path):
                os.remove(cls.temp_db_path)
        except Exception:
            pass

    def setUp(self):
        # Clean or set up per-test state if needed
        pass
