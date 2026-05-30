import re

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract script block (lines 5443 to 5917, 0-indexed: 5442 to 5917)
script_lines = lines[5442:5917]
script_content = ''.join(script_lines)

print("Original length:", len(script_content))
print("Escaped ${ counts:", script_content.count(r'\${'))
print("Triple escaped ${ counts:", script_content.count(r'\\\${'))
print("Escaped backtick counts:", script_content.count(r'\`'))
print("Triple escaped backtick counts:", script_content.count(r'\\\`'))
