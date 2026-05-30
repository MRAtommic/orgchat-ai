import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

js_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\static\app.js"
with open(js_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

targets = ["chatSidebarPanel", "chatMainArea", "groupChatModal"]

for idx, line in enumerate(lines):
    if any(t in line for t in targets):
        if any(w in line for w in ["class", "style", "shadow", "rounded", "margin"]):
            line_clean = line.strip().encode('ascii', errors='replace').decode('ascii')
            print(f"Line {idx+1}: {line_clean}")
