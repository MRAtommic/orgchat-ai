import subprocess

def run_cmd(args):
    try:
        res = subprocess.run(args, capture_output=True, text=True, check=True)
        print(f"--- SUCCESS: {' '.join(args)} ---")
        print(res.stdout)
    except subprocess.CalledProcessError as e:
        print(f"--- ERROR: {' '.join(args)} ---")
        print(e.stdout)
        print(e.stderr)

run_cmd(["git", "status"])
