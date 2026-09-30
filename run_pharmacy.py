"""
🚀 Pharmacy System Standalone Launcher
Run this script to launch the Pharmacy System on port 5005 so it immediately connects
with the Cloudflare tunnel (https://openchat.sbs) without changing any settings!
"""

import os
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
PHARMACY_DIR = BASE_DIR / "pharmacy_system"

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=" * 60)
    print("🏥 LAUNCHING PHARMACY STOCK MANAGEMENT SYSTEM")
    print("=" * 60)
    print(f"Directory: {PHARMACY_DIR}")
    print(f"Target Port: 5005 (Cloudflare Tunnel: https://openchat.sbs)")
    print("=" * 60)

    # Change working directory to pharmacy_system
    os.chdir(PHARMACY_DIR)

    # Run app.py
    cmd = [sys.executable, "app.py"]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n🛑 Pharmacy System stopped gracefully.")

if __name__ == "__main__":
    main()
