import sys
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)

import database

conn = database._get_conn()
cursor = conn.cursor()

print("--- USER SETTINGS ---")
cursor.execute("SELECT username, role, can_view_kb, can_edit_kb, can_delete_kb FROM user_settings")
for row in cursor.fetchall():
    print(row)

print("\n--- USER PROFILES ---")
cursor.execute("SELECT username, display_name FROM user_profiles")
for row in cursor.fetchall():
    print(row)

conn.close()
