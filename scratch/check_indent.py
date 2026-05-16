import sys

with open(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\app_server.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if line.strip():
            indent = len(line) - len(line.lstrip(' '))
            if indent % 4 != 0:
                print(f"Line {i} has non-standard indent: {indent} spaces")
