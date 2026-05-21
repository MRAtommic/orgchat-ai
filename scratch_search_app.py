import re

def search_app():
    with open("app_server.py", "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    keywords = ["/api/settings", "/settings", "settings_manager", "file_meta.json", "admin", "reconcile", "/api/admin"]
    print("=== SEARCH RESULTS ===")
    for idx, line in enumerate(lines):
        line_num = idx + 1
        for kw in keywords:
            if kw in line:
                print(f"Line {line_num}: {line.strip()}")
                break

if __name__ == "__main__":
    search_app()
