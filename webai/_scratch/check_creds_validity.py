import sys
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env", override=True)

from google.oauth2 import service_account

g_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if g_env:
    info = json.loads(g_env)
    scopes = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    creds = service_account.Credentials.from_service_account_info(
        info, scopes=scopes
    )
    print("Creds type:", type(creds))
    print("Is valid:", creds.valid)
    print("Token is None:", creds.token is None)
    
    # Try refreshing or using it
    from google.auth.transport.requests import Request
    try:
        creds.refresh(Request())
        print("After refresh, Is valid:", creds.valid)
        print("After refresh, Token:", creds.token[:10] if creds.token else "None")
    except Exception as e:
        print("Refresh failed:", e)
else:
    print("GOOGLE_SERVICE_ACCOUNT_JSON not set!")
