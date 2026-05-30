# -*- coding: utf-8 -*-
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

log_path = r"C:\Users\KC_Ketwilai\ .gemini\antigravity-ide\brain\7796d7dd-c4bd-488e-a79a-e92d2da994b8\.system_generated\logs\transcript.jsonl".replace(" ", "")

with open(log_path, encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        content = data.get("content", "")
        tool_calls = json.dumps(data.get("tool_calls", []))
        if "verify_gogoprint" in content or "verify_gogoprint" in tool_calls:
            print(f"=== STEP {data.get('step_index')} ({data.get('source')}) ===")
            if content:
                print(content[:300])
            if data.get("tool_calls"):
                print("Tool calls:", data.get("tool_calls"))
            print()
