import sys
import json
import re

sys.stdout.reconfigure(encoding='utf-8')

# Mock a raw malformed response (the one from the user's report)
raw_broken_response = """
{
  "category": "Slip",
  "smart_name": "Slip_29052026_ก```json
{
  "category": "Slip",
  "s"
"""

def parse_cleaned(full_response):
    try:
        # Clean response to get JSON
        full_response = full_response.strip()
        
        # Strip outer markdown blocks if present
        if full_response.startswith("```json"):
            full_response = full_response[7:].strip()
        if full_response.endswith("```"):
            full_response = full_response[:-3].strip()
            
        start_idx = full_response.find('{')
        end_idx = full_response.rfind('}')
        
        json_str = ""
        if start_idx != -1:
            if end_idx != -1:
                json_str = full_response[start_idx:end_idx+1]
            else:
                json_str = full_response[start_idx:]
                
        if json_str:
            try:
                # Use strict=False to allow control characters (tabs, newlines) inside strings
                return json.loads(json_str, strict=False)
            except Exception as e:
                # Clean nested markdown blocks if any
                cleaned = json_str
                cleaned = re.sub(r'```json\s*', '', cleaned)
                cleaned = re.sub(r'```\s*', '', cleaned)
                try:
                    return json.loads(cleaned, strict=False)
                except Exception:
                    pass
        
        # If we reach here, it failed to parse as JSON. Let's do a regex fallback on full_response!
        result = {
            "category": "Unknown",
            "extracted_data": {},
            "summary": "สแกนเอกสารสำเร็จ (ข้อมูลบางส่วนอาจคลาดเคลื่อน)"
        }
        
        # Use full_response or json_str as search target
        search_target = json_str or full_response
        
        # Extract category
        cat_match = re.search(r'"category"\s*:\s*"([^"]+)"', search_target)
        if cat_match:
            result["category"] = cat_match.group(1)
        else:
            # Try parsing from smart_name prefix
            name_match = re.search(r'"smart_name"\s*:\s*"([^"]+)"', search_target)
            if name_match:
                name_val = name_match.group(1)
                if "_" in name_val:
                    result["category"] = name_val.split("_")[0]
            
        # Extract net_amount
        amt_match = re.search(r'"net_amount"\s*:\s*([\d.]+)', search_target)
        if amt_match:
            try:
                result["extracted_data"]["net_amount"] = float(amt_match.group(1))
            except:
                pass
                
        # Extract sender
        sender_match = re.search(r'"sender"\s*:\s*"([^"]+)"', search_target)
        if sender_match:
            result["extracted_data"]["sender"] = sender_match.group(1)
            
        # Extract receiver
        receiver_match = re.search(r'"receiver"\s*:\s*"([^"]+)"', search_target)
        if receiver_match:
            result["extracted_data"]["receiver"] = receiver_match.group(1)

        # Extract date
        date_match = re.search(r'"date"\s*:\s*"([^"]+)"', search_target)
        if date_match:
            result["extracted_data"]["date"] = date_match.group(1)
            
        # Extract ref_number
        ref_match = re.search(r'"ref_number"\s*:\s*"([^"]+)"', search_target)
        if ref_match:
            result["extracted_data"]["ref_number"] = ref_match.group(1)

        # Extract summary
        sum_match = re.search(r'"summary"\s*:\s*"([^"]+)"', search_target)
        if sum_match:
            result["summary"] = sum_match.group(1)
            
        # If the category is STILL Unknown, but we see "Slip" or "Receipt" in the text, let's auto-detect it
        if result["category"] == "Unknown":
            lower_text = search_target.lower()
            if "slip" in lower_text or "สลิป" in lower_text:
                result["category"] = "Slip"
            elif "receipt" in lower_text or "ใบเสร็จ" in lower_text:
                result["category"] = "Receipt"
            elif "invoice" in lower_text or "ใบกำกับ" in lower_text:
                result["category"] = "Invoice"
                
        return result

    except Exception as e:
        return {"category": "Unknown", "extracted_data": {}, "summary": f"❌ JSON Parse Error: {str(e)} | Raw: {full_response[:100]}"}

parsed = parse_cleaned(raw_broken_response)
print("Parsed result:")
print(json.dumps(parsed, indent=2, ensure_ascii=False))
