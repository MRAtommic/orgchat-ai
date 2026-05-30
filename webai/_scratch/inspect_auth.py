import sys
import os

sys.path.append("..")
# Let's mock the env vars and database/rag dependencies if necessary
os.environ["DB_PATH"] = "chat_history.db"
os.environ["AI_PROVIDER"] = "groq"

try:
    import database
    from routes.auth import auth_bp
    print("Success: auth blueprint imported cleanly!")
except Exception as e:
    import traceback
    print("Error importing auth:")
    traceback.print_exc()
