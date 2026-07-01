import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Setup paths and load environment variables to run tools correctly
BASE_DIR = Path(__file__).parent.absolute()
sys.path.append(str(BASE_DIR.parent))
load_dotenv(BASE_DIR.parent / ".env", override=True, encoding="utf-8")

from google_drive_service import google_manager, GoogleWorkspaceManager

def run_now():
    try:
        # ย้ายตำแหน่งทำงานไปที่โฟลเดอร์ของสคริปต์ เพื่อให้หา credentials.json เจอ
        os.chdir(str(BASE_DIR))
        
        # ตั้งค่า Context เพื่อเชื่อมต่อ Google API
        google_manager.set_context("Admin", 1)
        
        service = google_manager.drive_service
        spreadsheet_name = "Digital_Assistant_Logs_V2"
        
        # 1. หา ID ของ Spreadsheet
        query = f"name = '{spreadsheet_name}' and mimeType = 'application/vnd.google-apps.spreadsheet' and trashed = false"
        results = service.files().list(q=query, fields="files(id)").execute()
        files = results.get('files', [])
        
        if not files:
            print("❌ ไม่พบ Spreadsheet ชื่อ Digital_Assistant_Logs_V2")
            return
            
        spreadsheet_id = files[0]['id']
        print(f"🔍 พบ Spreadsheet ID: {spreadsheet_id}")
        print("⏳ กำลังเริ่มกระทบยอดไฟล์เดิม...")
        
        # ตั้งค่า spreadsheet_id บน google_manager และสั่งกระทบยอดจริง
        google_manager.spreadsheet_id = spreadsheet_id
        google_manager.auto_reconcile_internal()
        
        print("✅ กระทบยอดเสร็จเรียบร้อย! กรุณาเช็คใน Tab 'กระทบยอด (Auto)' ใน Google Sheet ครับ")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    run_now()
