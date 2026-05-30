import os
if os.path.exists("page.html"):
    with open("page.html", "r", encoding="utf-8") as f:
        html = f.read()
    import re
    scripts = re.findall(r'<script\b[^>]*src="([^"]+)"', html)
    print("page.html scripts:", scripts)
else:
    print("page.html does not exist in root directory")

if os.path.exists("templates/page.html"):
    with open("templates/page.html", "r", encoding="utf-8") as f:
        html = f.read()
    import re
    scripts = re.findall(r'<script\b[^>]*src="([^"]+)"', html)
    print("templates/page.html scripts:", scripts)
