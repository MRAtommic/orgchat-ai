import os
import sys
import subprocess

def kill_port_5005():
    try:
        # Run netstat to find PIDs on port 5005
        print("Finding processes on port 5005...")
        output = subprocess.check_output("netstat -ano", shell=True).decode()
        pids = set()
        for line in output.splitlines():
            if ":5005" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    pids.add(int(pid))
        
        if not pids:
            print("No active processes listening on port 5005 found.")
            return
            
        print(f"Found PIDs listening on 5005: {pids}")
        for pid in pids:
            try:
                print(f"Killing process PID {pid}...")
                subprocess.check_call(f"taskkill /F /PID {pid}", shell=True)
                print(f"Successfully killed PID {pid}!")
            except Exception as e:
                print(f"Failed to kill PID {pid}: {e}")
                
    except Exception as e:
        print("Error while trying to kill port 5005:", e)

if __name__ == "__main__":
    kill_port_5005()
