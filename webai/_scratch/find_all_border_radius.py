import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\static\style.css"
with open(css_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "border-radius" in line:
        line_clean = line.strip().encode('ascii', errors='replace').decode('ascii')
        # Print the line and some context (like the selector above it)
        # Find selector by backtracking
        sel = ""
        for j in range(idx, max(-1, idx-10), -1):
            if "{" in lines[j]:
                sel = lines[j].strip()
                break
        sel_clean = sel.encode('ascii', errors='replace').decode('ascii')
        print(f"Line {idx+1}: {line_clean} (Selector context: {sel_clean})")
