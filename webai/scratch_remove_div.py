with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Verify that index 4035 is indeed "            </div>" and index 4036 is "          </header>"
if lines[4035].strip() == '</div>' and '</header>' in lines[4036]:
    del lines[4035]
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("Success")
else:
    print(f"Indices do not match! 4035: {lines[4035].strip()} | 4036: {lines[4036].strip()}")
