with open("templates/index.html", "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        if "app.js?v=" in line:
            print(f"Line {idx}: {line.strip()}")
