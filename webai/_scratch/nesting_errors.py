import re

def locate_nesting_errors(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We will trace the exact start and end of each section
    # Let's search for tags like:
    # <section id="view-...
    # and </section>
    
    lines = content.splitlines()
    section_stack = []
    
    # We also trace div/main/aside tags to find mismatching/unclosed tags inside sections
    tag_pattern = re.compile(
        r'<(section|div|main|aside)\b[^>]*id=["\'](view-[a-zA-Z0-9_-]+)["\']'  # Match view sections specifically
        r'|<(section|div|main|aside)\b[^>]*>'                                  # Match other tags
        r'|</(section|div|main|aside)>',                                      # Match closing tags
        re.IGNORECASE
    )
    
    current_path = []
    
    for line_num, line in enumerate(lines, 1):
        for match in tag_pattern.finditer(line):
            tag_text = match.group(0)
            if tag_text.startswith('</'):
                tag_name = tag_text[2:-1].lower()
                
                # Check if we are closing a view section
                if current_path and current_path[-1]['name'] == tag_name:
                    closed = current_path.pop()
                    if closed['is_view']:
                        print(f"Closed View Section {closed['view_id']} on line {line_num} (Opened on line {closed['line']})")
                else:
                    # Look back to find matching tag name
                    found_idx = -1
                    for idx in reversed(range(len(current_path))):
                        if current_path[idx]['name'] == tag_name:
                            found_idx = idx
                            break
                    if found_idx != -1:
                        # Popping mismatching elements
                        mismatched = current_path[found_idx+1:]
                        if mismatched:
                            print(f"Warning: Closing </{tag_name}> on line {line_num} implicitly closed nested tags: "
                                  f"{[m['text'] for m in mismatched]}")
                        current_path = current_path[:found_idx]
            else:
                # Opening tag
                # Check if it's a view section
                is_view = False
                view_id = None
                
                # Extract tag name
                tag_name_match = re.match(r'<([a-zA-Z0-9]+)', tag_text)
                if not tag_name_match:
                    continue
                tag_name = tag_name_match.group(1).lower()
                
                # Check if id starts with 'view-'
                id_match = re.search(r'id=["\'](view-[a-zA-Z0-9_-]+)["\']', tag_text, re.IGNORECASE)
                if id_match:
                    is_view = True
                    view_id = id_match.group(1)
                    print(f"Opened View Section {view_id} on line {line_num} inside: "
                          f"{[p['view_id'] if p['is_view'] else p['tag'] for p in current_path if p['is_view'] or p['tag'] != 'div']}")
                
                # Avoid self-closing tags (standard div/section/main/aside don't self close)
                if not tag_text.endswith('/>'):
                    current_path.append({
                        'name': tag_name,
                        'tag': tag_name,
                        'line': line_num,
                        'text': tag_text,
                        'is_view': is_view,
                        'view_id': view_id
                    })

locate_nesting_errors(r'c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html')
