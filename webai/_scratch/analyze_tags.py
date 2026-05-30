import re

def analyze_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple tag parser to trace block structures
    # We will trace tags like <div>, <aside>, <main>, <section>, etc. and their corresponding closing tags
    # Keep track of the active tags stack with their line numbers
    pattern = re.compile(r'<(div|aside|main|section|form|aside|header|footer)\b[^>]*>|</(div|aside|main|section|form|aside|header|footer)>', re.IGNORECASE)
    
    stack = []
    lines = content.splitlines()
    for line_num, line in enumerate(lines, 1):
        for match in pattern.finditer(line):
            tag_text = match.group(0)
            if tag_text.startswith('</'):
                tag_name = tag_text[2:-1].lower()
                # Find matching opening tag from stack (searching from end)
                found = False
                for idx in reversed(range(len(stack))):
                    if stack[idx]['name'] == tag_name:
                        stack.pop(idx)
                        found = True
                        break
                if not found:
                    print(f"Error: Closing tag {tag_text} on line {line_num} has no matching opening tag.")
            else:
                tag_name = re.match(r'<([a-zA-Z0-9]+)', tag_text).group(1).lower()
                # Self-closing tags should not be pushed to stack (though div/section/main/aside/form/header/footer are not self-closing)
                if not tag_text.endswith('/>'):
                    stack.append({'name': tag_name, 'line': line_num, 'text': tag_text})

    print("\n--- Remaining Unclosed Tags on Stack ---")
    for item in stack:
        print(f"Line {item['line']}: {item['text']}")

analyze_html(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html')
