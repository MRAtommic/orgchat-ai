import os
import json
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.absolute()
load_dotenv(BASE_DIR / ".env", override=True)

g_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
if g_env:
    info = json.loads(g_env)
    pk = info.get("private_key")
    print("Private key type:", type(pk))
    print("Private key length:", len(pk))
    print("Does it contain literal \\n?", "\\n" in pk)
    print("Does it contain actual newlines?", "\n" in pk)
    print("First 50 chars:", repr(pk[:50]))
    print("Last 50 chars:", repr(pk[-50:]))
    
    from cryptography.hazmat.primitives import serialization
    try:
        key = serialization.load_pem_private_key(pk.encode('utf-8'), password=None)
        print("Loaded key successfully:", type(key))
    except Exception as e:
        print("Failed to load key using cryptography:", e)
else:
    print("GOOGLE_SERVICE_ACCOUNT_JSON not set!")
