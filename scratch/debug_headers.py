import os
import json
from google_drive_service import GoogleWorkspaceManager

def debug_headers():
    manager = GoogleWorkspaceManager()
    spreadsheet_id = "1-FW2BexItxehvBmESWVLkb0IfkcUKqo8DUmCgy6MN6Q"
    sheet_name = "สลิปโอนเงิน"
    
    print(f"🔍 Reading headers for sheet: {sheet_name}")
    try:
        result = manager.sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A1:Z1"
        ).execute()
        headers = result.get('values', [[]])[0]
        print(f"📊 Actual Headers: {headers}")
        print(f"🔢 Header Count: {len(headers)}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_headers()
