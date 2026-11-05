import unittest
import os
import sys

# Ensure webai is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestP0Security(unittest.TestCase):
    def test_production_without_secret_fails_startup(self):
        """P0-2: In production without FLASK_SECRET_KEY, create_app must raise RuntimeError."""
        orig_env = os.environ.get("APP_ENV")
        orig_secret = os.environ.get("FLASK_SECRET_KEY")
        orig_sec2 = os.environ.get("SECRET_KEY")
        try:
            os.environ["APP_ENV"] = "production"
            if "FLASK_SECRET_KEY" in os.environ:
                del os.environ["FLASK_SECRET_KEY"]
            if "SECRET_KEY" in os.environ:
                del os.environ["SECRET_KEY"]

            from app_server import create_app
            with self.assertRaises(RuntimeError):
                create_app()
        finally:
            if orig_env is not None:
                os.environ["APP_ENV"] = orig_env
            else:
                os.environ.pop("APP_ENV", None)
            if orig_secret is not None:
                os.environ["FLASK_SECRET_KEY"] = orig_secret
            if orig_sec2 is not None:
                os.environ["SECRET_KEY"] = orig_sec2

    def test_insecure_default_secret_rejected_in_production(self):
        """P0-2: In production with default hardcoded secret, create_app must raise RuntimeError."""
        orig_env = os.environ.get("APP_ENV")
        orig_secret = os.environ.get("FLASK_SECRET_KEY")
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["FLASK_SECRET_KEY"] = "orgchat-default-secret-change-me"
            from app_server import create_app
            with self.assertRaises(RuntimeError):
                create_app()
        finally:
            if orig_env is not None:
                os.environ["APP_ENV"] = orig_env
            else:
                os.environ.pop("APP_ENV", None)
            if orig_secret is not None:
                os.environ["FLASK_SECRET_KEY"] = orig_secret
            else:
                os.environ.pop("FLASK_SECRET_KEY", None)

    def test_invite_token_legacy_and_tampered_rejected(self):
        """P0-2: Legacy untimed tokens and tampered tokens must fail verification."""
        from routes.auth import _verify_invite_token, _make_invite_token

        # Untimed legacy token (no dot) must be rejected
        self.assertFalse(_verify_invite_token("legacytokenwithnotimestamp", "test@org.com", 1))

        # Valid timed token must pass
        token = _make_invite_token("test@org.com", 1)
        self.assertTrue(_verify_invite_token(token, "test@org.com", 1))

        # Tampered token must fail
        self.assertFalse(_verify_invite_token(token + "x", "test@org.com", 1))
        self.assertFalse(_verify_invite_token(token, "other@org.com", 1))

    def test_cookie_secure_default_in_production(self):
        """P0-3: Under APP_ENV=production, SESSION_COOKIE_SECURE defaults to True."""
        orig_env = os.environ.get("APP_ENV")
        orig_cookie = os.environ.get("SESSION_COOKIE_SECURE")
        orig_secret = os.environ.get("FLASK_SECRET_KEY")
        try:
            os.environ["APP_ENV"] = "production"
            os.environ["FLASK_SECRET_KEY"] = "super-strong-test-secret-key-32charslong!"
            os.environ.pop("SESSION_COOKIE_SECURE", None)

            from app_server import create_app
            app_prod = create_app()
            self.assertTrue(app_prod.config['SESSION_COOKIE_SECURE'])
        finally:
            if orig_env is not None:
                os.environ["APP_ENV"] = orig_env
            else:
                os.environ.pop("APP_ENV", None)
            if orig_cookie is not None:
                os.environ["SESSION_COOKIE_SECURE"] = orig_cookie
            else:
                os.environ.pop("SESSION_COOKIE_SECURE", None)
            if orig_secret is not None:
                os.environ["FLASK_SECRET_KEY"] = orig_secret
            else:
                os.environ.pop("FLASK_SECRET_KEY", None)

    def test_cookie_secure_can_be_disabled_via_env(self):
        """P0-3: SESSION_COOKIE_SECURE=false explicitly disables secure cookie."""
        orig_cookie = os.environ.get("SESSION_COOKIE_SECURE")
        try:
            os.environ["SESSION_COOKIE_SECURE"] = "false"
            from app_server import create_app
            app = create_app()
            self.assertFalse(app.config['SESSION_COOKIE_SECURE'])
        finally:
            if orig_cookie is not None:
                os.environ["SESSION_COOKIE_SECURE"] = orig_cookie
            else:
                os.environ.pop("SESSION_COOKIE_SECURE", None)


if __name__ == '__main__':
    unittest.main()

