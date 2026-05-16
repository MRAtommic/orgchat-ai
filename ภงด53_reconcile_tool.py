# -*- coding: utf-8 -*-
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Setup paths and env
BASE_DIR = Path(__file__).parent.absolute()
sys.path.append(str(BASE_DIR))
load_dotenv(BASE_DIR / ".env", override=True)

import ai_providers
import google_drive_service
from google_drive_service import google_manager

def process_files_in_folder(folder_path, sheet_name):
    print(f"\n📂 Scanning folder: {folder_path} for {sheet_name}")
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png'))]
    print(f"📄 Found {len(files)} files.")

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        print(f"--- Processing: {filename} ---")
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            mime = "application/pdf" if filename.lower().endswith('.pdf') else "image/jpeg"
            
            # Use AI to analyze
            result = ai_providers.analyze_image_contents(image_data, mime)
            
            if result and 'extracted_data' in result:
                # Add metadata
                result['file_link'] = f"Local: {filename}"
                result['ai_model'] = result.get('ai_model', 'Gemini-2.0-Flash')
                
                # Log to Google Sheets
                google_manager.log_expense(result, sheet_name=sheet_name)
                print(f"✅ Logged to '{sheet_name}'")
            else:
                print(f"⚠️ AI failed to extract data from {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    # Folders
    invoice_folder = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\ใบเสร็จรับเงิน - ใบกำกับภาษี"
    slip_folder = r"c:\Users\KC_Ketwilai\Downloads\orgchat-ai-main\orgchat-ai-main\webai\ภงด.53\สลิปโอนเงิน"

    # 1. Process Invoices
    process_files_in_folder(invoice_folder, "ใบเสร็จ/ใบกำกับภาษี")

    # 2. Process Slips
    process_files_in_folder(slip_folder, "สลิปโอนเงิน")

    # 3. Trigger Reconciliation
    print("\n🎯 Triggering Smart Reconciliation...")
    google_manager.auto_reconcile_internal()
    print("✨ Process Complete! Please check your Google Sheets.")
