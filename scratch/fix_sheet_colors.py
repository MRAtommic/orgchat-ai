
import os
from google_drive_service import GoogleDriveService
from dotenv import load_dotenv

load_dotenv()

def fix_colors():
    spreadsheet_id = os.getenv("SPREADSHEET_ID")
    if not spreadsheet_id:
        print("❌ ไม่พบ SPREADSHEET_ID ใน .env")
        return

    print(f"🔄 กำลังแก้ไขสีใน Sheet: {spreadsheet_id}...")
    
    try:
        drive_service = GoogleDriveService()
        sheets_service = drive_service.sheets_service
        
        # ดึงข้อมูล Spreadsheet เพื่อหา Sheet ID ของ Tab 'บัตรประชาชน'
        spreadsheet = sheets_service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        tab_found = False
        for sheet in spreadsheet.get('sheets', []):
            title = sheet['properties']['title']
            if 'บัตรประชาชน' in title or 'id' in title.lower():
                sheet_id = sheet['properties']['sheetId']
                print(f"✨ พบ Tab: {title} (ID: {sheet_id})")
                
                # สร้าง Request เพื่ออัปเดตสูตร
                requests = [
                    {
                        "updateConditionalFormatRule": {
                            "index": 0,
                            "rule": {
                                "ranges": [{"sheetId": sheet_id, "startRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 15}],
                                "booleanRule": {
                                    "condition": {
                                        "type": "CUSTOM_FORMULA",
                                        "values": [{"userEnteredValue": "=AND($M2<>\"\", $M2 < TODAY())"}]
                                    },
                                    "format": {
                                        "backgroundColor": {"red": 1.0, "green": 0.85, "blue": 0.85}, 
                                        "textFormat": {"foregroundColor": {"red": 0.7, "green": 0.0, "blue": 0.0}, "bold": True}
                                    }
                                }
                            }
                        }
                    }
                ]
                
                sheets_service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body={'requests': requests}).execute()
                print(f"✅ แก้ไขสูตรใน Tab '{title}' เรียบร้อยแล้ว!")
                tab_found = True
        
        if not tab_found:
            print("⚠️ ไม่พบ Tab ที่เกี่ยวกับบัตรประชาชน")
            
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")

if __name__ == "__main__":
    fix_colors()
