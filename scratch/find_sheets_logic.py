import os
import sys

# Define keywords to search
keywords = [
    "sheet", "worksheet", "wks", "spreadsheet", "gspread", "append_row",
    "upload", "line_bot", "line-bot", "google_drive", "drive_service", 
    "service-account", "credentials", "oauth2"
]

log_path = "scratch/sheets_logic_log.txt"

with open(log_path, "w", encoding="utf-8") as out:
    out.write("=== ORGCHAT AI - GOOGLE SHEETS / DRIVE / LINE SEARCH ===\n\n")
    
    for filename in os.listdir("."):
        if filename.endswith(".py") and filename != "clean_app.py":
            try:
                with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                
                # Check if any keyword matches
                lines = content.splitlines()
                matches = []
                for idx, line in enumerate(lines):
                    for kw in keywords:
                        if kw.lower() in line.lower():
                            matches.append((idx + 1, line.strip()))
                            break
                            
                if matches:
                    out.write(f"\n📁 FILE: {filename} ({len(matches)} matches)\n")
                    out.write("-" * 60 + "\n")
                    for line_num, text in matches:
                        out.write(f"{line_num}: {text}\n")
            except Exception as e:
                out.write(f"Error reading {filename}: {e}\n")

print(f"Search complete. Results written to {log_path}")
