with open("app_server.py", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

print("Searching app_server.py for '犧' to find Mojibake...")
for i, line in enumerate(lines, 1):
    if "犧" in line:
        print(f"Line {i}: {line.strip()}")
