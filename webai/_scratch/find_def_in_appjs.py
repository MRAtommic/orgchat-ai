import re

with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "loadGoogleDriveStatus" in line and ("function" in line or "=>" in line or "async" in line) and "showView" not in line and "viewId" not in line:
        print(f"Definition on line {i+1}")
        # Write context around it
        start = max(0, i - 5)
        end = min(len(lines), i + 80)
        with open("load_status_def.js", "w", encoding="utf-8") as out:
            for idx in range(start, end):
                out.write(f"{idx+1}: {lines[idx]}")
        print("Written def to load_status_def.js")
