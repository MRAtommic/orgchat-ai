# -*- coding: utf-8 -*-
"""Make the whole test session use a throw-away database.

Before this file existed, importing the app in a test pointed it at the real `chat_history.db`, so tests
created users/orgs and wrote audit rows into production data. DB_PATH is read when `db.connection` is
imported, so it must be set here, before any test module imports the app.
"""
import atexit
import os
import shutil
import tempfile

_TMP = tempfile.mkdtemp(prefix="orgchat_tests_")
os.environ["DB_PATH"] = os.path.join(_TMP, "test_chat_history.db")
os.environ.pop("REDIS_URL", None)                       # never touch a real Redis from tests
os.environ.pop("GOOGLE_SERVICE_ACCOUNT_JSON", None)     # never call real Google APIs from tests
os.environ.setdefault("FLASK_SECRET_KEY", "test-only-secret-key-0123456789abcdef0123456789abcdef")
os.environ.setdefault("BASE_URL", "http://localhost:5999")
atexit.register(shutil.rmtree, _TMP, True)
