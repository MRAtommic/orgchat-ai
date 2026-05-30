import re

with open("../templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

start_match = re.search(r'<section\s+id="view-chat"', content)
if start_match:
    start_pos = start_match.start()
    pos = start_pos
    open_tags = 0
    while pos < len(content):
        if content[pos:pos+8] == "<section":
            open_tags += 1
        elif content[pos:pos+10] == "</section>":
            open_tags -= 1
            if open_tags == 0:
                end_pos = pos + 10
                break
        pos += 1
    
    view_chat_html = content[start_pos:end_pos]
    print(f"Extracted {len(view_chat_html)} bytes of view-chat")
    with open("view_chat_extracted.html", "w", encoding="utf-8") as out:
        out.write(view_chat_html)
else:
    print("Could not find view-chat in index.html")
