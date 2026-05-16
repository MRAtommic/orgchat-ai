import os
import sys
from google_drive_service import google_manager, GoogleWorkspaceManager

def run_now():
    try:
        # ย้ายตำแหน่งทำงานไปที่โฟลเดอร์ของสคริปต์ เพื่อให้หา credentials.json เจอ
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        service = google_manager.drive_service
        sheets_service = google_manager.sheets_service
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
        
        google_drive_service.perform_auto_reconciliation(sheets_service, spreadsheet_id)
        
        print("✅ กระทบยอดเสร็จเรียบร้อย! กรุณาเช็คใน Tab 'กระทบยอด (Auto)' ใน Google Sheet ครับ")
        
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    run_now()
