import subprocess
import os

def run_cmd(args):
    print(f"Running: {' '.join(args)}")
    res = subprocess.run(args, capture_output=True, text=True)
    if res.returncode == 0:
        print("SUCCESS:")
        print(res.stdout)
    else:
        print("FAILED:")
        print(res.stdout)
        print(res.stderr)
    return res.returncode == 0

# Step 1: Revert app_server.py to the latest git commit
print("--- STEP 1: Reverting app_server.py to git state ---")
if run_cmd(["git", "checkout", "app_server.py"]):
    print("app_server.py successfully reverted to committed git state.")
else:
    print("Could not revert app_server.py via git checkout. (Maybe it's not tracked yet?)")



# Step 2: Run clean_app.py to apply the fixed sanitization
print("\n--- STEP 2: Running clean_app.py ---")
import sys
# Add parent directory of this script to sys.path to find clean_app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "clean_app.py")):
    # We will run clean_app.py
    import clean_app
    try:
        clean_app.clean_file()
        print("clean_app.py executed successfully.")
    except Exception as e:
        print(f"Error executing clean_app.py: {e}")
else:
    print("clean_app.py not found!")

# Step 3: Validate syntax of app_server.py
print("\n--- STEP 3: Validating syntax of app_server.py ---")
if run_cmd(["python", "-m", "py_compile", "app_server.py"]):
    print("🎉 app_server.py syntax is perfectly valid!")
else:
    print("❌ app_server.py has syntax errors.")
