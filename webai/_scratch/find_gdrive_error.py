import os

# We will search both static/app.js and templates/index.html and any other file in the workspace
out = []

search_dirs = [".", "static", "templates", "routes"]
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith((".js", ".html", ".py", ".txt")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if "ไม่สามารถโหลดข้อมูล Google Drive ได้" in line:
                            out.append(f"{path}:{i+1}: {line.strip()}")
            except Exception:
                pass

with open("_scratch/find_gdrive_error_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
