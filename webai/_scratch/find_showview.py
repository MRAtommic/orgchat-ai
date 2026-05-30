import re

with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "function showView" in line or "function switchView" in line or "switchView =" in line:
        print(f"Line {i+1}: {line.strip()[:100]}")
        start = max(0, i - 5)
        end = min(len(lines), i + 60)
        with open(f"view_function_{i+1}.js", "w", encoding="utf-8") as out:
            for idx in range(start, end):
                out.write(f"{idx+1}: {lines[idx]}")
        print(f"Saved context to view_function_{i+1}.js")
