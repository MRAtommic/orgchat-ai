import os
import json

log_dir = r"C:\Users\KC_Ketwilai\.gemini\antigravity-ide\brain\7796d7dd-c4bd-488e-a79a-e92d2da994b8\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript.jsonl")

if os.path.exists(transcript_path):
    print("Found transcript!")
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            # Find steps that viewed index.html
            if data.get('type') == 'VIEW_FILE' or 'index.html' in str(data):
                # Print a snippet to verify
                content = data.get('content', '')
                if 'Google Drive & Sheets Connection' in content:
                    print(f"Found step: {data.get('step_index')}")
                    # Save this content to a backup file
                    with open(f"backup_step_{data.get('step_index')}.txt", 'w', encoding='utf-8') as bf:
                        bf.write(content)
else:
    print("Transcript not found at:", transcript_path)
