import sys
sys.stdout.reconfigure(encoding='utf-8')
from google_drive_service import google_manager

def inspect():
    try:
        spreadsheet = google_manager.sheets_service.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
        sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        print("Active sheets:", sheet_titles)
        
        for name in ["ใบเสร็จ/ใบกำกับภาษี", "peak"]:
            if name in sheet_titles:
                res = google_manager.sheets_service.spreadsheets().values().get(
                    spreadsheetId=google_manager.spreadsheet_id, range=f"'{name}'!A1:Z100"
                ).execute()
                vals = res.get('values', [])
                print(f"\n=== Sheet: {name} ===")
                print(f"Total rows retrieved: {len(vals)}")
                if len(vals) > 0:
                    print("Headers:", vals[0])
                for idx, row in enumerate(vals[1:6]):
                    print(f"Row {idx+1}: {row}")
            else:
                print(f"\nSheet {name} NOT found in spreadsheet")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    inspect()
