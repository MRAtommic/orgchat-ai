with open("app_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print("Searching app_server.py for dashboard data...")
for i, line in enumerate(lines, 1):
    if "/api/dashboard" in line or "/api/stats" in line or "dashAISummary" in line or "daily_morning_summary" in line or "get_daily_activities" in line:
        print(f"Line {i}: {line.strip()}")
