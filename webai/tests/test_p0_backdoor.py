import unittest
import os
import sys

# Ensure webai is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app_server import app


class TestP0Backdoor(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_line_test_login_backdoor_is_removed(self):
        """P0-1: /api/line/test-login must return 404 and must NOT log anyone in."""
        res_get = self.app.get('/api/line/test-login')
        self.assertEqual(res_get.status_code, 404, "GET /api/line/test-login must be 404 Not Found")

        res_post = self.app.post('/api/line/test-login')
        self.assertEqual(res_post.status_code, 404, "POST /api/line/test-login must be 404 Not Found")

        with self.app.session_transaction() as sess:
            self.assertNotIn("user", sess, "Session must NOT have user set by backdoor")


if __name__ == '__main__':
    unittest.main()

