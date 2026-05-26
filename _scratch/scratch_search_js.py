with open("templates/index.html", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print("Searching templates/index.html for dashGreeting...")
for i, line in enumerate(lines, 1):
    if "dashGreeting" in line or "dashAISummary" in line or "loadDashboard" in line:
        print(f"Line {i}: {line.strip()}")
