import json

log_path = r"C:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\transcript.jsonl"
# Actually, the file is in the .system_generated/logs directory!
log_path = r"C:\Users\KC_Ketwilai\.gemini\antigravity-ide\brain\5f78a935-a010-40d3-9802-9e8c0ae3b1db\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            step = json.loads(line)
            content = step.get('content', '')
            if 'def create_batch_summary_flex_bubble' in content and 'def ' in content:
                print(f"Step {step.get('step_index')}:")
                # print first few lines of the match
                idx = content.find('def create_batch_summary_flex_bubble')
                print(content[idx:idx+1500])
                print("=" * 60)
        except Exception:
            pass
