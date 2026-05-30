import sqlite3
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

conn = sqlite3.connect('chat_history.db')
cur = conn.cursor()

# 1. Update Admin's drive_folder_id to 1CxDshFuM17fTVSSKtSS_DZoMOdhl7iGa
print("Updating Admin's drive_folder_id in database...")
cur.execute("""
    UPDATE user_google_tokens 
    SET drive_folder_id = '1CxDshFuM17fTVSSKtSS_DZoMOdhl7iGa' 
    WHERE username = 'Admin'
""")
conn.commit()
print("Database updated!")

# Also let's check mxmm2547 folder ID if any
cur.execute("SELECT username, drive_folder_id FROM user_google_tokens")
for row in cur.fetchall():
    print("User token info:", row)

conn.close()

# 2. Test in google_manager context
from google_drive_service import google_manager
google_manager.set_context(username="Admin", org_id=1)

print("\n=== Testing under Admin context ===")
print("parent_folder_id now:", google_manager.parent_folder_id)
try:
    folders = google_manager.list_subfolders()
    print("Folders retrieved from Drive:")
    for f in folders:
        print(f"- {f['name']} (ID: {f['id']})")
except Exception as e:
    import traceback
    traceback.print_exc()
