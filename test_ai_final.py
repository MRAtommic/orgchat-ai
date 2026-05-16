import os
import ai_providers
from dotenv import load_dotenv

load_dotenv()

def test_file(file_path, mime_type):
    print(f"\n--- Testing File: {os.path.basename(file_path)} ---")
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    with open(file_path, "rb") as f:
        image_data = f.read()

    try:
        result = ai_providers.analyze_image_contents(image_data, mime_type)
        import json
        print(json.dumps(result, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error analyzing file: {e}")

# Test 1: Thunnaksilp (Previously missed Tax ID)
test_file(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ใบเสร็จรับเงิน - ใบกำกับภาษี\scan (1).pdf", "application/pdf")

# Test 2: A Slip (To check format)
test_file(r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\สลิปโอนเงิน\S__30482435 (1).jpg", "image/jpeg")
