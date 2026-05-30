import re

with open(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html", "r", encoding="utf-8") as f:
    html = f.read()

lines = html.splitlines()

# Let's find all section tags
section_pat = re.compile(r'<section\s+id="([^"]+)"\s+class="view\b', re.IGNORECASE)
sections = []
for idx, line in enumerate(lines, 1):
    m = section_pat.search(line)
    if m:
        sections.append((m.group(1), idx))

sections.append(("EOF", len(lines) + 1))

# For each section, trace the div tags
div_pat = re.compile(r'<(/?div)\b[^>]*>', re.IGNORECASE)

for i in range(len(sections) - 1):
    sec_name, start_line = sections[i]
    next_sec_name, end_line = sections[i+1]
    
    stack = []
    for line_no in range(start_line, end_line):
        line = lines[line_no - 1]
        
        # Skip Jinja lines to avoid matching issues
        if '{%' in line or '{{' in line or '%}' in line or '}}' in line:
            continue
            
        for match in div_pat.finditer(line):
            is_closing = bool(match.group(1).startswith('/'))
            tag_str = match.group(0)
            
            if not is_closing:
                stack.append((line_no, tag_str))
            else:
                if not stack:
                    # Stray closing div inside section
                    pass
                else:
                    stack.pop()
                    
    if stack:
        print(f"View '{sec_name}' (lines {start_line}-{end_line}) has {len(stack)} unclosed divs:")
        for lno, tag in stack[:5]:
            safe_tag = tag.encode('ascii', errors='ignore').decode('ascii')
            print(f"  Line {lno}: {safe_tag}")
