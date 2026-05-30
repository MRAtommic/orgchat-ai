import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)

import app_server

# Let's test the endpoint context
app = app_server.app
with app.test_request_context():
    # Set session values
    from flask import session, json
    session["user"] = "Admin"
    session["org_id"] = 1
    session["org_role"] = "admin"
    
    # Call get_drive_contents directly
    from routes.chat import get_drive_contents
    res = get_drive_contents()
    print("Status:", res.status_code)
    data = json.loads(res.data)
    print("Response JSON:")
    print("ok:", data.get("ok"))
    print("folder_name:", data.get("folder_name"))
    print("items count:", len(data.get("items", [])))
    if len(data.get("items", [])) > 0:
        print("First item:", data.get("items")[0])
