import unittest
import os
import sys
import ast
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import database
from db import connection as conn_mod
from db.social import (
    wiki_create_page,
    wiki_get_page,
    wiki_get_all_pages,
    wiki_update_page,
    wiki_delete_page,
    wiki_search
)
from db.orgs import transfer_org_ownership, is_org_owner
from db.users import get_persona
from db.finance import search_drive_logs


class TestP2DBIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["TESTING"] = "1"
        os.environ["FLASK_SECRET_KEY"] = "test-secret-key-for-p2-db-integrity-32b"

    # ─── P2-1: AST check for zero duplicate functions in db/ ─────────────────
    def test_p2_1_no_duplicate_function_declarations_in_db_layer(self):
        """AST check: ensures no top-level function names are shadowed/duplicated in any db/*.py file."""
        db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'db'))
        duplicates = []
        for filename in os.listdir(db_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(db_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=filename)
                seen = {}
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef):
                        if node.name in seen:
                            duplicates.append(f"{filename}: '{node.name}' declared at lines {seen[node.name]} and {node.lineno}")
                        else:
                            seen[node.name] = node.lineno

        self.assertEqual(duplicates, [], f"Duplicate DB functions found: {duplicates}")

    # ─── P2-1: Wiki Multi-Tenant Isolation ────────────────────────────────────
    def test_p2_1_wiki_multi_tenant_isolation(self):
        """Tenant isolation: Org A cannot read, update, delete, or search Org B's wiki pages."""
        org_a = 901
        org_b = 902

        # Create page in Org A
        pid_a, slug_a = wiki_create_page(
            title="Confidential Strategy Org A",
            content="Only Org A members should see this.",
            author="alice",
            org_id=org_a
        )
        self.assertIsNotNone(pid_a)

        # Create page in Org B
        pid_b, slug_b = wiki_create_page(
            title="Confidential Strategy Org B",
            content="Only Org B members should see this.",
            author="bob",
            org_id=org_b
        )
        self.assertIsNotNone(pid_b)

        # 1. Org B cannot read Org A's page by ID or slug
        self.assertIsNone(wiki_get_page(page_id=pid_a, org_id=org_b))
        self.assertIsNone(wiki_get_page(slug=slug_a, org_id=org_b))

        # 2. Org A can read Org A's page, and views counter increments
        page_a = wiki_get_page(page_id=pid_a, org_id=org_a)
        self.assertIsNotNone(page_a)
        self.assertEqual(page_a["title"], "Confidential Strategy Org A")
        self.assertGreaterEqual(page_a.get("views", 0), 1)

        # 3. Org B cannot search and find Org A's page
        search_b = wiki_search("Confidential", org_id=org_b)
        slugs_found_b = [p["slug"] for p in search_b]
        self.assertIn(slug_b, slugs_found_b)
        self.assertNotIn(slug_a, slugs_found_b)

        # 4. Org B cannot update Org A's page
        update_attempt = wiki_update_page(pid_a, title="Hacked by B", org_id=org_b)
        self.assertFalse(update_attempt)

        # Verify page in Org A was NOT modified
        page_a_check = wiki_get_page(page_id=pid_a, org_id=org_a)
        self.assertEqual(page_a_check["title"], "Confidential Strategy Org A")

        # 5. Org B cannot delete Org A's page
        delete_attempt = wiki_delete_page(pid_a, org_id=org_b)
        self.assertFalse(delete_attempt)

        # Clean up
        wiki_delete_page(pid_a, org_id=org_a)
        wiki_delete_page(pid_b, org_id=org_b)

    # ─── P2-1: Org Ownership Transfer ─────────────────────────────────────────
    def test_p2_1_transfer_org_ownership_updates_db_and_roles(self):
        """Verifies transfer_org_ownership updates owner_username, maintains admin status, and rejects non-owners."""
        conn = database._get_conn()
        cur = conn.cursor()
        test_org_name = f"TransferTestOrg_{os.urandom(3).hex()}"
        cur.execute("INSERT INTO organizations (name, owner_username) VALUES (?, ?)", (test_org_name, "owner_alice"))
        org_id = cur.lastrowid

        cur.execute("""
            INSERT INTO organization_members (organization_id, username, role, joined_at)
            VALUES (?, ?, 'admin', '2025-01-01 10:00:00')
        """, (org_id, "owner_alice"))
        cur.execute("""
            INSERT INTO organization_members (organization_id, username, role, joined_at)
            VALUES (?, ?, 'member', '2025-01-02 10:00:00')
        """, (org_id, "member_bob"))
        conn.commit()
        conn.close()

        # Non-owner cannot transfer
        ok, err = transfer_org_ownership(org_id, "member_bob", "owner_alice")
        self.assertFalse(ok)

        # Owner cannot transfer to self
        ok, err = transfer_org_ownership(org_id, "owner_alice", "owner_alice")
        self.assertFalse(ok)

        # Legitimate owner transfers to bob
        ok, msg = transfer_org_ownership(org_id, "owner_alice", "member_bob")
        self.assertTrue(ok)

        # Verify Bob is now owner
        self.assertTrue(is_org_owner(org_id, "member_bob"))
        # Verify Alice is no longer owner
        self.assertFalse(is_org_owner(org_id, "owner_alice"))

        # Verify both Alice and Bob remain admins
        conn = database._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT username, role FROM organization_members WHERE organization_id = ?", (org_id,))
        roles = dict(cur.fetchall())
        conn.close()
        self.assertEqual(roles.get("member_bob"), "admin")
        self.assertEqual(roles.get("owner_alice"), "admin")

    # ─── P2-3: DB Path Runtime Resolution for Test Isolation ──────────────────
    def test_p2_3_dynamic_db_path_honors_env_override(self):
        """P2-3: Verifies _resolve_db_path dynamically routes connections to isolated DB when DB_PATH env is set."""
        # tests/conftest.py fixes DB_PATH before the app is imported (so no test can touch the real database).
        # In that mode the path is deliberately immutable and this runtime-override check does not apply.
        if getattr(conn_mod, "_IMMUTABLE_CUSTOM_DB_PATH", None):
            self.skipTest("DB_PATH is fixed by tests/conftest.py for isolation")
        fd, temp_path = tempfile.mkstemp(suffix="_isolation_check.db")
        os.close(fd)
        try:
            orig_env = os.environ.get("DB_PATH")
            os.environ["DB_PATH"] = temp_path

            resolved = conn_mod._resolve_db_path()
            self.assertEqual(str(resolved), str(Path(temp_path)))

            # Connection opened using _get_conn() must target the temporary db
            test_conn = database._get_conn()
            test_conn.execute("CREATE TABLE isolation_marker (test_key TEXT)")
            test_conn.execute("INSERT INTO isolation_marker VALUES ('isolated_test_val')")
            test_conn.commit()
            test_conn.close()

            # Verify table exists in temp DB
            import sqlite3
            direct_conn = sqlite3.connect(temp_path)
            val = direct_conn.execute("SELECT test_key FROM isolation_marker").fetchone()[0]
            direct_conn.close()
            self.assertEqual(val, "isolated_test_val")

            # Restore env
            if orig_env is not None:
                os.environ["DB_PATH"] = orig_env
            else:
                os.environ.pop("DB_PATH", None)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == '__main__':
    unittest.main()
