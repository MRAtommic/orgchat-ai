import sys
import os

# Set system encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

# Mock environment if needed or load .env
from dotenv import load_dotenv
load_dotenv()

from google_drive_service import google_manager
import database

# Let's check with Org 1
google_manager.set_context(username="Admin", org_id=1)

print("=== Drive Service Ready ===")
print("drive_service present:", google_manager.drive_service is not None)
p_id = google_manager.parent_folder_id
print("parent_folder_id:", p_id)

try:
    folders = google_manager.list_subfolders()
    print("Folders found before create:", folders)
    if not folders:
        print("Folders empty! Attempting to create default folder 'ทั่วไป'...")
        new_folder_id = google_manager._get_or_create_folder("ทั่วไป", p_id)
        print("Successfully created folder! ID:", new_folder_id)
        folders = google_manager.list_subfolders()
        print("Folders found after create:", folders)
except Exception as e:
    import traceback
    traceback.print_exc()
