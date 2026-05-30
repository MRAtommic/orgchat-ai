import sys
import os
from pathlib import Path

# Add parent directory to sys.path so we can import packages
BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)

import app_server
import rag_engine
from routes.chat import view_kb_file

print("List of files:")
files = rag_engine.list_files()
for f in files:
    print(f"File ID: {f['file_id']}, Name: {f['name']}, Path: {f['path']}, Type: {f['type']}, Status: {f['status']}")

# Let's test the endpoint context
app = app_server.app
with app.test_request_context():
    # Set session values
    from flask import session
    session["user"] = "Admin"
    session["org_id"] = 1
    session["org_role"] = "admin"
    
    # Try calling view_kb_file directly
    file_id = "6be6b1203f3d51df0b553a70e57b8a723cd405683958204f96d23d7cd6aea659"
    print(f"\nTesting view_kb_file for {file_id}:")
    try:
        res = view_kb_file(file_id)
        print(f"Response: {res}")
    except Exception as e:
        import traceback
        print(f"Error in view_kb_file: {e}")
        traceback.print_exc()
