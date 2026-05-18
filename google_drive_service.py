"""
Google Drive & Sheets Service Manager
-------------------------------------
Handles all interactions with Google Workspace APIs including file uploads, 
logging to spreadsheets, and automated reconciliation.
"""

import os
import re
import io
import time
import threading
import logging
import difflib
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError
from google.oauth2 import service_account
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def normalize_thai_name(name):
    """Cleans up Thai business names for better matching, stripping special characters."""
    if not name or name == '-': return ""
    name = str(name).upper()
    # Remove common business prefixes/suffixes
    for word in ['บจก.', 'บริษัท', 'จำกัด', ' (มหาชน)', '(มหาชน)', 'CO.,LTD.', 'CO., LTD.', 'LTD.', 'CORP.', 'หจก.', 'ห้างหุ้นส่วนจำกัด']:
        name = name.replace(word, '')
    
    # Remove special characters often found in statements (++, *, -, etc.)
    name = re.sub(r'[^\u0E01-\u0E5B\w]', '', name)
    return name.strip()

def get_name_similarity(name1, name2):
    """Returns a similarity score between 0 and 1 for two names."""
    n1 = normalize_thai_name(name1)
    n2 = normalize_thai_name(name2)
    if not n1 or not n2: return 0.0
    if n1 in n2 or n2 in n1: return 1.0
    return difflib.SequenceMatcher(None, n1, n2).ratio()

