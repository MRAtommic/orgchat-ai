import re

html_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\templates\index.html"
with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

print("HTML Length:", len(content))

# Find all script src attributes
srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', content)
print("Found script srcs:")
for s in srcs:
    print("  ", s)

# Search for the word 'app.js' in the file
matches = [m.start() for m in re.finditer(r'app\.js', content)]
print(f"Occurrences of 'app.js': {len(matches)}")
for m in matches[:10]:
    start = max(0, m - 50)
    end = min(len(content), m + 50)
    snippet = content[start:end].replace('\n', ' ')
    print(f"  Snippet at {m}: ...{snippet}...")
