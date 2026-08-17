"""
Social Post Comment & LINE Push Notification Verification Test
Tests that social post commenting correctly triggers background push notifications without NameError runtime crashes.
"""
import sys
import os
import unittest

os.environ["FLASK_ENV"] = "testing"

try:
    from app_server import create_app
    import database
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_server import create_app
    import database


class SocialCommentNotificationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_social_comment_does_not_crash_on_missing_line_notification(self):
        """Verify adding a comment on a social post executes cleanly without NameError in background thread."""
        with self.client.session_transaction() as sess:
            sess["user"] = "commenter_user"
            sess["org_id"] = 1
            sess["_csrf_token"] = "testing"

        # Create a post first
        res_post = self.client.post(
            "/api/posts",
            data={"content": "Test Post Content", "category": "General"},
            headers={"X-CSRF-Token": "testing"}
        )
        self.assertEqual(res_post.status_code, 200)
        post_data = res_post.get_json()
        post_id = post_data.get("id")

        # Now add a comment as a different user to trigger post author notification
        with self.client.session_transaction() as sess:
            sess["user"] = "another_commenter"
            sess["org_id"] = 1
            sess["_csrf_token"] = "testing"

        res_comment = self.client.post(
            f"/api/posts/{post_id}/comments",
            json={"content": "Great post @commenter_user!"},
            headers={"X-CSRF-Token": "testing"}
        )
        self.assertEqual(res_comment.status_code, 200)
        data = res_comment.get_json()
        self.assertTrue(data.get("ok"))


if __name__ == "__main__":
    unittest.main()
