import sys
import os

# Add the webai directory to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))

try:
    print("Checking database imports...")
    import database
    print("Checking routes/auth.py syntax and imports...")
    import routes.auth
    print("Checking routes/admin.py syntax and imports...")
    import routes.admin
    print("✅ All imports and syntax checked successfully without any issues!")
except Exception as e:
    print(f"❌ Error detected: {e}")
    sys.exit(1)
