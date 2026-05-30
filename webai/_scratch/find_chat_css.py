with open("../static/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's write context around the matches
matches = [796, 811, 816, 1202, 1207, 1502]
with open("chat_css_context.css", "w", encoding="utf-8") as out:
    for m in matches:
        out.write(f"=== MATCH AT LINE {m} ===\n")
        start = max(0, m - 10)
        end = min(len(lines), m + 20)
        for idx in range(start, end):
            out.write(f"{idx+1}: {lines[idx]}")
        out.write("\n")
print("Wrote CSS context successfully.")
