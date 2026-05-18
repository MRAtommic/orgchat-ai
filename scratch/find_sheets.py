import sys
import io

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

with open("app_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print("--- SEARCH FOR GOOGLE / SHEETS ---")
for idx, line in enumerate(lines):
    if "sheet" in line.lower() or "google" in line.lower():
        print(f"{idx+1}: {line.strip()}")
