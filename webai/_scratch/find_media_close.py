with open("../static/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Let's count open/close braces starting from line 773
open_braces = 0
found_media = False
for idx in range(770, min(len(lines), 900)):
    line = lines[idx]
    if "@media (max-width: 1023px)" in line:
        found_media = True
        open_braces = 0
        print(f"Start media query on line {idx+1}")
    
    if found_media:
        # Count braces
        old_braces = open_braces
        open_braces += line.count('{')
        open_braces -= line.count('}')
        print(f"{idx+1}: ({open_braces}) {line.strip()[:60]}")
        if open_braces == 0 and old_braces > 0:
            print(f"End media query on line {idx+1}")
            break
