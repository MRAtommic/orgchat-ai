with open("../static/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("chat_panels_styles.txt", "w", encoding="utf-8") as out:
    for i, line in enumerate(lines):
        if "#chatSidebarPanel" in line or "#chatMainArea" in line or "groupChatModal" in line:
            out.write(f"Line {i+1}: {line}\n")
            out.write("--- CONTEXT ---\n")
            start = max(0, i - 4)
            end = min(len(lines), i + 12)
            for idx in range(start, end):
                out.write(f"{idx+1}: {lines[idx]}")
            out.write("---------------\n\n")
print("Wrote style context successfully.")
