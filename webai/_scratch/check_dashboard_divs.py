with open(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

import re
tag_pat = re.compile(r'<(/?div)\b[^>]*>', re.IGNORECASE)

stack = []
print("Tracing div tags inside view-dashboard (lines 4994-5427)...")
for line_no in range(4994, 5428):
    line = lines[line_no - 1]
    
    for match in tag_pat.finditer(line):
        is_closing = bool(match.group(1).startswith('/'))
        tag_str = match.group(0)
        
        # Clean print line to avoid console encoding crash
        safe_line = line.strip().encode('ascii', errors='ignore').decode('ascii')
        
        if not is_closing:
            stack.append((line_no, tag_str))
            print(f"[{len(stack)}] Open div at line {line_no}: {safe_line[:60]}")
        else:
            if not stack:
                print(f"!!! ERROR: Stray closing div at line {line_no}: {safe_line[:60]}")
            else:
                open_line, open_str = stack.pop()
                print(f"[{len(stack)+1}] Close div at line {line_no} matches open from line {open_line}")

print(f"\nRemaining unclosed divs in view-dashboard: {len(stack)}")
for open_line, open_str in stack:
    safe_str = open_str.encode('ascii', errors='ignore').decode('ascii')
    print(f"  Unclosed div from line {open_line}: {safe_str}")
