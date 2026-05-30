with open("templates/index.html", "r", encoding="utf-8") as f:
    html = f.read()

import re
scripts = re.findall(r'<script\b[^>]*src="([^"]+)"', html)
print("Scripts with src:", scripts)
