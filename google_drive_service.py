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
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2 import service_account
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

def normalize_thai_name(name):
    """Cleans up Thai business names for better matching."""
    if not name or name == '-': return ""
    name = str(name).replace('บจก.', '').replace('บริษัท', '').replace('จำกัด', '').replace('(มหาชน)', '')
    name = name.replace('CO.,LTD.', '').replace('CO., LTD.', '').replace('LTD.', '').replace('CORP.', '')
    name = name.replace(' ', '').replace('.', '').replace(',', '').strip()
    return name.upper()

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
                if os.path.exists(self.credentials_path):
                    creds = service_account.Credentials.from_service_account_file(
                        self.credentials_path, scopes=self.scopes
                    )
                    logger.info("Using service-account.json for Drive services.")
                else:
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
                    logger.warning(f"⚠️ Spreadsheet {self.spreadsheet_id} is in TRASH.")
            except Exception as e:
                logger.warning(f"⚠️ Spreadsheet ID {self.spreadsheet_id} is invalid: {e}")
        
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
                    
                    name_match = (normalize_thai_name(s_receiver) in normalize_thai_name(i_vendor) or \
                                  normalize_thai_name(i_vendor) in normalize_thai_name(s_receiver)) \
                                  if s_receiver != '-' and i_vendor != '-' else False
                    
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
                    matches.append([dt.now().strftime("%d/%m/%Y %H:%M"), f"⚠️ รอใบกำกับ ({p['source']})", s_date_display, s_amount, s_receiver, s_link, "-", "ยังไม่พบใบกำกับภาษีที่ยอดตรงกัน"])

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

            # Logic to extract sender/receiver with broader fallbacks
            s_name = get_val(['sender', 'from', 'vendor', 'vendor_name', 'seller', 'company_name'])
            r_name = get_val(['receiver', 'to', 'payee', 'buyer', 'customer', 'customer_name'])

            category_map = {
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
            }
            sheet_name = category_map.get(raw_category, raw_category).strip()
            
            def clean_val(v):
                if v is None or v == '-': return 0.0
                try: return float(str(v).replace(',', '').strip())
                except: return 0.0
            def clean_id(v):
                if v is None: return '-'
                s = str(v).replace('-', '').replace(' ', '').strip()
                if not s or s == '-': return '-'
                # Prefix ANY long numeric string with ' to avoid scientific notation
                if s.isdigit() and len(s) >= 10:
                    return f"'{s}"
                return s

            if sheet_name == "บัตรประชาชน":
                headers = ["เวลาที่บันทึก", "หมวดหมู่", "วันที่บันทึก", "เวลาที่บันทึก", "AI Model", "เลขบัตรประชาชน", "ชื่อ (ไทย)", "นามสกุล (ไทย)", "ชื่อ (อังกฤษ)", "นามสกุล (อังกฤษ)", "วันเกิด", "เพศ", "ที่อยู่", "วันหมดอายุ", "Laser ID", "ลิงก์ไฟล์", "AI ถูก/ผิด"]
                
                # Robust name extraction for ID Card
                full_name_th = get_val(['first_name_th', 'sender', 'name'])
                f_name_th = get_val('first_name_th')
                l_name_th = get_val('last_name_th')
                
                # Ultimate fallback: If name is still missing, try to get it from smart_name
                if full_name_th == '-' or full_name_th == '':
                    s_name_part = data.get('smart_name', '')
                    if 'ID_Card_' in s_name_part:
                        # Extract name from "ID_Card_YYYY-MM-DD_Name_Surname.jpg"
                        try:
                            name_part = s_name_part.split('_', 3)[-1].replace('.jpg', '').replace('.png', '').replace('_', ' ')
                            if name_part:
                                full_name_th = name_part
                        except: pass

                if f_name_th == '-' and full_name_th != '-':
                    # Split if we only got a full name
                    parts = full_name_th.split(' ', 2)
                    if len(parts) >= 2:
                        f_name_th = parts[0] if parts[0] not in ['นาย', 'นาง', 'น.ส.'] else f"{parts[0]} {parts[1]}"
                        l_name_th = parts[-1]
                    else:
                        f_name_th = full_name_th

                rows = [[
                    datetime.now().strftime("%d/%m/%Y %H:%M"), 
                    "ID_Card", 
                    datetime.now().strftime("%d/%m/%Y"), 
                    datetime.now().strftime("%H:%M"), 
                    data.get('ai_model', '-'), 
                    clean_id(get_val(['id_number', 'tax_id'])), 
                    f_name_th, 
                    l_name_th, 
                    get_val(['first_name_en', 'name_en']), 
                    get_val(['last_name_en', 'surname_en']), 
                    get_val(['birth_date', 'birthday', 'dob']), 
                    get_val(['gender', 'sex']), 
                    get_val('address'), 
                    get_val(['expiry_date', 'expired_date', 'expiry']), 
                    get_val(['laser_id', 'laser', 'ref_number']), # AI sometimes puts laser in ref_number
                    data.get('file_link', '-'), 
                    "-"
                ]]
            elif sheet_name == "สเตตเมนต์":
                headers = ["เวลาที่บันทึก", "วันที่เอกสาร", "เวลา/วันที่มีผล", "รายการ", "รายละเอียด", "ถอน/เงินออก", "ฝาก/เงินเข้า", "ค่าธรรมเนียม", "ยอดคงเหลือ", "ช่องทาง", "เลขที่อ้างอิง", "คู่ค้า/ผู้โอน", "ลิงก์ไฟล์"]
                
                # Check if AI returned multiple transactions
                transactions = ext.get('transactions', [])
                if transactions and isinstance(transactions, list):
                    rows = []
                    for t in transactions:
                        # Internal helper for transaction fields
                        def get_t_val(keys, default='-'):
                            if isinstance(keys, str): keys = [keys]
                            for k in keys:
                                v = t.get(k)
                                if v is not None and str(v).strip() != '-': return v
                            return default
                        
                        # Smart Date/Time split if combined
                        raw_date = get_t_val('date', get_val('date'))
                        raw_time = get_t_val('time', get_val('time'))
                        if ' ' in raw_date and raw_time == '-':
                            parts = raw_date.split(' ', 1)
                            raw_date = parts[0]
                            raw_time = parts[1]
                        
                        rows.append([
                            datetime.now().strftime("%d/%m/%Y %H:%M"),
                            raw_date,
                            raw_time,
                            get_t_val(['memo', 'description', 'รายการ']),
                            get_t_val(['details', 'info', 'รายละเอียด']),
                            clean_val(get_t_val(['withdrawal', 'ถอน', 'out'])),
                            clean_val(get_t_val(['deposit', 'ฝาก', 'in'])),
                            clean_val(get_t_val(['fee', 'ค่าธรรมเนียม'])),
                            clean_val(get_t_val(['balance', 'ยอดคงเหลือ'])),
                            get_t_val(['channel', 'source', 'ช่องทาง'], get_val(['channel', 'source'])),
                            clean_id(get_t_val(['ref', 'ref_number', 'เลขที่อ้างอิง'])),
                            get_t_val(['counterparty', 'sender', 'receiver', 'คู่ค้า']),
                            data.get('file_link', '-')
                        ])
                else:
                    # Fallback to single row if no transaction list found
                    rows = [[
                        datetime.now().strftime("%d/%m/%Y %H:%M"),
                        get_val('date'),
                        get_val('time'),
                        get_val(['memo', 'description']),
                        get_val(['details', 'info']),
                        clean_val(get_val('withdrawal', 0)),
                        clean_val(get_val('deposit', 0)),
                        clean_val(get_val('fee', 0)),
                        clean_val(get_val('balance', 0)),
                        get_val(['channel', 'source']),
                        get_val('ref_number'),
                        s_name if s_name != '-' else get_val('receiver'),
                        data.get('file_link', '-')
                    ]]
            elif sheet_name == "ใบเสร็จ/ใบกำกับภาษี":
                headers = ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "ผู้ส่ง/ร้านค้า", "รหัสสาขา", "เลขผู้เสียภาษี", "ที่อยู่คู่ค้า", "ผู้รับ", "ช่องทางการติดต่อ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "ส่วนลด", "VAT", "WHT", "ประเภท WHT", "เลขที่อ้างอิง", "สรุปจาก AI", "ลิงก์ไฟล์", "AI ถูก/ผิด"]
                wht_val = clean_val(get_val('wht_amount'))
                rows = [[
                    datetime.now().strftime("%d/%m/%Y %H:%M"), 
                    "ใบเสร็จ/ใบกำกับภาษี", 
                    get_val('date'), 
                    s_name, 
                    get_val('branch'), 
                    clean_id(get_val('tax_id')), 
                    get_val('address'), 
                    r_name, 
                    get_val(['contact', 'phone', 'email']), 
                    clean_val(get_val('net_amount')), 
                    clean_val(get_val('gross_amount')), 
                    clean_val(get_val('discount_amount')), 
                    clean_val(get_val('vat_amount')), 
                    wht_val, 
                    get_val(['wht_type', 'wht_category', 'wht_rate', 'wht_percent']), 
                    get_val('ref_number'), 
                    data.get('summary', '-'), 
                    data.get('file_link', '-'), 
                    "-"
                ]]
            elif sheet_name == "สลิปโอนเงิน":
                headers = ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "เวลาในเอกสาร", "ผู้ส่ง/ร้านค้า", "เลขผู้เสียภาษี", "ผู้รับ", "ช่องทางการติดต่อ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "WHT", "เลขที่อ้างอิง", "ธนาคารต้นทาง", "ธนาคารปลายทาง", "บันทึกช่วยจำ", "สรุปจาก AI", "ลิงก์ไฟล์", "AI ถูก/ผิด"]
                wht_val = clean_val(get_val('wht_amount'))
                rows = [[
                    datetime.now().strftime("%d/%m/%Y %H:%M"), 
                    "สลิปโอนเงิน", 
                    get_val('date'), 
                    get_val('time'), 
                    s_name, 
                    clean_id(get_val('tax_id')), 
                    r_name, 
                    get_val(['contact', 'phone']), 
                    clean_val(get_val('net_amount')), 
                    clean_val(get_val('gross_amount')), 
                    wht_val, 
                    get_val('ref_number'), 
                    get_val(['sender_bank', 'bank_from']), 
                    get_val(['receiver_bank', 'bank_to']), 
                    get_val('memo'), 
                    data.get('summary', '-'), 
                    data.get('file_link', '-'), 
                    "-"
                ]]
            elif sheet_name == "ใบเสนอราคา":
                headers = ["เวลาที่บันทึก", "วันที่เอกสาร", "ผู้เสนอราคา", "ลูกค้า", "ยอดเงินสุทธิ", "สถานะ", "ลิงก์ไฟล์", "AI ถูก/ผิด"]
                rows = [[
                    datetime.now().strftime("%d/%m/%Y %H:%M"),
                    get_val('date'),
                    s_name,
                    r_name,
                    clean_val(get_val('net_amount')),
                    "รออนุมัติ",
                    data.get('file_link', '-'),
                    "-"
                ]]
            else:
                headers = ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "สรุปข้อมูล", "ลิงก์ไฟล์", "AI ถูก/ผิด"]
                rows = [[datetime.now().strftime("%d/%m/%Y %H:%M"), sheet_name, get_val('date'), data.get('summary', '-'), data.get('file_link', '-'), "-"]]

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
                self.sheets_service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A2", valueInputOption="USER_ENTERED", body={"values": rows}).execute()
            except Exception as e:
                logger.error(f"❌ Error logging to sheet: {e}")
                return False

            # --- Trigger Reconciliation ---
            self.auto_reconcile_internal()

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

    def get_monthly_summary(self):
        return "ฟังก์ชันสรุปกำลังปรับปรุงให้รองรับหลาย Sheet ครับ"

google_manager = GoogleWorkspaceManager()

def rename_file(file_id, new_name): return google_manager.rename_file(file_id, new_name)
def delete_file(file_id): return google_manager.delete_file(file_id)
def list_folder_contents(folder_id=None): return google_manager.list_subfolders(folder_id)
