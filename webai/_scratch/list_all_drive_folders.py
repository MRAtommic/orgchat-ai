import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from google_drive_service import google_manager

google_manager.set_context(username="Admin", org_id=1)

print("=== Listing ALL folders in Admin's Drive ===")
try:
    query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = google_manager.drive_service.files().list(q=query, fields="files(id, name, parents)", supportsAllDrives=True).execute()
    folders = results.get('files', [])
    print(f"Total folders found: {len(folders)}")
    for f in folders:
        print(f"- {f['name']} (ID: {f['id']}), Parents: {f.get('parents')}")
except Exception as e:
    import traceback
    traceback.print_exc()
