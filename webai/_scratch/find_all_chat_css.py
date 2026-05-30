import re

with open("../static/style.css", "r", encoding="utf-8") as f:
    content = f.read()

matches = list(re.finditer(r'#chatSidebarPanel|#chatMainArea', content))

with open("all_chat_css.css", "w", encoding="utf-8") as out:
    out.write(f"Found {len(matches)} matches.\n\n")
    for i, m in enumerate(matches):
        start_pos = max(0, m.start() - 100)
        end_pos = min(len(content), m.end() + 200)
        out.write(f"=== MATCH {i+1} ===\n")
        out.write(content[start_pos:end_pos])
        out.write("\n\n")
print("Wrote all matches to all_chat_css.css successfully.")
