# -*- coding: utf-8 -*-
import fitz
import os
import glob
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ทดสอบ พงด\ใบกำกับ"
pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

print(f"Total PDFs found: {len(pdf_files)}")

for pdf_path in sorted(pdf_files):
    filename = os.path.basename(pdf_path)
    print("\n" + "="*80)
    print(f"FILE: {filename}")
    print("="*80)
    try:
        doc = fitz.open(pdf_path)
        text_content = []
        for i, page in enumerate(doc):
            text = page.get_text()
            text_content.append(text)
        
        full_text = "\n--- Page Separator ---\n".join(text_content)
        
        # Print a structured preview or full text if short
        lines = [line.strip() for line in full_text.split("\n") if line.strip()]
        print(f"Total non-empty lines: {len(lines)}")
        
        # Let's search for interesting substrings like business names, tax IDs, dates, numbers
        tax_ids = re.findall(r'\b\d{13}\b', full_text)
        print(f"Tax IDs found: {list(set(tax_ids))}")
        
        # Let's print the first 60 lines of the extracted text
        print("--- EXTRACTED TEXT (FIRST 60 LINES) ---")
        for line in lines[:60]:
            print(f"  {line}")
            
    except Exception as e:
        print(f"Error parsing: {e}")
