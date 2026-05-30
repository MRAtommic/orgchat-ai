import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from google_drive_service import google_manager

# Set context to None so it falls back to GOOGLE_SERVICE_ACCOUNT_JSON
google_manager.set_context(username=None, org_id=None)

print("=== Listing ALL folders in Service Account's Drive ===")
try:
    # Build a temporary service using the service account creds directly
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    import json
    
    info = json.loads(os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON"))
    creds = service_account.Credentials.from_service_account_info(info, scopes=google_manager.scopes)
    drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)
    
    query = "mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = drive_service.files().list(q=query, fields="files(id, name, parents)", supportsAllDrives=True).execute()
    folders = results.get('files', [])
    print(f"Total folders found: {len(folders)}")
    for f in folders:
        print(f"- {f['name']} (ID: {f['id']}), Parents: {f.get('parents')}")
        
    print("\n=== Listing children of parent_folder_id 1CxDshFuM17fTVSSKtSS_DZoMOdhl7iGa ===")
    p_query = "'1CxDshFuM17fTVSSKtSS_DZoMOdhl7iGa' in parents and trashed = false"
    p_results = drive_service.files().list(q=p_query, fields="files(id, name, mimeType)", supportsAllDrives=True).execute()
    p_files = p_results.get('files', [])
    print(f"Files inside parent folder: {len(p_files)}")
    for pf in p_files:
        print(f"- {pf['name']} ({pf['mimeType']} ID: {pf['id']})")
except Exception as e:
    import traceback
    traceback.print_exc()
