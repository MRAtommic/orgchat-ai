# -*- coding: utf-8 -*-
import fitz
import os
import glob
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ"
pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

out_file = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\_scratch\verify_results.txt"

with open(out_file, "w", encoding="utf-8") as f:
    f.write(f"Total PDFs found: {len(pdf_files)}\n")
    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        f.write("\n" + "="*80 + "\n")
        f.write(f"FILE: {filename}\n")
        f.write("="*80 + "\n")
        try:
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            
            # Extract basic information
            # Tax IDs (13 digits)
            tax_ids = re.findall(r'\b\d{13}\b', full_text)
            f.write(f"Tax IDs: {list(set(tax_ids))}\n")
            
            # Dates
            dates = re.findall(r'(?:\d{1,2}[/\-.]\d{1,2}[/\-.]\d{4}|\d{1,2}\s+(?:ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.|มกราคม|กุมภาพันธ์|มีนาคม|เมษายน|พฤษภาคม|มิถุนายน|กรกฎาคม|สิงหาคม|กันยายน|ตุลาคม|พฤศจิกายน|ธันวาคม)\s+\d{4})', full_text)
            f.write(f"Dates: {list(set(dates))}\n")
            
            # Lines containing numbers that look like money
            money_lines = []
            for line in full_text.split("\n"):
                line = line.strip()
                if not line:
                    continue
                # If the line contains a number with a comma or dot and is short, or contains numbers
                if re.search(r'\d+,\d{3}', line) or re.search(r'\d+\.\d{2}', line) or any(k in line.lower() for k in ["บาท", "สุทธิ", "total", "vat", "ภาษี", "หัก", "จ่าย", "บจ", "บริษัท"]):
                    money_lines.append(line)
            
            f.write("Interesting Lines:\n")
            for ml in money_lines[:25]:
                f.write(f"  {ml}\n")
                
            if not money_lines:
                f.write("No text extracted (scanned image?)\n")
                
        except Exception as e:
            f.write(f"Error parsing: {e}\n")

print("Saved report to verify_results.txt")
