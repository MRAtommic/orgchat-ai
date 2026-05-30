with open("../templates/index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "data-view=" in line or "data-mobile-view=" in line or "groupChatHead" in line or "groupChatModal" in line:
        if "aside" in line or "nav" in line or "button" in line or "a" in line:
            print(f"Line {i+1}: {line.strip()[:120]}")
