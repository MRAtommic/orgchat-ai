with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Extract script block (lines 5443 to 5917, 0-indexed: 5442 to 5917)
script_lines = lines[5442:5917]
script_content = ''.join(script_lines)

print("Original script length:", len(script_content))

# Clean the block
cleaned_content = script_content
# Replace triple escapes first
cleaned_content = cleaned_content.replace(r'\\\${', '${')
cleaned_content = cleaned_content.replace(r'\\\`', '`')
# Replace single escapes
cleaned_content = cleaned_content.replace(r'\${', '${')
cleaned_content = cleaned_content.replace(r'\`', '`')

print("Cleaned script length:", len(cleaned_content))

# Verify javascript syntax by parsing with python's compile or checking brackets
# We can overwrite the lines in the list
lines[5442:5917] = [cleaned_content]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ templates/index.html successfully updated and cleaned!")
