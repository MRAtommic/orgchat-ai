# -*- coding: utf-8 -*-
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Reconfigure stdout to use UTF-8 (resilient against Windows encoding issues)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Setup paths and env
BASE_DIR = Path(__file__).parent.absolute()
sys.path.append(str(BASE_DIR))
load_dotenv(BASE_DIR.parent / ".env", override=True)

import ai_providers
import google_drive_service
import database
from google_drive_service import google_manager
google_manager.set_context("Admin", 1)

CACHE_FILE = BASE_DIR / "processed_files_cache.json"

def load_processed_cache():
    """Loads the set of already processed files from local JSON cache."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception as e:
            print(f"⚠️ Warning: Could not load processed cache: {e}")
            return set()
    return set()

def save_processed_cache(processed_set):
    """Saves the set of already processed files to local JSON cache."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(list(processed_set), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ Error saving cache: {e}")

def process_files_in_folder(folder_path, sheet_name):
    print(f"\n📂 Scanning folder: {folder_path} for {sheet_name}")
    if not os.path.exists(folder_path):
        print(f"❌ Folder not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png'))]
    print(f"📄 Found {len(files)} files in folder.")

    processed_cache = load_processed_cache()
    
    # Filter only truly new files using sheet_name + filename as unique key
    new_files = [f for f in files if f"{sheet_name}:{f}" not in processed_cache]
    skipped_count = len(files) - len(new_files)
    
    if skipped_count > 0:
        print(f"⚡ Skipped {skipped_count} already processed files (saving tokens!).")
        
    print(f"🆕 {len(new_files)} new files to process.")

    if not new_files:
        return

    for filename in new_files:
        file_path = os.path.join(folder_path, filename)
        print(f"--- Processing: {filename} ---")
        try:
            with open(file_path, 'rb') as f:
                image_data = f.read()
            
            mime = "application/pdf" if filename.lower().endswith('.pdf') else "image/jpeg"
            
            # Upload to Google Drive
            print(f"☁️ Uploading {filename} to Google Drive...")
            link, upload_err = google_manager.upload_file(image_data, filename, mime)
            if upload_err:
                print(f"⚠️ Drive upload error: {upload_err}")
                file_link = f"Local: {filename}"
            else:
                print(f"🚀 Uploaded to Google Drive: {link}")
                file_link = link

            # Use AI to analyze
            result = ai_providers.analyze_media_contents(image_data, mime)
            
            if result and 'extracted_data' in result:
                # Add metadata
                result['file_link'] = file_link
                result['original_name'] = filename
                result['ai_model'] = result.get('ai_model', 'Gemini-2.0-Flash')
                
                # Log to Google Sheets
                google_manager.log_expense(result, sheet_name=sheet_name)
                print(f"✅ Logged to '{sheet_name}'")

                # ALSO: Log to local database for Dashboard stats
                try:
                    ext = result.get('extracted_data', {})
                    amt = ext.get('net_amount', 0)
                    if not amt or amt == '-': amt = 0
                    try: 
                        if isinstance(amt, str):
                            amt = float(amt.replace(',', '').replace('฿', '').strip())
                        else:
                            amt = float(amt)
                    except: amt = 0.0
                    
                    database.add_drive_log(
                        filename=filename,
                        category=ext.get('category', sheet_name),
                        amount=amt,
                        doc_date=ext.get('date'),
                        summary=result.get('summary', f"Reconcile Tool: {filename}"),
                        file_link=file_link
                    )
                except Exception as dbe:
                    print(f"⚠️ Local DB log error: {dbe}")
                
                # Add to cache and save immediately
                processed_cache.add(f"{sheet_name}:{filename}")
                save_processed_cache(processed_cache)
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
