with open("../static/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "loadGoogleDriveStatus" in line:
        print(f"Line {i+1}: {line.strip()}")
        # Let's print 10 lines before and 30 lines after
        start = max(0, i - 10)
        end = min(len(lines), i + 40)
        print("--- CONTEXT ---")
        for idx in range(start, end):
            print(f"{idx+1}: {lines[idx]}", end="")
        print("---------------\n")
