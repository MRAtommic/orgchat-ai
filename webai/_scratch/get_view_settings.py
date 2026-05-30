import re

with open("../index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find view-settings section
start_match = re.search(r'<section\s+id="view-settings"', content)
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
    
    view_settings_html = content[start_pos:end_pos]
    print(f"Extracted {len(view_settings_html)} bytes of view-settings.")
    
    # Save it to a file
    with open("view_settings_extracted.html", "w", encoding="utf-8") as out:
        out.write(view_settings_html)
    print("Saved to view_settings_extracted.html successfully.")
else:
    print("Could not find view-settings in index.html")
