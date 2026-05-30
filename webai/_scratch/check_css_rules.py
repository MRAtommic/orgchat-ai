import sys

sys.stdout.reconfigure(encoding='utf-8')

css_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\static\style.css"
with open(css_path, "r", encoding="utf-8") as f:
    content = f.read()

def parse_css(css_text):
    rules = []
    i = 0
    n = len(css_text)
    
    in_comment = False
    selector_start = 0
    
    while i < n:
        if i < n - 1 and css_text[i:i+2] == "/*":
            in_comment = True
            i += 2
            continue
        if i < n - 1 and css_text[i:i+2] == "*/":
            in_comment = False
            i += 2
            continue
        if in_comment:
            i += 1
            continue
            
        char = css_text[i]
        if char == "{":
            selector = css_text[selector_start:i].strip()
            brace_count = 1
            j = i + 1
            while j < n and brace_count > 0:
                if css_text[j] == "{":
                    brace_count += 1
                elif css_text[j] == "}":
                    brace_count -= 1
                j += 1
            
            block_content = css_text[i+1:j-1].strip()
            
            if "{" in block_content:
                rules.append((selector, block_content, True))
                child_rules = parse_css(block_content)
                for child_sel, child_prop, is_nested in child_rules:
                    rules.append((f"{selector} -> {child_sel}", child_prop, False))
            else:
                rules.append((selector, block_content, False))
                
            i = j
            selector_start = i
            continue
            
        i += 1
        
    return rules

all_rules = parse_css(content)

# We want to print any rule containing properties with rounded or shadow that could be active in the modal
for selector, properties, is_media in all_rules:
    if is_media:
        continue
    selector_clean = selector.strip().lower()
    props_clean = properties.strip().lower()
    
    # We want to see rules setting border-radius or box-shadow or margin on elements inside the chat modal
    # that could style these cards
    if "radius" in props_clean or "shadow" in props_clean or "margin" in props_clean:
        # Filter to things that could match the chat modal elements
        if any(w in selector_clean for w in ["aside", "main", "chat", "modal", "panel", "bg-", "article"]):
            # Clean and print
            selector_print = selector_clean.encode('ascii', errors='replace').decode('ascii')
            properties_print = properties.strip().encode('ascii', errors='replace').decode('ascii')
            print(f"Selector: {selector_print}")
            print(f"Properties:\n{properties_print}")
            print("-" * 50)
