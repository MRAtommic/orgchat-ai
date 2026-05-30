import re
import sys

# Set standard output encoding to utf-8 if possible
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')

with open("c:/Users/KC_Ketwilai/Downloads/orgchat-ai-main/orgchat-ai-main/webai/templates/index.html", "r", encoding="utf-8") as f:
    content = f.read()

lines = content.splitlines()
for idx, line in enumerate(lines):
    if "<header" in line:
        print(f"--- Line {idx + 1} ---")
        start = max(0, idx - 2)
        end = min(len(lines), idx + 10)
        for i in range(start, end):
            prefix = "-> " if i == idx else "   "
            # Ensure line can be printed safely without unicode encode errors
            safe_line = lines[i].encode('ascii', 'replace').decode('ascii')
            print(f"{i+1:4d}:{prefix}{safe_line}")
