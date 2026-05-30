import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)

from google_drive_service import google_manager

# Set context to bypass credentials error for testing if possible
# Let's see if we can authenticate using token.json or service account
google_manager.set_context("Admin", 1)

print("Drive Service is None?", google_manager.drive_service is None)
if google_manager.drive_service:
    p_id = google_manager.parent_folder_id
    print("Parent Folder ID:", p_id)
    try:
        contents = google_manager.list_subfolders()
        print(f"list_subfolders returned {len(contents)} items:")
        for c in contents:
            print(c)
    except Exception as e:
        print("Error listing:", e)
else:
    print("Cannot test because Drive Service could not be initialized.")
