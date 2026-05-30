with open("../static/style.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

open_braces = 0
found_media = False
for idx in range(770, len(lines)):
    line = lines[idx]
    if "@media (max-width: 1023px)" in line:
        found_media = True
        open_braces = 0
    
    if found_media:
        open_braces += line.count('{')
        open_braces -= line.count('}')
        if open_braces == 0:
            print(f"End media query on line {idx+1}")
            # Print 10 lines around the end
            for offset in range(max(0, idx - 5), min(len(lines), idx + 5)):
                print(f"{offset+1}: {lines[offset]}", end="")
            break
