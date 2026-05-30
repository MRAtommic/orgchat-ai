# -*- coding: utf-8 -*-
import fitz  # PyMuPDF
import os
import glob
import re
import sys

# Reconfigure stdout to use UTF-8
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ"
pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

print(f"Found {len(pdf_files)} PDF files to inspect.\n")

for pdf_path in sorted(pdf_files):
    filename = os.path.basename(pdf_path)
    print("=" * 60)
    print(f"FILE: {filename}")
    print("=" * 60)
    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        
        # Print first few hundred characters
        # print(full_text[:300])
        # print("-" * 40)
        
        # Search for key metadata
        # 1. Total amounts
        amounts = re.findall(r'(?:สุทธิ|รวมทั้งสิ้น|จำนวนเงิน|ยอดรวม|total|grand total|net|amount|sum|vat|ภาษีมูลค่าเพิ่ม|หัก|wht|ณ ที่จ่าย|3%|2%)\s*:?\s*[\d,]+\.?\d*', full_text, re.IGNORECASE)
        print("💡 Key matched terms:")
        seen = set()
        count = 0
        for amt in amounts:
            clean = amt.strip().replace('\n', ' ')
            if clean not in seen and len(clean) > 3:
                seen.add(clean)
                print(f"   - {clean}")
                count += 1
                if count >= 15:
                    break
        
        if count == 0:
            print("📝 Extracted Text Snippet:")
            print(full_text[:600].strip())
        
        # Search for dates
        dates = re.findall(r'(?:\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4}|\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+\d{4})', full_text)
        if dates:
            print(f"📅 Extracted Dates: {list(set(dates))}")
            
    except Exception as e:
        print(f"❌ Error parsing {filename}: {e}")
    print("\n")
