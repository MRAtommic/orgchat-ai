# -*- coding: utf-8 -*-
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv('.env')

import database
from oauth2_service import oauth2_service
from googleapiclient.discovery import build

creds, src = oauth2_service.build_credentials(username='mxmm2547', org_id=1)
print(f"Creds source: {src}, valid: {creds.valid if creds else 'None'}")

sheets = build('sheets', 'v4', credentials=creds, cache_discovery=False)

# Check peak sheet
res = sheets.spreadsheets().values().get(
    spreadsheetId='1wu2hpyvMXaHrLC-Ulv7dK3fAz5m3G08-cejTodYYajk',
    range="'peak'!A1:X5"
).execute()

rows = res.get('values', [])
print(f"\n=== Peak Sheet ({len(rows)} rows) ===")
for i, r in enumerate(rows):
    print(f"Row {i}: {r[:5]}...")  # first 5 cols

# Check ใบเสร็จ sheet
res2 = sheets.spreadsheets().values().get(
    spreadsheetId='1wu2hpyvMXaHrLC-Ulv7dK3fAz5m3G08-cejTodYYajk',
    range="'ใบเสร็จ/ใบกำกับภาษี'!A1:X5"
).execute()

rows2 = res2.get('values', [])
print(f"\n=== ใบเสร็จ/ใบกำกับภาษี Sheet ({len(rows2)} rows) ===")
for i, r in enumerate(rows2):
    print(f"Row {i}: {r[:5]}...")

# Check สลิปโอนเงิน sheet
res3 = sheets.spreadsheets().values().get(
    spreadsheetId='1wu2hpyvMXaHrLC-Ulv7dK3fAz5m3G08-cejTodYYajk',
    range="'สลิปโอนเงิน'!A1:X5"
).execute()

rows3 = res3.get('values', [])
print(f"\n=== สลิปโอนเงิน Sheet ({len(rows3)} rows) ===")
for i, r in enumerate(rows3):
    print(f"Row {i}: {r[:5]}...")

# Check drive folder
drive = build('drive', 'v3', credentials=creds, cache_discovery=False)
tok_data = database.resolve_google_token('mxmm2547', 1)[0]
folder_id = tok_data.get('drive_folder_id')
print(f"\nDrive folder ID: {folder_id}")
if folder_id:
    results = drive.files().list(
        q=f"'{folder_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)",
        pageSize=10
    ).execute()
    files = results.get('files', [])
    print(f"Files in folder: {len(files)}")
    for f in files[:10]:
        print(f"  - {f['name']} ({f['mimeType']})")
