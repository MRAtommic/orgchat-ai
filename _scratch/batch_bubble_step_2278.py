import json

log_path = r"C:\Users\KC_Ketwilai\.gemini\antigravity-ide\brain\5f78a935-a010-40d3-9802-9e8c0ae3b1db\.system_generated\logs\transcript.jsonl"

print("Searching for paired / batch functions...")
with open(log_path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        try:
            step = json.loads(line)
            content = step.get('content', '')
            if 'def create_paired_expense_flex_bubble' in content:
                print(f"Found 'def create_paired_expense_flex_bubble' in step {step.get('step_index')}")
            if 'def create_batch_summary_flex_bubble' in content:
                print(f"Found 'def create_batch_summary_flex_bubble' in step {step.get('step_index')}")
            if 'def _get_item_flex_block' in content:
                print(f"Found 'def _get_item_flex_block' in step {step.get('step_index')}")
        except Exception as e:
            pass
