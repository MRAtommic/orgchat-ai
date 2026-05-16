import os
import base64
import json
from dotenv import load_dotenv
import ai_providers

load_dotenv()

def test_extraction():
    img_path = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\uploads\social_feed\1778479579_ac6a93fec87fa2da6dc2aca161e1ad5d.jpg"
    
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        return

    with open(img_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"🚀 Testing extraction for: {os.path.basename(img_path)}")
    
    # Mocking the call to analyze_image_for_accounting
    # We need to set the environment variable if not present
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️ GEMINI_API_KEY not found in environment!")
        return

    result = ai_providers.analyze_image_for_accounting(image_data, "image/jpeg")
    
    print("\n--- AI RESPONSE ---")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("-------------------\n")
    
    # Check for banks
    banks_found = result.get('extracted_data', {}).get('sender_bank') != '-' or \
                  result.get('extracted_data', {}).get('receiver_bank') != '-'
    
    print(f"Bank Detection: {'✅ SUCCESS' if banks_found else '❌ FAILED'}")
    
    # Check for zero values
    wht = result.get('extracted_data', {}).get('wht_amount')
    print(f"WHT Amount: {wht} (Type: {type(wht)})")

if __name__ == "__main__":
    test_extraction()
