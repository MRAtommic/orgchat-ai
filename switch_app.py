"""
🔁 Multi-Project Switcher
Switch between OrgChat AI (Default) and Pharmacy Stock System (New Medical App)
Both run on port 5005 and connect seamlessly to the existing Cloudflare tunnel (https://openchat.sbs)
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Force UTF-8 on Windows
sys.stdout.reconfigure(encoding='utf-8')

ROOT_DIR = Path(__file__).parent.absolute()
WEBAI_DIR = ROOT_DIR / "webai"
PHARMACY_DIR = ROOT_DIR / "pharmacy_system"

def check_port_5005():
    """Check what process is using port 5005 on Windows."""
    try:
        out = subprocess.check_output("netstat -ano | findstr :5005", shell=True, text=True)
        lines = [line.strip() for line in out.splitlines() if "LISTENING" in line]
        if lines:
            parts = lines[0].split()
            pid = parts[-1]
            return pid
    except Exception:
        pass
    return None

def kill_process(pid):
    """Kill process by PID."""
    try:
        subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=True)
        print(f"🛑 Terminated process PID {pid} on port 5005")
        time.sleep(1)
        return True
    except Exception as e:
        print(f"⚠️ Failed to kill process {pid}: {e}")
        return False

def run_project(choice):
    pid = check_port_5005()
    if pid:
        print(f"\n⚠️ พบโปรเซส (PID: {pid}) กำลังใช้งานพอร์ต 5005 อยู่")
        ans = input("ต้องการปิดโปรเซสเดิมเพื่อสลับไปรันโปรเจกต์ใหม่หรือไม่? (y/n): ").strip().lower()
        if ans == 'y':
            kill_process(pid)
        else:
            print("ยกเลิกการสลับโปรเจกต์")
            return

    if choice == "1":
        print("\n🚀 กำลังเริ่มรัน: [1] OrgChat AI (ระบบเดิม)...")
        os.chdir(WEBAI_DIR)
        subprocess.run([sys.executable, "app_server.py"])
    elif choice == "2":
        print("\n🚀 กำลังเริ่มรัน: [2] Pharmacy Stock System (ระบบคลังยาใหม่)...")
        os.chdir(PHARMACY_DIR)
        subprocess.run([sys.executable, "app.py"])

def main():
    while True:
        print("\n" + "=" * 60)
        print("🔁 PROJECT SWITCHER (Domain: openchat.sbs / Port: 5005)")
        print("=" * 60)
        print(" [1] 🤖 รัน OrgChat AI (ระบบเดิม - แชทบอท / บัญชีสลิปการเงิน)")
        print(" [2] 🏥 รัน Pharmacy Stock System (ระบบคลังยา - ตัดสต็อก LINE & QR)")
        print(" [3] 🔍 ตรวจสอบสถานะพอร์ต 5005")
        print(" [0] 🚪 ออกจากโปรแกรม")
        print("=" * 60)
        
        choice = input("กรุณาเลือกโปรเจกต์ที่ต้องการรัน [0-3]: ").strip()
        if choice in ["1", "2"]:
            run_project(choice)
            break
        elif choice == "3":
            pid = check_port_5005()
            if pid:
                print(f"🟢 พอร์ต 5005 กำลังทำงานอยู่ (PID: {pid})")
            else:
                print("⚪ พอร์ต 5005 ยังว่างอยู่ (ไม่มีโปรเจกต์ใดรันอยู่)")
        elif choice == "0":
            print("บายค่ะ!")
            break
        else:
            print("ตัวเลือกไม่ถูกต้อง กรุณาเลือกใหม่ค่ะ")

if __name__ == "__main__":
    main()