class GoogleWorkspaceManager:
    """
    Singleton Manager for Google Workspace interactions.
    Manages API clients and provides high-level utilities for Drive and Sheets.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(GoogleWorkspaceManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.credentials_path = 'service-account.json'
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self.drive_service = None
        self.sheets_service = None
        self.parent_folder_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
        
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        self._initialize_services()
        self._validate_or_create_spreadsheet()
        self._initialized = True

    def _load_sheet_schema(self):
        """Loads sheet schema configuration from json or returns built-in fallback."""
        import json
        config_path = os.path.join(os.path.dirname(__file__), 'config', 'sheet_schema.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load sheet schema registry JSON: {e}")
        
        # Resilient fallback matching config/sheet_schema.json
        return {
            "category_map": {
                "Slip": "สลิปโอนเงิน",
                "Transfer": "สลิปโอนเงิน",
                "Receipt": "ใบเสร็จ/ใบกำกับภาษี",
                "Invoice": "ใบเสร็จ/ใบกำกับภาษี",
                "Voucher": "ใบเสร็จ/ใบกำกับภาษี",
                "ใบเสร็จ_ใบกำกับ": "ใบเสร็จ/ใบกำกับภาษี",
                "ใบเสร็จรับเงิน - ใบกำกับภาษี": "ใบเสร็จ/ใบกำกับภาษี",
                "Statement": "สเตตเมนต์",
                "statement": "สเตตเมนต์",
                "ID_Card": "บัตรประชาชน",
                "slip": "สลิปโอนเงิน",
                "Uploads": "สลิปโอนเงิน"
            },
            "schemas": {
                "บัตรประชาชน": {
                    "headers": ["เวลาที่บันทึก", "หมวดหมู่", "วันที่บันทึก", "เวลาที่บันทึก", "AI Model", "เลขบัตรประชาชน", "ชื่อ (ไทย)", "นามสกุล (ไทย)", "ชื่อ (อังกฤษ)", "นามสกุล (อังกฤษ)", "วันเกิด", "เพศ", "ที่อยู่", "วันหมดอายุ", "Laser ID", "ลิงก์ไฟล์", "AI ถูก/ผิด"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:ID_Card"},
                        {"source": "current_date"},
                        {"source": "current_time"},
                        {"source": "ai_model"},
                        {"source": "ai_keys:id_number,tax_id", "cleaner": "id"},
                        {"source": "id_card_first_name_th"},
                        {"source": "id_card_last_name_th"},
                        {"source": "ai_keys:first_name_en,name_en"},
                        {"source": "ai_keys:last_name_en,surname_en"},
                        {"source": "ai_keys:birth_date,birthday,dob"},
                        {"source": "ai_keys:gender,sex"},
                        {"source": "ai_keys:address"},
                        {"source": "ai_keys:expiry_date,expired_date,expiry"},
                        {"source": "ai_keys:laser_id,laser,ref_number"},
                        {"source": "file_link"},
                        {"source": "const:-"}
                    ]
                },
                "สเตตเมนต์": {
                    "headers": ["เวลาที่บันทึก", "วันที่เอกสาร", "เวลา/วันที่มีผล", "รายการ", "รายละเอียด", "ถอน/เงินออก", "ฝาก/เงินเข้า", "ค่าธรรมเนียม", "ยอดคงเหลือ", "ช่องทาง", "เลขที่อ้างอิง", "คู่ค้า/ผู้โอน", "ลิงก์ไฟล์"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "statement_date"},
                        {"source": "statement_time"},
                        {"source": "ai_keys:memo,description,รายการ"},
                        {"source": "ai_keys:details,info,รายละเอียด"},
                        {"source": "ai_keys:withdrawal,ถอน,out", "cleaner": "float"},
                        {"source": "ai_keys:deposit,ฝาก,in", "cleaner": "float"},
                        {"source": "ai_keys:fee,ค่าธรรมเนียม", "cleaner": "float"},
                        {"source": "ai_keys:balance,ยอดคงเหลือ", "cleaner": "float"},
                        {"source": "statement_channel"},
                        {"source": "ai_keys:ref,ref_number,เลขที่อ้างอิง", "cleaner": "id"},
                        {"source": "ai_keys:counterparty,sender,receiver,คู่ค้า"},
                        {"source": "file_link"}
                    ]
                },
                "ใบเสร็จ/ใบกำกับภาษี": {
                    "headers": ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "ผู้ส่ง/ร้านค้า", "รหัสสาขา", "เลขผู้เสียภาษี", "ที่อยู่คู่ค้า", "ผู้รับ", "ช่องทางการติดต่อ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "ส่วนลด", "VAT", "WHT", "ประเภท WHT", "เลขที่อ้างอิง", "สรุปจาก AI", "ลิงก์ไฟล์", "AI ถูก/ผิด"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:ใบเสร็จ/ใบกำกับภาษี"},
                        {"source": "ai_keys:date"},
                        {"source": "sender_name_fallback"},
                        {"source": "ai_keys:branch"},
                        {"source": "ai_keys:tax_id", "cleaner": "id"},
                        {"source": "ai_keys:address"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:contact,phone,email"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:gross_amount", "cleaner": "float"},
                        {"source": "ai_keys:discount_amount", "cleaner": "float"},
                        {"source": "ai_keys:vat_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_type,wht_category,wht_rate,wht_percent"},
                        {"source": "ai_keys:ref_number"},
                        {"source": "summary"},
                        {"source": "file_link"},
                        {"source": "const:-"}
                    ]
                },
                "สลิปโอนเงิน": {
                    "headers": ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "เวลาในเอกสาร", "ผู้ส่ง/ร้านค้า", "เลขผู้เสียภาษี", "ผู้รับ", "ช่องทางการติดต่อ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "WHT", "เลขที่อ้างอิง", "ธนาคารต้นทาง", "ธนาคารปลายทาง", "บันทึกช่วยจำ", "สรุปจาก AI", "ลิงก์ไฟล์", "AI ถูก/ผิด"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:สลิปโอนเงิน"},
                        {"source": "ai_keys:date"},
                        {"source": "ai_keys:time"},
                        {"source": "sender_name_fallback"},
                        {"source": "ai_keys:tax_id", "cleaner": "id"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:contact,phone"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:gross_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_amount", "cleaner": "float"},
                        {"source": "ai_keys:ref_number"},
                        {"source": "ai_keys:sender_bank,bank_from"},
                        {"source": "ai_keys:receiver_bank,bank_to"},
                        {"source": "ai_keys:memo"},
                        {"source": "summary"},
                        {"source": "file_link"},
                        {"source": "const:-"}
                    ]
                },
                "ใบเสนอราคา": {
                    "headers": ["เวลาที่บันทึก", "วันที่เอกสาร", "ผู้เสนอราคา", "ลูกค้า", "ยอดเงินสุทธิ", "สถานะ", "ลิงก์ไฟล์", "AI ถูก/ผิด"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "ai_keys:date"},
                        {"source": "sender_name_fallback"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "const:รออนุมัติ"},
                        {"source": "file_link"},
                        {"source": "const:-"}
                    ]
                },
                "default": {
                    "headers": ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "สรุปข้อมูล", "ลิงก์ไฟล์", "AI ถูก/ผิด"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "sheet_name"},
                        {"source": "ai_keys:date"},
                        {"source": "summary"},
                        {"source": "file_link"},
                        {"source": "const:-"}
                    ]
                }
            }
        }


    def get_date_header_name(self, sheet_name):
        """Dynamically look up the date column header from the schema registry."""
        try:
            registry = self._load_sheet_schema()
            schemas = registry.get("schemas", {})
            schema_config = schemas.get(sheet_name, schemas.get("default", {}))
            for col in schema_config.get("columns", []):
                src = col.get("source", "")
                if src in ["ai_keys:date", "current_date", "statement_date"] or "date" in src:
                    return col.get("header", "วันที่ในเอกสาร")
            return "วันที่ในเอกสาร"
        except Exception:
            return "วันที่ในเอกสาร"

    def _initialize_services(self):
        """Initializes Google API clients."""
        try:
            creds = None
            token_path = 'token.json'
            if os.path.exists(token_path):
                from google.oauth2.credentials import Credentials
                from google.auth.transport.requests import Request
                creds = Credentials.from_authorized_user_file(token_path, self.scopes)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                logger.info("Using token.json (OAuth2 User) for Drive services.")

            if not creds or not creds.valid:
                g_env = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
                if g_env:
                    try:
                        import json
                        info = json.loads(g_env)
                        creds = service_account.Credentials.from_service_account_info(
                            info, scopes=self.scopes
                        )
                        logger.info("Using GOOGLE_SERVICE_ACCOUNT_JSON from environment variable for Drive/Sheets.")
                    except Exception as e:
                        logger.error(f"Failed to load credentials from environment variable: {e}")

                if (not creds or not creds.valid) and os.path.exists(self.credentials_path):
                    creds = service_account.Credentials.from_service_account_file(
                        self.credentials_path, scopes=self.scopes
                    )
                    logger.info("Using service-account.json file for Drive services.")
                
                if not creds or not creds.valid:
                    logger.error("No valid credentials found.")
                    return

            self.drive_service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            self.sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")

    def _validate_or_create_spreadsheet(self):
        """Checks if the current spreadsheet exists, otherwise creates a new one."""
        if not self.sheets_service: return
        
        valid = False
        if self.spreadsheet_id:
            try:
                meta = self.drive_service.files().get(fileId=self.spreadsheet_id, fields='trashed', supportsAllDrives=True).execute()
                if not meta.get('trashed', False):
                    self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                    valid = True
                else:
                    logger.warning(f"⚠️ Spreadsheet {self.spreadsheet_id} is in TRASH. Creating new one...")
            except HttpError as he:
                if he.resp.status == 404:
                    logger.warning(f"⚠️ Spreadsheet ID {self.spreadsheet_id} not found on Google Drive (404). Creating a new one...")
                elif he.resp.status in [403, 401]:
                    logger.error(f"❌ Permission denied or unauthorized to access spreadsheet {self.spreadsheet_id} (HTTP {he.resp.status}). Keeping current ID.")
                    valid = True
                else:
                    logger.warning(f"⚠️ Google Sheets API returned HTTP {he.resp.status} during check: {he}. Keeping current ID.")
                    valid = True
            except Exception as e:
                # Resilient: Network timeouts, transient errors, socket issues.
                # NEVER create a new spreadsheet for transient network issues!
                logger.warning(f"⚠️ Transient network/timeout error checking spreadsheet {self.spreadsheet_id}: {e}. Keeping current ID.")
                valid = True
        
        if not valid:
            self._create_new_spreadsheet()

    def _create_new_spreadsheet(self):
        """Creates a new spreadsheet with Thai headers."""
        try:
            spreadsheet_body = {'properties': {'title': 'Digital_Assistant_Logs_V2'}}
            request = self.sheets_service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId')
            response = request.execute()
            new_id = response.get('spreadsheetId')
            
            headers = [
                "เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "เวลาในเอกสาร", "ผู้ส่ง/ร้านค้า",
                "เลขผู้เสียภาษี", "ผู้รับ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "VAT",
                "WHT", "ประเภท WHT", "เลขที่อ้างอิง", "ธนาคารต้นทาง", "ธนาคารปลายทาง",
                "บันทึกช่วยจำ", "สรุปจาก AI", "ลิงก์ไฟล์", "AI ถูก/ผิด"
            ]
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=new_id, range="A1",
                valueInputOption="RAW", body={"values": [headers]}
            ).execute()
            
            # Update .env
            env_path = os.path.join(os.path.dirname(__file__), '.env')
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                with open(env_path, 'w', encoding='utf-8') as f:
                    updated = False
                    for line in lines:
                        if line.startswith("SPREADSHEET_ID="):
                            f.write(f"SPREADSHEET_ID={new_id}\n")
                            updated = True
                        else:
                            f.write(line)
                    if not updated:
                        f.write(f"\nSPREADSHEET_ID={new_id}\n")
            
            os.environ["SPREADSHEET_ID"] = new_id
            self.spreadsheet_id = new_id
            logger.info(f"🚀 Created new Spreadsheet: {new_id}")
        except Exception as e:
            logger.error(f"❌ Failed to create new spreadsheet: {e}")

    def upload_file(self, file_content, filename, mimetype, folder_id=None):
        """Uploads file with Year/Month/Day folder structure."""
        if not self.drive_service: return None, "Service not initialized"
        try:
            base_p_id = folder_id or self.parent_folder_id
            now = datetime.now()
            year_str, month_str, day_str = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")
            
            p_id = base_p_id
            for folder_name in [year_str, month_str, day_str]:
                p_id = self._get_or_create_folder(folder_name, p_id)

            file_metadata = {'name': filename, 'parents': [p_id]}
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mimetype, resumable=True)
            file = self.drive_service.files().create(
                body=file_metadata, media_body=media, fields='id, webViewLink', supportsAllDrives=True
            ).execute()
            return file.get('webViewLink'), None
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return None, str(e)

    def rename_file(self, file_id, new_name):
        if not self.drive_service: return False, "Service not initialized"
        try:
            self.drive_service.files().update(fileId=file_id, body={'name': new_name}, supportsAllDrives=True).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def delete_file(self, file_id):
        if not self.drive_service: return False, "Service not initialized"
        try:
            self.drive_service.files().update(fileId=file_id, body={'trashed': True}, supportsAllDrives=True).execute()
            return True, None
        except Exception as e:
            return False, str(e)

    def _get_or_create_folder(self, folder_name, parent_id):
        query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive_service.files().list(q=query, fields="files(id)", supportsAllDrives=True).execute()
        files = results.get('files', [])
        if files: return files[0]['id']
        
        metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
        folder = self.drive_service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()
        return folder.get('id')

    def list_subfolders(self, parent_id=None):
        if not self.drive_service: return []
        p_id = parent_id or self.parent_folder_id
        try:
            query = f"'{p_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
            results = self.drive_service.files().list(q=query, fields="files(id, name)", supportsAllDrives=True).execute()
            return results.get('files', [])
        except: return []

    def auto_reconcile_internal(self):
        """Matches Payment Slips with Invoices in the current Spreadsheet."""
        if not self.sheets_service or not self.spreadsheet_id: return
        try:
            # 0. ตรวจสอบก่อนว่ามี Sheet หรือไม่ เพื่อป้องกัน Error 400
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]

            # 1. Read Payments (สลิปโอนเงิน + สเตตเมนต์)
            payments = []
            # 1. โหลดข้อมูลสลิป
            if "สลิปโอนเงิน" in sheet_titles:
                try:
                    res_slip = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range="'สลิปโอนเงิน'!A1:S").execute()
                    vals = res_slip.get('values', [])
                    if vals:
                        header_row = vals[0]
                        data_rows = vals[1:]
                        
                        # หาตำแหน่งคอลัมน์แบบไดนามิก
                        idx_date = next((i for i, h in enumerate(header_row) if "วันที่" in h), 2)
                        idx_amt = next((i for i, h in enumerate(header_row) if "จำนวนเงิน" in h or "สุทธิ" in h), 8)
                        idx_rec = next((i for i, h in enumerate(header_row) if "ผู้รับ" in h), 4)
                        idx_link = next((i for i, h in enumerate(header_row) if "ลิงก์" in h), 16)

                        for row in data_rows:
                            if len(row) <= max(idx_date, idx_amt): continue
                            payments.append({
                                'date': row[idx_date],
                                'amount': str(row[idx_amt]).replace(',', '').strip(),
                                'receiver': row[idx_rec] if len(row) > idx_rec else "-",
                                'link': row[idx_link] if len(row) > idx_link else "",
                                'source': "สลิป"
                            })
                except Exception as e:
                    print(f"Error loading slips for reconciliation: {e}")

            # 2. โหลดข้อมูลสเตตเมนต์
            if "สเตตเมนต์" in sheet_titles:
                try:
                    res_stmt = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range="'สเตตเมนต์'!A1:M").execute()
                    s_vals = res_stmt.get('values', [])
                    if s_vals:
                        s_header = s_vals[0]
                        s_data = s_vals[1:]
                        
                        s_idx_date = next((i for i, h in enumerate(s_header) if "วันที่" in h or "เอกสาร" in h), 1)
                        s_idx_out = next((i for i, h in enumerate(s_header) if "ถอน" in h or "ออก" in h), 5)
                        s_idx_cparty = next((i for i, h in enumerate(s_header) if "คู่ค้า" in h or "รายละเอียด" in h), 11)
                        s_idx_link = next((i for i, h in enumerate(s_header) if "ลิงก์" in h), 12)

                        for row in s_data:
                            if len(row) <= max(s_idx_date, s_idx_out): continue
                            amount = str(row[s_idx_out]).replace(',', '').strip()
                            if amount == '-' or not amount or amount == '0.0': continue 
                            payments.append({
                                'date': row[s_idx_date],
                                'amount': amount,
                                'receiver': row[s_idx_cparty] if len(row) > s_idx_cparty else "-",
                                'link': row[s_idx_link] if len(row) > s_idx_link else "",
                                'source': "สเตตเมนต์"
                            })
                except Exception as e:
                    print(f"Error loading statements for reconciliation: {e}")

            # 2. Read Invoices (ใบเสร็จ/ใบกำกับภาษี)
            inv_header = []
            invoices = []
            if "ใบเสร็จ/ใบกำกับภาษี" in sheet_titles:
                try:
                    res_inv = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range="'ใบเสร็จ/ใบกำกับภาษี'!A1:W").execute()
                    inv_all = res_inv.get('values', [])
                    if inv_all:
                        inv_header = inv_all[0]
                        invoices = inv_all[1:]
                except: pass

            if not payments and not invoices: 
                self.update_dashboard()
                return

            # 3. Match Logic
            matches = []
            matched_inv_indices = set()
            
            from datetime import datetime as dt
            def parse_date(d_str):
                if not d_str or d_str == '-': return None
                d_str = str(d_str).strip()
                try: 
                    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"):
                        try: 
                            parsed = dt.strptime(d_str, fmt)
                            if parsed.year > 2500: parsed = parsed.replace(year=parsed.year - 543)
                            return parsed
                        except: continue
                    return None
                except: return None
            
            for p in payments:
                try: s_amount = float(str(p['amount']).replace(',', ''))
                except: s_amount = 0
                s_receiver = str(p['receiver']).strip()
                s_date = parse_date(str(p['date']).strip())
                s_link = p['link']

                found = False
                # หาตำแหน่งคอลัมน์ใบกำกับแบบไดนามิก
                i_idx_date = next((i for i, h in enumerate(inv_header) if "วันที่" in h), 2)
                i_idx_amt = next((i for i, h in enumerate(inv_header) if "จำนวนเงิน" in h or "สุทธิ" in h), 8)
                i_idx_wht = next((i for i, h in enumerate(inv_header) if "WHT" in h), 11)
                i_idx_vend = next((i for i, h in enumerate(inv_header) if "ผู้ส่ง" in h or "ร้านค้า" in h or "คู่ค้า" in h), 4)
                i_idx_link = next((i for i, h in enumerate(inv_header) if "ลิงก์" in h), 18)

                for inv_idx, inv in enumerate(invoices):
                    if inv_idx in matched_inv_indices: continue
                    if len(inv) <= max(i_idx_date, i_idx_amt): continue
                    
                    try:
                        i_amount = float(str(inv[i_idx_amt]).replace(',', '')) if inv[i_idx_amt] != '-' else 0
                        i_wht = float(str(inv[i_idx_wht]).replace(',', '')) if len(inv) > i_idx_wht and inv[i_idx_wht] != '-' else 0
                    except: 
                        i_amount = 0
                        i_wht = 0
                    
                    i_vendor = str(inv[i_idx_vend]).strip() if len(inv) > i_idx_vend else "-"
                    i_date = parse_date(str(inv[i_idx_date]).strip())
                    i_link = str(inv[i_idx_link]).strip() if len(inv) > i_idx_link else ""

                    # SMART MATCH LOGIC
                    total_before_wht = i_amount + i_wht if i_wht > 0 else i_amount
                    
                    # Case 1: Payment matches Net Amount (Correct)
                    if abs(s_amount - i_amount) < 5.0:
                        amount_match = True
                        wht_correct = True
                    # Case 2: Payment matches Total before WHT (Forgot to deduct)
                    elif i_wht > 0 and abs(s_amount - total_before_wht) < 5.0:
                        amount_match = True
                        wht_correct = False
                    else:
                        amount_match = False
                        wht_correct = False
                    
                    # Name Matching with Fuzzy Logic
                    s_norm = normalize_thai_name(s_receiver)
                    i_norm = normalize_thai_name(i_vendor)
                    
                    similarity = get_name_similarity(s_receiver, i_vendor)
                    name_match = (similarity > 0.7) if s_receiver != '-' and i_vendor != '-' else False
                    
                    date_match = (abs((s_date - i_date).days) <= 7) if s_date and i_date else False

                    if amount_match and (name_match or date_match):
                        status = "✅ จับคู่สำเร็จ"
                        if i_wht > 0:
                            note = f"พบจาก {p['source']}: " + ("หัก WHT ถูกต้อง" if wht_correct else "⚠️ ลืมหัก WHT? (จ่ายยอดเต็ม)")
                        else:
                            note = f"พบจาก {p['source']}: จ่ายยอดเต็ม (ไม่มี WHT)"
                            
                        matches.append([dt.now().strftime("%d/%m/%Y %H:%M"), status, str(p['date']), s_amount, i_vendor, s_link, i_link, note])
                        matched_inv_indices.add(inv_idx)
                        found = True
                        break
                
                if not found:
                    s_date_display = p.get('date', '-')
                    s_rec_upper = s_receiver.upper()
                    if "ฮาร์ทวอมมิ" in s_rec_upper or "HEARTWARMING" in s_rec_upper:
                        matches.append([
                            dt.now().strftime("%d/%m/%Y %H:%M"),
                            "🔄 โอนย้ายระหว่างบัญชี",
                            s_date_display,
                            s_amount,
                            s_receiver,
                            s_link,
                            "-",
                            "โอนย้ายระหว่างบัญชีภายใน บจก. ฮาร์ทวอมมิ่ง (ไม่ต้องมีใบกำกับ)"
                        ])
                    else:
                        matches.append([
                            dt.now().strftime("%d/%m/%Y %H:%M"),
                            f"⚠️ รอใบกำกับ ({p['source']})",
                            s_date_display,
                            s_amount,
                            s_receiver,
                            s_link,
                            "-",
                            "ยังไม่พบใบกำกับภาษีที่ยอดตรงกัน"
                        ])

            for inv_idx, inv in enumerate(invoices):
                if inv_idx not in matched_inv_indices:
                    if len(inv) <= max(i_idx_date, i_idx_amt): continue
                    # ใช้ i_idx_date, i_idx_amt, i_idx_vend ที่หาได้แบบ Dynamic
                    inv_d = inv[i_idx_date] if len(inv) > i_idx_date else "-"
                    inv_a = inv[i_idx_amt] if len(inv) > i_idx_amt else "-"
                    inv_v = inv[i_idx_vend] if len(inv) > i_idx_vend else "-"
                    inv_l = inv[i_idx_link] if len(inv) > i_idx_link else "-"
                    matches.append([dt.now().strftime("%d/%m/%Y %H:%M"), "📬 รอการชำระเงิน", inv_d, inv_a, inv_v, "-", inv_l, "มีใบกำกับแล้วแต่ยังไม่พบยอดโอน"])

            # 4. Write to "สรุปกระทบยอด"
            sheet_name = "สรุปกระทบยอด"
            headers = ["วันที่ประมวลผล", "สถานะ", "วันที่เอกสาร", "ยอดเงิน", "คู่ค้า/ร้านค้า", "ลิงก์สลิป", "ลิงก์ใบกำกับ", "หมายเหตุ"]
            try:
                self.sheets_service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}).execute()
            except: pass
            
            self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1", valueInputOption="RAW", body={"values": [headers]}).execute()
            self.sheets_service.spreadsheets().values().clear(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A2:Z").execute()
            if matches:
                self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A2", valueInputOption="RAW", body={"values": matches}).execute()
            
            self.update_dashboard()
            logger.info("🎯 Reconciliation & Dashboard updated.")
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")

    def update_dashboard(self):
        """Creates or updates a high-level Dashboard sheet with formulas."""
        if not self.sheets_service or not self.spreadsheet_id: return
        sheet_name = "📊 แดชบอร์ดสรุป"
        try:
            try:
                self.sheets_service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}).execute()
            except: pass

            dashboard_data = [
                ["สรุปภาพรวมบัญชี", "", "", f"อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M')}"],
                ["", "", "", ""],
                ["💰 ยอดค่าใช้จ่ายแยกตามหมวดหมู่", "", "🧾 สรุปภาษีประจำเดือน", ""],
                ["หมวดหมู่", "ยอดรวมสุทธิ", "รายการภาษี", "ยอดรวม"],
                ["สลิปโอนเงิน", "=SUM('สลิปโอนเงิน'!I:I)", "VAT (7%) รวม", "=SUM('ใบเสร็จ/ใบกำกับภาษี'!M:M)"],
                ["สเตตเมนต์ (ถอน)", "=SUM('สเตตเมนต์'!F:F)", "WHT รวม", "=SUM('ใบเสร็จ/ใบกำกับภาษี'!N:N)"],
                ["ใบเสร็จ/ใบกำกับภาษี", "=SUM('ใบเสร็จ/ใบกำกับภาษี'!J:J)", "", ""],
                ["ยอดรวมทั้งหมด", "=B5+B6+B7", "⚠️ จ่ายเต็มแต่ลืมหัก WHT", "=COUNTIF('สรุปกระทบยอด'!H:H, \"*ระวัง*\")"],
                ["", "", "", ""],
                ["📊 สถานะการกระทบยอด (Matching)", "", "", ""],
                ["สถานะ", "จำนวนรายการ", "", ""],
                ["จับคู่สำเร็จ", "=COUNTIF('สรุปกระทบยอด'!B:B, \"*สำเร็จ*\")", "", ""],
                ["โอนย้ายระหว่างบัญชี", "=COUNTIF('สรุปกระทบยอด'!B:B, \"*โอนย้าย*\")", "", ""],
                ["รอใบกำกับ/รอชำระ", "=COUNTIF('สรุปกระทบยอด'!B:B, \"*รอ*\")", "", ""]
            ]
            self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1", valueInputOption="USER_ENTERED", body={"values": dashboard_data}).execute()
        except Exception as e:
            logger.error(f"Dashboard update error: {e}")

    def log_expense(self, data, sheet_name=None):
        """Logs data with strict Thai headers and legacy cleanup."""
        if not self.sheets_service: return
        self._validate_or_create_spreadsheet()
        if not self.spreadsheet_id: return

        import json
        try:
            ext = data.get('extracted_data', {})
            raw_category = ext.get('category', 'Others')
            
            # Helper to get values with multiple key possibilities
            def get_val(keys, default='-'):
                if isinstance(keys, str): keys = [keys]
                for k in keys:
                    v = ext.get(k)
                    if v is not None and str(v).strip() != '-': return v
                
                if any(k in keys for k in ['sender', 'from']):
                    for k in ['sender_name', 'from_name', 'vendor', 'name']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['receiver', 'to']):
                    for k in ['receiver_name', 'to_name', 'customer', 'payee']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['address', 'ที่อยู่']):
                    for k in ['sender_address', 'vendor_address', 'address_of_sender', 'address', 'receiver_address', 'full_address']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['branch', 'สาขา']):
                    for k in ['sender_branch', 'receiver_branch', 'branch_code', 'branch']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['withdrawal', 'deposit', 'balance', 'fee']):
                    for k in keys:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['sender_bank', 'bank_from']):
                    for k in ['sender_bank', 'bank_from', 'from_bank', 'bank_sender', 'sender_bank_name']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                if any(k in keys for k in ['receiver_bank', 'bank_to']):
                    for k in ['receiver_bank', 'bank_to', 'to_bank', 'bank_receiver', 'receiver_bank_name']:
                        v = ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                return default

            # Load Schema Registry
            registry = self._load_sheet_schema()
            category_map = registry.get("category_map", {})
            sheet_name = category_map.get(raw_category, raw_category).strip()

            # --- 🛡️ Duplicate Slip Detection by Ref Number ---
            ref_val = get_val(['ref', 'ref_number', 'เลขที่อ้างอิง', 'transaction_id'])
            if ref_val and str(ref_val).strip() != '-':
                cleaned_ref = str(ref_val).replace('-', '').replace(' ', '').replace("'", "").strip()
                if cleaned_ref and len(cleaned_ref) >= 6:
                    try:
                        res_val = self.sheets_service.spreadsheets().values().get(
                            spreadsheetId=self.spreadsheet_id, 
                            range=f"'{sheet_name}'!A1:Z1000"
                        ).execute()
                        existing_rows = res_val.get('values', [])
                        
                        for r_idx, row_data in enumerate(existing_rows):
                            if r_idx == 0: continue # Skip header
                            for cell_val in row_data:
                                if cell_val:
                                    cleaned_cell = str(cell_val).replace('-', '').replace(' ', '').replace("'", "").strip()
                                    if cleaned_cell == cleaned_ref:
                                        logger.warning(f"⚠️ Duplicate slip detected! Ref: {ref_val} at row {r_idx + 1}")
                                        return {
                                            "ok": False, 
                                            "error": "duplicate", 
                                            "sheet": sheet_name, 
                                            "row": r_idx + 1, 
                                            "ref_number": ref_val,
                                            "data": row_data
                                        }
                    except Exception as e:
                        logger.error(f"Failed to check duplicate: {e}")
            
            # Retrieve schema config for this sheet
            schemas = registry.get("schemas", {})
            schema_config = schemas.get(sheet_name, schemas.get("default", {}))
            
            headers = schema_config.get("headers", [])
            columns_def = schema_config.get("columns", [])
            
            def clean_val(v):
                if v is None or v == '-': return 0.0
                try: return float(str(v).replace(',', '').strip())
                except: return 0.0
                
            def clean_id(v):
                if v is None: return '-'
                s = str(v).replace('-', '').replace(' ', '').strip()
                if not s or s == '-': return '-'
                if s.isdigit() and len(s) >= 10:
                    return f"'{s}"
                return s

            # Custom Value Extractor based on source string
            def extract_field_value(col_def, context_ext=None, context_data=None):
                if context_ext is None: context_ext = ext
                if context_data is None: context_data = data
                
                src = col_def.get("source", "")
                cleaner = col_def.get("cleaner", "")
                
                # Built-in fallback helper inside extract_field_value
                def local_get_val(keys, default='-'):
                    if isinstance(keys, str): keys = [keys]
                    for k in keys:
                        v = context_ext.get(k)
                        if v is not None and str(v).strip() != '-': return v
                        
                    if any(k in keys for k in ['sender', 'from']):
                        for k in ['sender_name', 'from_name', 'vendor', 'name']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['receiver', 'to']):
                        for k in ['receiver_name', 'to_name', 'customer', 'payee']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['address', 'ที่อยู่']):
                        for k in ['sender_address', 'vendor_address', 'address_of_sender', 'address', 'receiver_address', 'full_address']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['branch', 'สาขา']):
                        for k in ['sender_branch', 'receiver_branch', 'branch_code', 'branch']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['withdrawal', 'deposit', 'balance', 'fee']):
                        for k in keys:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['sender_bank', 'bank_from']):
                        for k in ['sender_bank', 'bank_from', 'from_bank', 'bank_sender', 'sender_bank_name']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    if any(k in keys for k in ['receiver_bank', 'bank_to']):
                        for k in ['receiver_bank', 'bank_to', 'to_bank', 'bank_receiver', 'receiver_bank_name']:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                    return default

                val = "-"
                if src == "current_datetime":
                    val = datetime.now().strftime("%d/%m/%Y %H:%M")
                elif src == "current_date":
                    val = datetime.now().strftime("%d/%m/%Y")
                elif src == "current_time":
                    val = datetime.now().strftime("%H:%M")
                elif src == "ai_model":
                    val = context_data.get('ai_model', '-')
                elif src == "file_link":
                    val = context_data.get('file_link', '-')
                elif src == "summary":
                    val = context_data.get('summary', '-')
                elif src == "sheet_name":
                    val = sheet_name
                elif src.startswith("const:"):
                    val = src.replace("const:", "")
                elif src.startswith("ai_keys:"):
                    keys_list = src.replace("ai_keys:", "").split(",")
                    val = local_get_val(keys_list)
                elif src == "sender_name_fallback":
                    val = local_get_val(['sender', 'from', 'vendor', 'vendor_name', 'seller', 'company_name'])
                elif src == "receiver_name_fallback":
                    val = local_get_val(['receiver', 'to', 'payee', 'buyer', 'customer', 'customer_name'])
                
                # Special cases for ID card split
                elif src == "id_card_first_name_th":
                    full_name_th = local_get_val(['first_name_th', 'sender', 'name'])
                    f_name_th = local_get_val('first_name_th')
                    
                    if full_name_th == '-' or full_name_th == '':
                        s_name_part = context_data.get('smart_name', '')
                        if 'ID_Card_' in s_name_part:
                            try:
                                name_part = s_name_part.split('_', 3)[-1].replace('.jpg', '').replace('.png', '').replace('_', ' ')
                                if name_part:
                                    full_name_th = name_part
                            except: pass

                    if f_name_th == '-' and full_name_th != '-':
                        parts = full_name_th.split(' ', 2)
                        if len(parts) >= 2:
                            f_name_th = parts[0] if parts[0] not in ['นาย', 'นาง', 'น.ส.'] else f"{parts[0]} {parts[1]}"
                        else:
                            f_name_th = full_name_th
                    val = f_name_th
                elif src == "id_card_last_name_th":
                    full_name_th = local_get_val(['first_name_th', 'sender', 'name'])
                    l_name_th = local_get_val('last_name_th')
                    
                    if full_name_th == '-' or full_name_th == '':
                        s_name_part = context_data.get('smart_name', '')
                        if 'ID_Card_' in s_name_part:
                            try:
                                name_part = s_name_part.split('_', 3)[-1].replace('.jpg', '').replace('.png', '').replace('_', ' ')
                                if name_part:
                                    full_name_th = name_part
                            except: pass

                    if l_name_th == '-' and full_name_th != '-':
                        parts = full_name_th.split(' ', 2)
                        if len(parts) >= 2:
                            l_name_th = parts[-1]
                    val = l_name_th
                
                # Special cases for Statement Transaction looping
                elif src == "statement_date":
                    val = context_ext.get('date', local_get_val('date'))
                    # Split if combined with space
                    if ' ' in str(val):
                        val = str(val).split(' ', 1)[0]
                elif src == "statement_time":
                    val = context_ext.get('time', local_get_val('time'))
                    raw_date = context_ext.get('date', local_get_val('date'))
                    if ' ' in str(raw_date) and str(val) == '-':
                        parts = str(raw_date).split(' ', 1)
                        if len(parts) > 1:
                            val = parts[1]
                elif src == "statement_channel":
                    val = context_ext.get('channel', context_ext.get('source', local_get_val(['channel', 'source'])))

                # Apply data cleaners
                if cleaner == "float":
                    val = clean_val(val)
                elif cleaner == "id":
                    val = clean_id(val)
                    
                return val

            # Populate row(s) dynamically
            if sheet_name == "สเตตเมนต์":
                transactions = ext.get('transactions', [])
                if transactions and isinstance(transactions, list):
                    rows = []
                    for t in transactions:
                        row_vals = []
                        for col in columns_def:
                            row_vals.append(extract_field_value(col, context_ext=t))
                        rows.append(row_vals)
                else:
                    row_vals = []
                    for col in columns_def:
                        row_vals.append(extract_field_value(col))
                    rows = [row_vals]
            else:
                row_vals = []
                for col in columns_def:
                    row_vals.append(extract_field_value(col))
                rows = [row_vals]

            # Check if sheet exists and update headers if they don't match our strict format
            try:
                res = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1:Z1").execute()
                current_headers = res.get('values', [[]])[0]
                # Force update if headers are English, empty, or too short (missing columns)
                if not current_headers or len(current_headers) < (len(headers) - 2) or any(x in str(current_headers) for x in ["Log Time", "Category", "Doc Date"]):
                    logger.info(f"🔄 Updating headers for {sheet_name} to match system standards...")
                    self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1", valueInputOption="RAW", body={"values": [headers]}).execute()
            except Exception as e:
                logger.warning(f"⚠️ Header check failed: {e}")
                try:
                    self.sheets_service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}).execute()
                except: pass
                self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1", valueInputOption="RAW", body={"values": [headers]}).execute()

            # Append the data
            try:
                logger.info(f"📝 Appending row to {sheet_name} (Length: {len(rows[0])}): {rows[0][:10]}...")
                result = self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id, 
                    range=f"'{sheet_name}'!A2", 
                    valueInputOption="USER_ENTERED", 
                    body={"values": rows}
                ).execute()
                
                # Extract row index from updatedRange (e.g., "'Sheet1'!A5:S5")
                updated_range = result.get('updates', {}).get('updatedRange', '')
                row_idx = 1
                if '!' in updated_range:
                    range_part = updated_range.split('!')[1]
                    # Extract the first number found in the range string
                    match = re.search(r'\d+', range_part)
                    if match:
                        row_idx = int(match.group())
                
                # --- Trigger Reconciliation ---
                self.auto_reconcile_internal()
                
                return {"ok": True, "sheet": sheet_name, "row": row_idx, "data": rows[0]}

            except Exception as e:
                logger.error(f"❌ Error logging to sheet: {e}")
                return {"ok": False, "error": str(e)}

            # --- Automatic Cleanup: Delete "Sheet1" or "ชีต1" if it's empty and not the only sheet ---
            try:
                spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                sheets = spreadsheet.get('sheets', [])
                if len(sheets) > 1:
                    for s in sheets:
                        title = s['properties']['title']
                        if title in ["Sheet1", "ชีต1"]:
                            # Check if it's empty (optional but safer)
                            s_id = s['properties']['sheetId']
                            self.sheets_service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'requests': [{'deleteSheet': {'sheetId': s_id}}]}).execute()
                            logger.info(f"🗑 Deleted default sheet: {title}")
                            break
            except: pass
        except Exception as e:
            logger.error(f"Logging error: {e}")
            return {"ok": False, "error": str(e)}

    def update_expense(self, sheet_name, row_index, column_name, new_value):
        """Updates a specific cell in the spreadsheet based on header name."""
        if not self.sheets_service or not self.spreadsheet_id: return False, "Service not initialized"
        try:
            # 1. Get headers to find column index
            res = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1:Z1"
            ).execute()
            headers = res.get('values', [[]])[0]
            
            try:
                col_idx = -1
                for i, h in enumerate(headers):
                    if column_name.lower() in h.lower():
                        col_idx = i
                        break
                
                if col_idx == -1:
                    return False, f"Column '{column_name}' not found"
                
                # Convert 0-indexed col to Excel column (A, B, C...)
                col_letter = chr(65 + col_idx) if col_idx < 26 else f"A{chr(65 + (col_idx - 26))}"
                cell_range = f"'{sheet_name}'!{col_letter}{row_index}"
                
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=cell_range,
                    valueInputOption="USER_ENTERED",
                    body={"values": [[new_value]]}
                ).execute()
                
                # Re-run reconciliation after update
                self.auto_reconcile_internal()
                return True, None
            except ValueError:
                return False, f"Header matching failed"
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False, str(e)

    def move_row_between_sheets(self, from_sheet, row_index, to_sheet):
        """Moves a specific row from one sheet to another, adjusting headers appropriately and deleting from source."""
        if not self.sheets_service or not self.spreadsheet_id:
            return False, "Google Sheets service not initialized"
            
        try:
            # 1. Get source row values
            source_res = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=f"'{from_sheet}'!A{row_index}:Z{row_index}"
            ).execute()
            source_vals = source_res.get('values', [])
            if not source_vals:
                return False, f"Row {row_index} in sheet '{from_sheet}' is empty or not found"
            row_data = source_vals[0]
            
            # Get source headers
            source_headers_res = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=f"'{from_sheet}'!A1:Z1"
            ).execute()
            source_headers = source_headers_res.get('values', [[]])[0]
            
            # Map source data into a dictionary {header: value}
            row_dict = {}
            for i, val in enumerate(row_data):
                if i < len(source_headers):
                    row_dict[source_headers[i]] = val
            
            # 2. Get target headers to align the values correctly
            target_headers_res = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id, range=f"'{to_sheet}'!A1:Z1"
            ).execute()
            target_headers = target_headers_res.get('values', [[]])[0]
            
            # If target sheet has no headers, just append the raw row
            if not target_headers:
                target_headers = source_headers
                # Write headers to target sheet first
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"'{to_sheet}'!A1",
                    valueInputOption="USER_ENTERED",
                    body={"values": [target_headers]}
                ).execute()
            
            # Align values with target headers
            new_row_values = []
            for h in target_headers:
                matching_val = ""
                for k, v in row_dict.items():
                    if k.strip().lower() == h.strip().lower():
                        matching_val = v
                        break
                new_row_values.append(matching_val)
                
            # If the category (หมวดหมู่) column exists in target, set it to the target sheet name or keep existing
            cat_idx = next((i for i, h in enumerate(target_headers) if "หมวดหมู่" in h), -1)
            if cat_idx != -1:
                new_row_values[cat_idx] = to_sheet
                
            # Append new row to target sheet
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{to_sheet}'!A1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body={"values": [new_row_values]}
            ).execute()
            
            # Get target sheetId and from_sheet sheetId for row deletion
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            from_sheet_id = None
            for s in spreadsheet.get('sheets', []):
                if s['properties']['title'] == from_sheet:
                    from_sheet_id = s['properties']['sheetId']
                    break
                    
            if from_sheet_id is not None:
                # Delete row from source sheet using batchUpdate
                delete_req = {
                    "requests": [
                        {
                            "deleteDimension": {
                                "range": {
                                    "sheetId": from_sheet_id,
                                    "dimension": "ROWS",
                                    "startIndex": row_index - 1,
                                    "endIndex": row_index
                                }
                            }
                        }
                    ]
                }
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id, body=delete_req
                ).execute()
                
            # Re-run reconciliation
            self.auto_reconcile_internal()
            return True, None
            
        except Exception as e:
            logger.error(f"Error moving row from {from_sheet} to {to_sheet}: {e}")
            return False, str(e)

    def get_monthly_summary(self):
        """Fetches real spreadsheet data and generates a stunning monthly expense summary Flex Message."""
        if not self.sheets_service or not self.spreadsheet_id:
            return "❌ ระบบ Google Sheets ยังไม่ได้เชื่อมต่อหรือยังไม่ได้ลงทะเบียนค่ะ"
            
        try:
            # Get list of sheets
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
            
            total_expense = 0.0
            total_count = 0
            categories_breakdown = {}
            
            # We will parse สลิปโอนเงิน
            if "สลิปโอนเงิน" in sheet_titles:
                res_slip = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id, range="'สลิปโอนเงิน'!A1:Z"
                ).execute()
                vals = res_slip.get('values', [])
                if vals and len(vals) > 1:
                    header_row = vals[0]
                    data_rows = vals[1:]
                    
                    # Dynamic column mapping
                    idx_amt = next((i for i, h in enumerate(header_row) if "จำนวนเงินสุทธิ" in h or "สุทธิ" in h), 8)
                    idx_cat = next((i for i, h in enumerate(header_row) if "หมวดหมู่" in h), 1)
                    
                    for row in data_rows:
                        if len(row) <= max(idx_amt, idx_cat): continue
                        try:
                            amt_str = str(row[idx_amt]).replace(',', '').strip()
                            if amt_str and amt_str != '-':
                                amt = float(amt_str)
                                total_expense += amt
                                total_count += 1
                                
                                cat = str(row[idx_cat]).strip() or "ทั่วไป"
                                categories_breakdown[cat] = categories_breakdown.get(cat, 0.0) + amt
                        except:
                            pass
            
            # We will also parse ใบเสร็จ/ใบกำกับภาษี if it exists
            if "ใบเสร็จ/ใบกำกับภาษี" in sheet_titles:
                res_tax = self.sheets_service.spreadsheets().values().get(
                    spreadsheetId=self.spreadsheet_id, range="'ใบเสร็จ/ใบกำกับภาษี'!A1:Z"
                ).execute()
                vals = res_tax.get('values', [])
                if vals and len(vals) > 1:
                    header_row = vals[0]
                    data_rows = vals[1:]
                    
                    idx_amt = next((i for i, h in enumerate(header_row) if "จำนวนเงินสุทธิ" in h or "สุทธิ" in h), 8)
                    idx_cat = next((i for i, h in enumerate(header_row) if "หมวดหมู่" in h), 1)
                    
                    for row in data_rows:
                        if len(row) <= max(idx_amt, idx_cat): continue
                        try:
                            amt_str = str(row[idx_amt]).replace(',', '').strip()
                            if amt_str and amt_str != '-':
                                amt = float(amt_str)
                                total_expense += amt
                                total_count += 1
                                
                                cat = str(row[idx_cat]).strip() or "ใบเสร็จรับเงิน"
                                categories_breakdown[cat] = categories_breakdown.get(cat, 0.0) + amt
                        except:
                            pass

            # If no data found at all
            if total_count == 0:
                return "📊 ไม่พบข้อมูลรายการใช้จ่ายที่บันทึกไว้ใน Google Sheets ในขณะนี้ค่ะ ลองบันทึกข้อมูลก่อนนะคะ 😊"

            # Format amounts cleanly
            total_expense_str = f"{total_expense:,.2f}"
            if total_expense_str.endswith(".00"):
                total_expense_str = total_expense_str[:-3]
                
            avg_expense = total_expense / total_count
            avg_expense_str = f"{avg_expense:,.2f}"
            if avg_expense_str.endswith(".00"):
                avg_expense_str = avg_expense_str[:-3]

            # Construct beautiful custom Flex Message
            contents_list = []
            
            # Categories breakdown list
            for cat, amt in categories_breakdown.items():
                amt_formatted = f"{amt:,.2f}"
                if amt_formatted.endswith(".00"):
                    amt_formatted = amt_formatted[:-3]
                
                contents_list.append({
                    "type": "box",
                    "layout": "horizontal",
                    "margin": "md",
                    "contents": [
                        {
                            "type": "text",
                            "text": f"📁 {cat}",
                            "size": "sm",
                            "color": "#333333",
                            "flex": 5
                        },
                        {
                            "type": "text",
                            "text": f"{amt_formatted} THB",
                            "size": "sm",
                            "weight": "bold",
                            "color": "#111111",
                            "align": "end",
                            "flex": 5
                        }
                    ]
                })

            sheet_url = f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"
            
            flex_bubble = {
                "type": "bubble",
                "size": "mega",
                "header": {
                    "type": "box",
                    "layout": "vertical",
                    "backgroundColor": "#17A2B8",
                    "paddingAll": "16px",
                    "contents": [
                        {
                            "type": "text",
                            "text": "📊 รายงานสรุปรายจ่ายทั้งหมด",
                            "weight": "bold",
                            "color": "#FFFFFF",
                            "size": "md"
                        }
                    ]
                },
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "20px",
                    "spacing": "md",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "ยอดรวมรายจ่าย",
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 4,
                                    "align": "start"
                                },
                                {
                                    "type": "text",
                                    "text": f"{total_expense_str} THB",
                                    "weight": "bold",
                                    "size": "xl",
                                    "color": "#17A2B8",
                                    "flex": 6,
                                    "align": "end"
                                }
                            ]
                        },
                        {
                            "type": "separator",
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "📂 แยกตามประเภทบัญชี/หมวดหมู่",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#17A2B8"
                                }
                            ] + contents_list
                        },
                        {
                            "type": "separator",
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "margin": "lg",
                            "spacing": "xs",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "จำนวนรายการทั้งหมด", "color": "#888888", "size": "xs", "flex": 6},
                                        {"type": "text", "text": f"{total_count} รายการ", "color": "#333333", "weight": "bold", "size": "xs", "flex": 4, "align": "end"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "ยอดเฉลี่ยต่อรายการ", "color": "#888888", "size": "xs", "flex": 6},
                                        {"type": "text", "text": f"{avg_expense_str} THB", "color": "#333333", "weight": "bold", "size": "xs", "flex": 4, "align": "end"}
                                    ]
                                }
                            ]
                        }
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "vertical",
                    "paddingAll": "10px",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#17A2B8",
                            "action": {
                                "type": "uri",
                                "label": "📊 เปิดดูรายละเอียดใน Google Sheets",
                                "uri": sheet_url
                            }
                        }
                    ]
                }
            }
            
            return {
                "type": "flex",
                "altText": "📊 รายงานสรุปยอดรายจ่ายของพี่ค่ะ",
                "contents": flex_bubble
            }
            
        except Exception as e:
            logger.error(f"Error compiling monthly summary: {e}")
            return f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลรายจ่าย: {e}"

google_manager = GoogleWorkspaceManager()

def rename_file(file_id, new_name): return google_manager.rename_file(file_id, new_name)
def delete_file(file_id): return google_manager.delete_file(file_id)
def list_folder_contents(folder_id=None): return google_manager.list_subfolders(folder_id)
def move_row_between_sheets(from_sheet, row_index, to_sheet): return google_manager.move_row_between_sheets(from_sheet, row_index, to_sheet)
