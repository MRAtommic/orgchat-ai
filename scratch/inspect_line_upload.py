import sys
import io

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

def search_file(filepath, keywords):
    print(f"\n================ SEARCHING: {filepath} ================")
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            for kw in keywords:
                if kw.lower() in line.lower():
                    print(f"{idx+1}: {line.strip()}")
                    break
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

search_file("app_server.py", ["webhook", "line", "sheet", "drive"])
search_file("google_drive_service.py", ["sheet", "upload", "append", "column"])
