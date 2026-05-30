"""
Google Drive & Sheets Service Manager
-------------------------------------
Handles all interactions with Google Workspace APIs including file uploads, 
logging to spreadsheets, and automated reconciliation.
"""

import os
import contextlib
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

def parse_to_yyyymmdd(date_str):
    """Parses date string into YYYYMMDD format, handling Thai Buddhist Era and various formats."""
    if not date_str or str(date_str).strip() in ['-', '']:
        return datetime.now().strftime("%Y%m%d")
    
    s = str(date_str).strip()
    # Try common formats using datetime first
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            from datetime import datetime as dt
            parsed = dt.strptime(s, fmt)
            year = parsed.year
            if year > 2500:
                year -= 543
            return f"{year:04d}{parsed.month:02d}{parsed.day:02d}"
        except Exception:
            continue
            
    # Regular expression fallback if not perfectly matching simple formats
    digits = re.findall(r'\d+', s)
    if len(digits) >= 3:
        try:
            d1, d2, d3 = digits[0], digits[1], digits[2]
            if len(d1) == 4:
                year, month, day = int(d1), int(d2), int(d3)
            elif len(d3) == 4:
                year, month, day = int(d3), int(d2), int(d1)
            else:
                day, month, year = int(d1), int(d2), int(d3)
                if year < 100:
                    # Logic: If year is >= 60, assume it's BE short year (e.g., 67 -> 2567)
                    # If year is < 60, assume it's AD short year (e.g., 24 -> 2024)
                    if year >= 60:
                        year += 2500
                    else:
                        year += 2000
            if year > 2400:
                year -= 543
            
            if month < 1 or month > 12: month = 1
            if day < 1 or day > 31: day = 1
            return f"{year:04d}{month:02d}{day:02d}"
        except Exception:
            pass
    
    return datetime.now().strftime("%Y%m%d")

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

def thread_safe(func):
    """Decorator to serialize access to the Google Workspace APIs using an instance-level RLock."""
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, '_instance_lock'):
            with GoogleWorkspaceManager._lock:
                if not hasattr(self, '_instance_lock'):
                    self._instance_lock = threading.RLock()
        with self._instance_lock:
            return func(self, *args, **kwargs)
    return wrapper

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

        self._local = threading.local()
        self._local.creds = None
        self._cached_creds = None
        self._creds_lock = threading.Lock()

        self.credentials_path = 'service-account.json'
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        self._parent_folder_id = os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")
        self._spreadsheet_id = os.getenv("SPREADSHEET_ID")
        # Network calls (token refresh, API build, spreadsheet validation) are lazy —
        # triggered on first use via drive_service/sheets_service properties.
        self._initialized = True

    def set_context(self, username=None, org_id=None):
        """Dynamically set the user/org context for the current thread to route operations to their specific Drive/Sheets."""
        self._local.username = username
        self._local.org_id = org_id
        # Reset cached services in the current thread to force re-initialization
        self._local.drive_service = None
        self._local.sheets_service = None
        self._local.creds = None
        self._local.spreadsheet_id_override = None  # clear any post-creation override
        with self._creds_lock:
            self._cached_creds = None
        logger.info(f"🎯 Switched thread context to user={username}, org={org_id}")

    def clear_context(self):
        """Resets all thread-local storage attributes at the end of a request or thread execution to prevent thread reuse pollution."""
        if hasattr(self, '_local'):
            self._local.username = None
            self._local.org_id = None
            self._local.drive_service = None
            self._local.sheets_service = None
            self._local.creds = None
            self._local.spreadsheet_id_override = None  # clear any post-creation override
            logger.info("🧹 Cleared thread local Google Workspace context")

    @contextlib.contextmanager
    def secure_context(self, username=None, org_id=None):
        """
        Context manager to set user/org credentials context dynamically
        and guarantee context cleanup on exit or error.
        """
        old_username = getattr(self._local, 'username', None)
        old_org_id = getattr(self._local, 'org_id', None)
        try:
            self.set_context(username, org_id)
            yield self
        finally:
            if old_username or old_org_id:
                self.set_context(old_username, old_org_id)
            else:
                self.clear_context()

    @property
    def spreadsheet_id(self):
        # Thread-local override: set immediately after auto-recreation to avoid 404 loops
        # within the same request before DB write propagates to the correct table
        override = getattr(self._local, 'spreadsheet_id_override', None)
        if override:
            return override

        username = getattr(self._local, 'username', None)
        org_id = getattr(self._local, 'org_id', None)

        if not username and not org_id:
            try:
                from flask import session, has_request_context
                if has_request_context():
                    username = session.get("user")
                    org_id = session.get("org_id", 1)
            except Exception:
                pass

        if username or org_id:
            try:
                import database
                token_data, source = database.resolve_google_token(username, org_id)
                if token_data and token_data.get("spreadsheet_id"):
                    return token_data.get("spreadsheet_id")
            except Exception as e:
                logger.error(f"Error resolving spreadsheet_id from database: {e}")

        return getattr(self, '_spreadsheet_id', None) or os.getenv("SPREADSHEET_ID")

    @spreadsheet_id.setter
    def spreadsheet_id(self, value):
        self._spreadsheet_id = value

    @property
    def parent_folder_id(self):
        username = getattr(self._local, 'username', None)
        org_id = getattr(self._local, 'org_id', None)
        
        if not username and not org_id:
            try:
                from flask import session, has_request_context
                if has_request_context():
                    username = session.get("user")
                    org_id = session.get("org_id", 1)
            except Exception:
                pass
                
        if username or org_id:
            try:
                import database
                token_data, source = database.resolve_google_token(username, org_id)
                if token_data and token_data.get("drive_folder_id"):
                    return token_data.get("drive_folder_id")
            except Exception as e:
                logger.error(f"Error resolving parent_folder_id from database: {e}")
                
        return getattr(self, '_parent_folder_id', None) or os.getenv("GOOGLE_DRIVE_PARENT_ID") or os.getenv("PARENT_FOLDER_ID")

    @parent_folder_id.setter
    def parent_folder_id(self, value):
        self._parent_folder_id = value

    @classmethod
    def invalidate_user_cache(cls, username):
        """Clears the credentials cache to force re-initialization of thread services."""
        mgr = cls()
        if hasattr(mgr, '_creds_lock'):
            with mgr._creds_lock:
                mgr._cached_creds = None
        if hasattr(mgr, '_local'):
            mgr._local.drive_service = None
            mgr._local.sheets_service = None
            mgr._local.creds = None
        logger.info(f"🔄 Invalidated Google Workspace credentials cache for user {username}")

    @property
    def drive_service(self):
        if not hasattr(self._local, 'drive_service') or self._local.drive_service is None:
            self._initialize_thread_services()
        return self._local.drive_service

    @drive_service.setter
    def drive_service(self, value):
        self._local.drive_service = value

    @property
    def sheets_service(self):
        if not hasattr(self._local, 'sheets_service') or self._local.sheets_service is None:
            self._initialize_thread_services()
        return self._local.sheets_service

    @sheets_service.setter
    def sheets_service(self, value):
        self._local.sheets_service = value

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
                "Uploads": "สลิปโอนเงิน",
                "WHT": "ใบหัก ณ ที่จ่าย",
                "wht": "ใบหัก ณ ที่จ่าย",
                "Withholding_Tax": "ใบหัก ณ ที่จ่าย",
                "ใบหักณที่จ่าย": "ใบหัก ณ ที่จ่าย",
                "หนังสือรับรองการหักภาษี ณ ที่จ่าย": "ใบหัก ณ ที่จ่าย",
                "peak": "peak",
                "Import_Expenses": "peak",
                "General_Expense": "บันทึกค่าใช้จ่าย",
                "Expense": "บันทึกค่าใช้จ่าย"
            },
            "schemas": {
                "บันทึกค่าใช้จ่าย": {
                    "headers": [
                        "เวลาที่บันทึก", "หมวดหมู่", "วันที่", "ประเภทค่าใช้จ่าย", "จำนวนเงิน", "ผู้รับเงิน", "รายละเอียด/บันทึกช่วยจำ", "สรุปจาก AI", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์อ้างอิง", "ลิงก์ไฟล์", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:บันทึกค่าใช้จ่าย"},
                        {"source": "ai_keys:date"},
                        {"source": "ai_keys:income_type"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:receiver"},
                        {"source": "ai_keys:memo"},
                        {"source": "summary"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "line_sender_name"}
                    ]
                },
                "บัตรประชาชน": {
                    "headers": [
                        "เวลาที่บันทึก", "หมวดหมู่", "วันที่บันทึก", "เวลาที่บันทึก", "AI Model", 
                        "เลขบัตรประชาชน", "ชื่อ (ไทย)", "นามสกุล (ไทย)", "ชื่อ (อังกฤษ)", "นามสกุล (อังกฤษ)", 
                        "วันเกิด", "เพศ", "ที่อยู่", "วันหมดอายุ", "Laser ID", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:ID_Card"},
                        {"source": "current_date"},
                        {"source": "current_time"},
                        {"source": "ai_model"},
                        {"source": "ai_keys:id_number,tax_id", "cleaner": "id"},
                        {"source": "id_card_first_name_th"},
                        {"source": "id_card_last_name_th"},
                        {"source": "id_card_first_name_en"},
                        {"source": "id_card_last_name_en"},
                        {"source": "ai_keys:birth_date,birthday,dob"},
                        {"source": "ai_keys:gender,sex"},
                        {"source": "ai_keys:address"},
                        {"source": "ai_keys:expiry_date,expired_date,expiry"},
                        {"source": "ai_keys:laser_id,laser,ref_number"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
                    ]
                },
                "สเตตเมนต์": {
                    "headers": [
                        "เวลาที่บันทึก", "วันที่เอกสาร", "เวลา/วันที่มีผล", "รายการ", "รายละเอียด", 
                        "ถอน/เงินออก", "ฝาก/เงินเข้า", "ค่าธรรมเนียม", "ยอดคงเหลือ", "ช่องทาง", 
                        "เลขที่อ้างอิง", "คู่ค้า/ผู้โอน", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "ผู้ส่ง (LINE User)"
                    ],
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
                        {"source": "ai_keys:ref,ref_number,เลขที่อ้างอิง", "cleaner": "literal"},
                        {"source": "ai_keys:counterparty,sender,receiver,คู่ค้า"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "line_sender_name"}
                    ]
                },
                "ใบเสร็จ/ใบกำกับภาษี": {
                    "headers": [
                        "เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "ผู้ส่ง/ร้านค้า", "รหัสสาขา", 
                        "เลขผู้เสียภาษี", "ที่อยู่คู่ค้า", "ผู้รับ", "ช่องทางการติดต่อ", "จำนวนเงินสุทธิ", 
                        "ยอดก่อนภาษี", "ส่วนลด", "VAT", "หัก ณ ที่จ่าย", "ประเภท หัก ณ ที่จ่าย", "เลขที่อ้างอิง", 
                        "ตามใบกำกับ", "สรุปจาก AI", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:ใบเสร็จ/ใบกำกับภาษี"},
                        {"source": "ai_keys:date"},
                        {"source": "sender_name_fallback"},
                        {"source": "ai_keys:branch", "cleaner": "branch"},
                        {"source": "ai_keys:tax_id", "cleaner": "id"},
                        {"source": "ai_keys:address"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:contact,phone,email", "cleaner": "literal"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:gross_amount", "cleaner": "float"},
                        {"source": "ai_keys:discount_amount", "cleaner": "float"},
                        {"source": "ai_keys:vat_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_amount", "cleaner": "float"},
                        {"source": "wht_type_smart"},
                        {"source": "ai_keys:ref_number", "cleaner": "literal"},
                        {"source": "invoice_follow_up"},
                        {"source": "summary"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
                    ]
                },
                "สลิปโอนเงิน": {
                    "headers": [
                        "เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "เวลาในเอกสาร", "ผู้ส่ง/ร้านค้า", 
                        "ผู้รับ", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "หัก ณ ที่จ่าย", "เลขที่อ้างอิง", 
                        "ธนาคารต้นทาง", "ธนาคารปลายทาง", "บันทึกช่วยจำ", "สรุปจาก AI", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:สลิปโอนเงิน"},
                        {"source": "ai_keys:date"},
                        {"source": "ai_keys:time"},
                        {"source": "sender_name_fallback"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:gross_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_amount", "cleaner": "float"},
                        {"source": "ai_keys:ref_number", "cleaner": "literal"},
                        {"source": "ai_keys:sender_bank,bank_from"},
                        {"source": "ai_keys:receiver_bank,bank_to"},
                        {"source": "ai_keys:memo"},
                        {"source": "summary"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
                    ]
                },
                "ใบหัก ณ ที่จ่าย": {
                    "headers": [
                        "เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "ผู้มีหน้าที่หักภาษี (ผู้จ่ายเงิน)", "ผู้ถูกหักภาษี (ผู้รับเงิน)", "จำนวนเงินสุทธิ", "ยอดก่อนภาษี", "จำนวนภาษีที่หัก", "อัตราภาษี", "ประเภทเงินได้", "เลขที่อ้างอิง", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "const:ใบหัก ณ ที่จ่าย"},
                        {"source": "ai_keys:date"},
                        {"source": "ai_keys:payer_name,ผู้จ่ายเงิน"},
                        {"source": "ai_keys:payee_name,ผู้รับเงิน"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "ai_keys:gross_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_amount", "cleaner": "float"},
                        {"source": "ai_keys:wht_rate,wht_percent"},
                        {"source": "ai_keys:wht_type,income_type"},
                        {"source": "ai_keys:ref_number", "cleaner": "literal"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
                    ]
                },
                "ใบเสนอราคา": {
                    "headers": ["เวลาที่บันทึก", "วันที่เอกสาร", "ผู้เสนอราคา", "ลูกค้า", "ยอดเงินสุทธิ", "สถานะ", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "ai_keys:date"},
                        {"source": "sender_name_fallback"},
                        {"source": "receiver_name_fallback"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "const:รออนุมัติ"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
                    ]
                },
                "peak": {
                    "headers": [
                        "ลำดับที่*", "วันที่เอกสาร", "อ้างอิงถึง", "ผู้รับเงิน/คู่ค้า", "เลขทะเบียน 13 หลัก",
                        "เลขสาขา 5 หลัก", "เลขที่ใบกำกับฯ (ถ้ามี)", "วันที่ใบกำกับฯ (ถ้ามี)", "วันที่บันทึกภาษีซื้อ (ถ้ามี)",
                        "ประเภทราคา", "บัญชี", "คำอธิบาย", "จำนวน", "ราคาต่อหน่วย", "อัตราภาษี",
                        "หัก ณ ที่จ่าย (ถ้ามี)", "ชำระโดย", "จำนวนเงินที่ชำระ", "ภ.ง.ด. (ถ้ามี)", "หมายเหตุ", "กลุ่มจัดประเภท", "ไฟล์ต้นฉบับ", "ลิงก์ drive", "ผู้ส่ง (LINE User)"
                    ],
                    "columns": [
                        {"source": "peak_seq"},
                        {"source": "peak_doc_date"},
                        {"source": "ai_keys:ref_number"},
                        {"source": "ai_keys:sender_name,sender,vendor,merchant,payee_name,ผู้รับเงิน,ร้านค้า,ผู้ส่ง"},
                        {"source": "ai_keys:tax_id", "cleaner": "id"},
                        {"source": "ai_keys:branch", "cleaner": "branch"},
                        {"source": "ai_keys:invoice_number,ref_number,เลขที่อ้างอิง"},
                        {"source": "peak_invoice_date"},
                        {"source": "peak_invoice_date"},
                        {"source": "peak_price_type"},
                        {"source": "peak_account_code"},
                        {"source": "summary"},
                        {"source": "const:1"},
                        {"source": "peak_price_unit"},
                        {"source": "peak_vat_rate"},
                        {"source": "peak_wht_rate"},
                        {"source": "peak_payment_channel"},
                        {"source": "ai_keys:net_amount", "cleaner": "float"},
                        {"source": "peak_wht_type"},
                        {"source": "ai_keys:memo,note,remark,หมายเหตุ"},
                        {"source": "const:-"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "line_sender_name"}
                    ]
                },
                "default": {
                    "headers": ["เวลาที่บันทึก", "หมวดหมู่", "วันที่ในเอกสาร", "สรุปข้อมูล", "รหัสกลุ่ม (Batch ID)", "การตรวจสอบ (WHT/QR)", "ไฟล์ต้นฉบับ", "ลิงก์ไฟล์", "AI ถูก/ผิด", "ผู้ส่ง (LINE User)"],
                    "columns": [
                        {"source": "current_datetime"},
                        {"source": "sheet_name"},
                        {"source": "ai_keys:date"},
                        {"source": "summary"},
                        {"source": "batch_id"},
                        {"source": "verification_status"},
                        {"source": "original_filename"},
                        {"source": "file_link"},
                        {"source": "const:-"},
                        {"source": "line_sender_name"}
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

    def _initialize_thread_services(self):
        """Initializes Google API clients specifically for the current thread."""
        try:
            username = getattr(self._local, 'username', None)
            org_id = getattr(self._local, 'org_id', None)
            
            if not username and not org_id:
                try:
                    from flask import session, has_request_context
                    if has_request_context():
                        username = session.get("user")
                        org_id = session.get("org_id", 1)
                except Exception:
                    pass

            thread_creds = getattr(self._local, 'creds', None)
            with self._creds_lock:
                if not thread_creds or not thread_creds.valid:
                    creds = None
                    
                    # 1. Try to load dynamic credentials from database
                    if username or org_id:
                        try:
                            from oauth2_service import oauth2_service
                            creds, source = oauth2_service.build_credentials(username=username, org_id=org_id)
                            if creds:
                                logger.info(f"Loaded dynamic Google credentials from database ({source}) for user={username}, org={org_id}")
                        except Exception as e:
                            logger.error(f"Failed to load dynamic credentials from database: {e}")
                            
                    # 2. Fall back to local file token.json
                    if not creds:
                        token_path = 'token.json'
                        if os.path.exists(token_path):
                            from google.oauth2.credentials import Credentials
                            from google.auth.transport.requests import Request
                            try:
                                creds = Credentials.from_authorized_user_file(token_path, self.scopes)
                                if creds and creds.expired and creds.refresh_token:
                                    creds.refresh(Request())
                                logger.info("Using token.json (OAuth2 User) for Drive services.")
                            except Exception as e:
                                logger.warning(f"Could not load/refresh token.json: {e}")

                    # 3. Fall back to service account JSON env
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

                        # 4. Fall back to local service-account.json
                        if (not creds or not creds.valid) and os.path.exists(self.credentials_path):
                            creds = service_account.Credentials.from_service_account_file(
                                self.credentials_path, scopes=self.scopes
                            )
                            logger.info("Using service-account.json file for Drive services.")
                        
                    self._local.creds = creds
                
            thread_creds = getattr(self._local, 'creds', None)
            is_service_acct = isinstance(thread_creds, service_account.Credentials)
            if not thread_creds or (not is_service_acct and not thread_creds.valid):
                logger.error("No valid credentials found for the thread.")
                self._local.drive_service = None
                self._local.sheets_service = None
                return

            self._local.drive_service = build('drive', 'v3', credentials=thread_creds, cache_discovery=False)
            self._local.sheets_service = build('sheets', 'v4', credentials=thread_creds, cache_discovery=False)
        except Exception as e:
            logger.error(f"Failed to initialize thread services: {e}")
            self._local.drive_service = None
            self._local.sheets_service = None

    @thread_safe
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

    def _sheet_exec(self, build_request_fn):
        """Execute a Sheets API request. If 404 (spreadsheet deleted/trashed) → recreate immediately and retry once."""
        try:
            return build_request_fn().execute()
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning("⚠️ Spreadsheet 404 — recreating and retrying")
                self._create_new_spreadsheet()
                return build_request_fn().execute()
            raise

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

            # Set thread-local override immediately so spreadsheet_id property returns new_id
            # for all subsequent calls in this request, before any DB write propagates
            self._local.spreadsheet_id_override = new_id

            # Persist to DB — update the CORRECT table based on which token is actually in use
            import database as _db
            username = getattr(self._local, 'username', None)
            org_id = getattr(self._local, 'org_id', None)

            try:
                _, source = _db.resolve_google_token(username, org_id)
            except Exception:
                source = "none"

            if source == "org_admin_personal" and org_id:
                # org_google_tokens has no refresh_token → resolve falls to admin's user_google_tokens
                # Must update the admin's personal row, not org table
                admin_token = _db.get_org_admin_google_token(org_id)
                if admin_token and admin_token.get('username'):
                    _db.set_user_spreadsheet_id(admin_token['username'], new_id)
                    logger.info(f"💾 Updated admin user '{admin_token['username']}' spreadsheet_id → {new_id}")
            elif source == "personal" and username:
                _db.set_user_spreadsheet_id(username, new_id)
            elif username:
                _db.set_user_spreadsheet_id(username, new_id)

            # Always also write to org table as safety net (for when org connects directly later)
            if org_id:
                _db.set_org_spreadsheet_id(org_id, new_id)

            logger.info(f"🚀 Created new Spreadsheet: {new_id} (source={source}, org={org_id}, user={username})")
        except Exception as e:
            logger.error(f"❌ Failed to create new spreadsheet: {e}")

    def freeze_sheet(self, sheet_title):
        """Locks the first row (headers) and applies royal blue header styling and data validations."""
        if not self.sheets_service or not self.spreadsheet_id:
            return
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheet = next((s for s in spreadsheet.get('sheets', []) if s['properties']['title'] == sheet_title), None)
            if existing_sheet is None:
                return
            sheet_id = existing_sheet['properties']['sheetId']

            # Skip custom styling for the dashboard sheet, only apply grid styling if needed
            is_dashboard = sheet_title == "📊 แดชบอร์ดสรุป"
            
            requests = []
            
            # Freeze the first row
            requests.append({
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_id,
                        "gridProperties": {
                            "frozenRowCount": 0 if is_dashboard else 1
                        }
                    },
                    "fields": "gridProperties.frozenRowCount"
                }
            })
            
            num_cols = 20
            if not is_dashboard:
                # Get the number of columns in the header to style
                try:
                    res = self.sheets_service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id, range=f"'{sheet_title}'!A1:Z1"
                    ).execute()
                    headers_row = res.get('values', [[]])[0]
                    num_cols = len(headers_row) if headers_row else 20
                except Exception:
                    num_cols = 20
                
                # Apply royal blue background (#1D4ED8) and white bold text formatting
                requests.append({
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 1,
                            "startColumnIndex": 0,
                            "endColumnIndex": num_cols
                        },
                        "cell": {
                            "userEnteredFormat": {
                                "backgroundColor": {
                                    "red": 0.1137,     # 29/255 -> #1D4ED8
                                    "green": 0.3098,   # 78/255
                                    "blue": 0.8471     # 216/255
                                },
                                "textFormat": {
                                    "foregroundColor": {
                                        "red": 1.0,
                                        "green": 1.0,
                                        "blue": 1.0
                                    },
                                    "bold": True,
                                    "fontSize": 10,
                                    "fontFamily": "Inter"
                                },
                                "horizontalAlignment": "CENTER",
                                "verticalAlignment": "MIDDLE"
                              }
                        },
                        "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
                    }
                })
                
                # Apply data validation dropdown and conditional formatting for Column Q ("ตามใบกำกับ" at index 16)
                if sheet_title == "ใบเสร็จ/ใบกำกับภาษี":
                    requests.append({
                        "setDataValidation": {
                            "range": {
                                "sheetId": sheet_id,
                                "startRowIndex": 1,      # Row 2 onwards
                                "startColumnIndex": 16,  # Column Q
                                "endColumnIndex": 17
                            },
                            "rule": {
                                "condition": {
                                    "type": "ONE_OF_LIST",
                                    "values": [
                                        {"userEnteredValue": "ต้องตาม"},
                                        {"userEnteredValue": "ไม่ต้องตาม"}
                                    ]
                                },
                                "showCustomUi": True,
                                "strict": True
                            }
                        }
                    })

                    # Clear existing conditional formatting rules to prevent duplicates
                    existing_rules = existing_sheet.get('conditionalFormats', [])
                    for _ in range(len(existing_rules)):
                        requests.append({
                            "deleteConditionalFormatRule": {
                                "sheetId": sheet_id,
                                "index": 0
                            }
                        })

                    # Add Rule 1: "ต้องตาม" (Pastel light red background with dark red text)
                    requests.append({
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "startColumnIndex": 16,
                                    "endColumnIndex": 17
                                }],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": "ต้องตาม"}]
                                    },
                                    "format": {
                                        "backgroundColor": {"red": 0.992, "green": 0.925, "blue": 0.925},
                                        "textFormat": {
                                            "foregroundColor": {"red": 0.863, "green": 0.204, "blue": 0.204},
                                            "bold": True
                                        }
                                    }
                                }
                            },
                            "index": 0
                        }
                    })

                    # Add Rule 2: "ไม่ต้องตาม" (Pastel light gray/green background with dark slate text)
                    requests.append({
                        "addConditionalFormatRule": {
                            "rule": {
                                "ranges": [{
                                    "sheetId": sheet_id,
                                    "startRowIndex": 1,
                                    "startColumnIndex": 16,
                                    "endColumnIndex": 17
                                }],
                                "booleanRule": {
                                    "condition": {
                                        "type": "TEXT_EQ",
                                        "values": [{"userEnteredValue": "ไม่ต้องตาม"}]
                                    },
                                    "format": {
                                        "backgroundColor": {"red": 0.941, "green": 0.949, "blue": 0.961},
                                        "textFormat": {
                                            "foregroundColor": {"red": 0.419, "green": 0.447, "blue": 0.502},
                                            "bold": True
                                        }
                                    }
                                }
                            },
                            "index": 1
                        }
                    })

            # Auto-resize columns to fit content beautifully
            requests.append({
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheet_id,
                        "dimension": "COLUMNS",
                        "startIndex": 0,
                        "endIndex": num_cols
                    }
                }
            })

            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id, 
                body={"requests": requests}
            ).execute()
            logger.info(f"📌 Froze, styled, and auto-resized sheet columns: {sheet_title}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to freeze/style headers for sheet '{sheet_title}': {e}")

    def freeze_all_existing_sheets(self):
        """Iterates over all sheets in the spreadsheet and freezes/styles them."""
        if not self.sheets_service or not self.spreadsheet_id:
            return
        try:
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            for s in spreadsheet.get('sheets', []):
                title = s['properties']['title']
                self.freeze_sheet(title)
        except Exception as e:
            logger.warning(f"⚠️ Failed to freeze/style all sheets: {e}")

    def ensure_essential_sheets(self):
        """Ensures all essential sheets exist in the spreadsheet and have standard headers & styling."""
        if not self.sheets_service or not self.spreadsheet_id:
            return
        
        try:
            # 1. Fetch existing sheets
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            existing_sheets = {s['properties']['title']: s['properties']['sheetId'] for s in spreadsheet.get('sheets', [])}
            
            # 2. Define essential sheets and their headers
            registry = self._load_sheet_schema()
            schemas = registry.get("schemas", {})
            
            essential_sheets = {
                "บันทึกค่าใช้จ่าย": schemas.get("บันทึกค่าใช้จ่าย", {}).get("headers", []),
                "ใบเสร็จ/ใบกำกับภาษี": schemas.get("ใบเสร็จ/ใบกำกับภาษี", {}).get("headers", []),
                "สลิปโอนเงิน": schemas.get("สลิปโอนเงิน", {}).get("headers", []),
                "สรุปกระทบยอด": ["วันที่ประมวลผล", "สถานะ", "วันที่เอกสาร", "ยอดเงิน", "คู่ค้า/ร้านค้า", "ลิงก์สลิป", "ลิงก์ใบกำกับ", "หมายเหตุ"],
                "peak": schemas.get("peak", {}).get("headers", [])
            }
            
            # 3. Create missing sheets
            for sheet_title, headers in essential_sheets.items():
                if sheet_title not in existing_sheets:
                    logger.info(f"➕ Pre-creating missing essential sheet: {sheet_title}")
                    try:
                        res = self.sheets_service.spreadsheets().batchUpdate(
                            spreadsheetId=self.spreadsheet_id, 
                            body={'requests': [{'addSheet': {'properties': {'title': sheet_title}}}]}
                        ).execute()
                        # Extract newly created sheetId
                        new_sheet_id = res['replies'][0]['addSheet']['properties']['sheetId']
                        existing_sheets[sheet_title] = new_sheet_id
                        
                        # Initialize headers
                        self.sheets_service.spreadsheets().values().update(
                            spreadsheetId=self.spreadsheet_id,
                            range=f"'{sheet_title}'!A1",
                            valueInputOption="RAW",
                            body={"values": [headers]}
                        ).execute()
                    except Exception as ce:
                        logger.error(f"❌ Failed to create sheet {sheet_title}: {ce}")
            
            # 4. Update "📊 แดชบอร์ดสรุป" and "สรุปกระทบยอด" if needed
            self.update_dashboard()
            
            # 5. Apply freezing, styling, and data validation to all sheets
            self.freeze_all_existing_sheets()
            
            # 6. Delete default sheet "Sheet1" or "ชีต1" if we have other sheets
            sheets = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute().get('sheets', [])
            if len(sheets) > 1:
                for s in sheets:
                    title = s['properties']['title']
                    if title in ["Sheet1", "ชีต1"]:
                        s_id = s['properties']['sheetId']
                        self.sheets_service.spreadsheets().batchUpdate(
                            spreadsheetId=self.spreadsheet_id, 
                            body={'requests': [{'deleteSheet': {'sheetId': s_id}}]}
                        ).execute()
                        logger.info(f"🗑 Deleted default sheet: {title}")
                        break
        except Exception as e:
            logger.error(f"⚠️ ensure_essential_sheets error: {e}")

    def upload_file(self, file_content, filename, mimetype, folder_id=None, org_id=None, username=None):
        """Uploads file with [org_N/]Year/Month/Day folder structure."""
        if org_id or username:
            self.set_context(username=username, org_id=org_id)
            
        if not self.drive_service:
            logger.error("❌ upload_file: drive_service is not initialized (Google Drive not connected)")
            return None, "Service not initialized"
        try:
            base_p_id = self._safe_folder_id(folder_id or self.parent_folder_id)
            now = datetime.now()
            year_str, month_str, day_str = now.strftime("%Y"), now.strftime("%m"), now.strftime("%d")

            p_id = base_p_id
            # When using shared Drive (no specific folder_id), prefix with org folder
            if not folder_id and org_id:
                p_id = self._get_or_create_folder(f"org_{org_id}", p_id)

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

    def _safe_folder_id(self, folder_id) -> str:
        """Return a valid, non-trashed folder ID.
        Rule: never interact with trashed items — if a folder is trashed or gone, fall back to parent immediately."""
        if not folder_id:
            return self._verify_or_recreate_parent(self.parent_folder_id or "")
        try:
            meta = self.drive_service.files().get(
                fileId=folder_id, fields='id,trashed', supportsAllDrives=True
            ).execute()
            if not meta.get('trashed'):
                return folder_id  # Valid and not trashed — use as-is
            logger.info(f"⚠️ Folder {folder_id} is in trash — ignoring, falling back to parent")
        except Exception:
            pass  # Folder permanently deleted
        # Trash or gone — use verified parent instead
        return self._verify_or_recreate_parent(self.parent_folder_id or folder_id)

    def _verify_or_recreate_parent(self, p_id) -> str:
        """Verify parent folder exists and is NOT trashed; recreate if missing/trashed. Returns valid folder ID."""
        if p_id:
            try:
                result = self.drive_service.files().get(
                    fileId=p_id, fields='id,trashed', supportsAllDrives=True
                ).execute()
                if not result.get('trashed'):
                    return p_id  # Still alive and clean
                logger.info(f"⚠️ Parent folder {p_id} is in trash — ignoring, will recreate")
            except Exception:
                pass  # 404 or permission error — folder is gone

        # Rebuild parent folder name from context
        username = getattr(self._local, 'username', None)
        org_id = getattr(self._local, 'org_id', None)

        import database as _db
        if org_id:
            try:
                conn = _db._get_conn()
                row = conn.execute("SELECT name FROM organizations WHERE id = ?", (org_id,)).fetchone()
                conn.close()
                org_name = row[0] if row else f"org_{org_id}"
            except Exception:
                org_name = f"org_{org_id}"
            folder_name = f'OrgChat AI — {org_name}'
        else:
            folder_name = 'OrgChat AI — เอกสารบัญชี'

        # Search for existing folder with same name before creating
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive_service.files().list(q=query, fields="files(id)", pageSize=1).execute()
        files = results.get('files', [])
        if files:
            new_id = files[0]['id']
        else:
            folder_meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            folder = self.drive_service.files().create(body=folder_meta, fields='id').execute()
            new_id = folder.get('id')

        # Persist new folder ID to DB and thread-local cache
        if org_id:
            _db.set_org_drive_folder_id(org_id, new_id)
        elif username:
            _db.set_user_drive_folder_id(username, new_id)
        self._parent_folder_id = new_id
        # Invalidate subfolder cache so next list_subfolders re-fetches with new parent
        GoogleWorkspaceManager._subfolder_cache = {
            k: v for k, v in GoogleWorkspaceManager._subfolder_cache.items()
            if not k.startswith(f"{org_id}:{username}:")
        }
        logger.info(f"♻️ Recreated parent Drive folder '{folder_name}' → {new_id} (org={org_id}, user={username})")
        return new_id

    @thread_safe
    def _get_or_create_folder(self, folder_name, parent_id):
        query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        results = self.drive_service.files().list(q=query, fields="files(id)", supportsAllDrives=True).execute()
        files = results.get('files', [])
        if files: return files[0]['id']
        
        metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_id]}
        folder = self.drive_service.files().create(body=metadata, fields='id', supportsAllDrives=True).execute()
        return folder.get('id')

    # Short-lived cache: {cache_key: {"folders": [...], "ts": float}}
    # Avoids redundant Drive API calls when multiple uploads arrive close together
    _subfolder_cache: dict = {}
    _SUBFOLDER_CACHE_TTL = 60  # seconds

    def list_subfolders(self, parent_id=None):
        if not self.drive_service: return []
        p_id = parent_id or self.parent_folder_id
        if not p_id: return []

        org_id = getattr(self._local, 'org_id', None)
        username = getattr(self._local, 'username', None)

        # Proactively verify/recreate parent if it's the root parent folder
        if not parent_id or parent_id == self.parent_folder_id:
            try:
                p_id = self._verify_or_recreate_parent(p_id)
            except Exception as pe:
                logger.error(f"❌ list_subfolders parent verification failed: {pe}")
                return []

        cache_key = f"{org_id}:{username}:{p_id}"

        # Return from cache if fresh — skip Drive API round-trip
        cached = GoogleWorkspaceManager._subfolder_cache.get(cache_key)
        if cached and (time.time() - cached['ts']) < GoogleWorkspaceManager._SUBFOLDER_CACHE_TTL:
            return cached['folders']

        try:
            # 1. Try list directly - list BOTH folders and files
            query = f"'{p_id}' in parents and trashed = false"
            try:
                results = self.drive_service.files().list(
                    q=query, 
                    fields="files(id, name, mimeType, iconLink, thumbnailLink, webViewLink)", 
                    supportsAllDrives=True
                ).execute()
            except HttpError as he:
                if he.resp.status in (400, 404):
                    # Parent gone or invalid — verify/recreate and retry once
                    logger.info(f"⚠️ list_subfolders parent {p_id} returned {he.resp.status} — recreating")
                    p_id = self._verify_or_recreate_parent(p_id)
                    results = self.drive_service.files().list(
                        q=f"'{p_id}' in parents and trashed = false",
                        fields="files(id, name, mimeType, iconLink, thumbnailLink, webViewLink)", 
                        supportsAllDrives=True
                    ).execute()
                else:
                    raise
            existing_folders = results.get('files', [])
            
            # 2. Define essential folders matching the luxury minimal structure
            essential_folders = [
                "เงินยืมกรรมการ",
                "บัตรประชาชน",
                "สลิปโอนเงิน",
                "ใบเสร็จ_ใบกำกับ",
                "ใบหัก ณ ที่จ่าย",
                "ใบเสนอราคา",
                "statement",
                "ทั่วไป",
                "อื่นๆ"
            ]
            
            # Check if any folders exist in the returned list
            has_folders = any(f.get('mimeType') == 'application/vnd.google-apps.folder' for f in existing_folders)
            if not has_folders:
                new_folders = []
                for folder_name in essential_folders:
                    try:
                        fid = self._get_or_create_folder(folder_name, p_id)
                        new_folders.append({
                            'id': fid, 
                            'name': folder_name,
                            'mimeType': 'application/vnd.google-apps.folder',
                            'iconLink': '',
                            'thumbnailLink': '',
                            'webViewLink': ''
                        })
                    except Exception as ce:
                        logger.error(f"Error creating essential folder {folder_name}: {ce}")
                # Don't cache first-time setup result; let next request re-verify
                return new_folders + [f for f in existing_folders if f.get('mimeType') != 'application/vnd.google-apps.folder']

            # Store in cache before returning
            GoogleWorkspaceManager._subfolder_cache[cache_key] = {"folders": existing_folders, "ts": time.time()}
            return existing_folders
        except Exception as e:
            logger.error(f"Error in list_subfolders: {e}")
            return []

    @thread_safe
    def auto_reconcile_internal(self):
        """Reconciles Bank Statements (Master Reference) ↔ Payment Slips ↔ Invoices (3-Way Match)."""
        if not self.sheets_service or not self.spreadsheet_id: return
        
        def col_idx_to_letter(idx):
            letter = ""
            while idx >= 0:
                letter = chr(idx % 26 + ord('A')) + letter
                idx = idx // 26 - 1
            return letter
            
        idx_wht = 8  # Default WHT column index for slip
        
        try:
            # 0. Check sheet titles
            spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
            sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]

            # 1. Read Slips
            slips = []
            if "สลิปโอนเงิน" in sheet_titles:
                try:
                    res_slip = self.sheets_service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id, range="'สลิปโอนเงิน'!A1:S"
                    ).execute()
                    slip_vals = res_slip.get('values', [])
                    if slip_vals and len(slip_vals) > 1:
                        header_row = slip_vals[0]
                        data_rows = slip_vals[1:]
                        idx_date = next((i for i, h in enumerate(header_row) if "วันที่" in h), 2)
                        idx_amt = next((i for i, h in enumerate(header_row) if "จำนวนเงิน" in h or "สุทธิ" in h), 8)
                        idx_rec = next((i for i, h in enumerate(header_row) if "ผู้รับ" in h), 4)
                        idx_link = next((i for i, h in enumerate(header_row) if "ลิงก์" in h), 16)
                        idx_wht = next((i for i, h in enumerate(header_row) if "หัก" in h), 8)
                        for r_idx, row in enumerate(data_rows):
                            if len(row) <= max(idx_date, idx_amt): continue
                            slip_wht_val = str(row[idx_wht]).strip() if len(row) > idx_wht else "-"
                            slip_wht_present = (slip_wht_val == "หัก ณ ที่จ่าย" or "WHT" in slip_wht_val.upper() or "EXWHT" in slip_wht_val.upper())
                            try:
                                if not slip_wht_present and slip_wht_val != '-':
                                    if float(slip_wht_val.replace(',', '').strip()) > 0:
                                        slip_wht_present = True
                            except Exception:
                                pass
                            slips.append({
                                'index': r_idx,
                                'date': row[idx_date],
                                'amount': str(row[idx_amt]).replace(',', '').strip(),
                                'receiver': row[idx_rec] if len(row) > idx_rec else "-",
                                'link': row[idx_link] if len(row) > idx_link else "",
                                'wht_present': slip_wht_present
                            })
                except Exception as e:
                    logger.warning(f"Error loading slips for reconciliation: {e}")

            # 2. Read Invoices
            invoices = []
            inv_header = []
            if "ใบเสร็จ/ใบกำกับภาษี" in sheet_titles:
                try:
                    res_inv = self.sheets_service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id, range="'ใบเสร็จ/ใบกำกับภาษี'!A1:W"
                    ).execute()
                    inv_vals = res_inv.get('values', [])
                    if inv_vals and len(inv_vals) > 1:
                        inv_header = inv_vals[0]
                        data_rows = inv_vals[1:]
                        i_idx_date = next((i for i, h in enumerate(inv_header) if "วันที่" in h), 2)
                        i_idx_amt = next((i for i, h in enumerate(inv_header) if "จำนวนเงิน" in h or "สุทธิ" in h), 9)
                        i_idx_wht = next((i for i, h in enumerate(inv_header) if "WHT" in h or "หัก" in h), 13)
                        i_idx_vend = next((i for i, h in enumerate(inv_header) if "ผู้ส่ง" in h or "ร้านค้า" in h or "คู่ค้า" in h), 3)
                        i_idx_link = next((i for i, h in enumerate(inv_header) if "ลิงก์" in h), 17)
                        i_idx_gross = next((i for i, h in enumerate(inv_header) if "ก่อน" in h or "gross" in h.lower()), 10)
                        for r_idx, row in enumerate(data_rows):
                            if len(row) <= max(i_idx_date, i_idx_amt): continue
                            
                            net_amt = 0.0
                            wht_val = 0.0
                            gross_val = 0.0
                            wht_present = False
                            
                            try:
                                net_amt = float(str(row[i_idx_amt]).replace(',', '').strip()) if row[i_idx_amt] != '-' else 0.0
                            except Exception:
                                pass
                                
                            if len(row) > i_idx_wht:
                                val_str = str(row[i_idx_wht]).strip()
                                if val_str == "หัก ณ ที่จ่าย" or "WHT" in val_str.upper() or "EXWHT" in val_str.upper():
                                    wht_present = True
                                elif val_str != '-':
                                    try:
                                        wht_val = float(val_str.replace(',', '').strip())
                                        if wht_val > 0:
                                            wht_present = True
                                    except Exception:
                                        pass
                                        
                            try:
                                gross_val = float(str(row[i_idx_gross]).replace(',', '').strip()) if len(row) > i_idx_gross and row[i_idx_gross] != '-' else 0.0
                            except Exception:
                                pass

                            invoices.append({
                                'index': r_idx,
                                'date': row[i_idx_date],
                                'net_amount': net_amt,
                                'wht_amount': wht_val,
                                'gross_amount': gross_val,
                                'wht_present': wht_present,
                                'vendor': row[i_idx_vend] if len(row) > i_idx_vend else "-",
                                'link': row[i_idx_link] if len(row) > i_idx_link else ""
                            })
                except Exception as e:
                    logger.warning(f"Error loading invoices for reconciliation: {e}")

            # 3. Read Statements (Primary Master Reference)
            statements = []
            if "สเตตเมนต์" in sheet_titles:
                try:
                    res_stmt = self.sheets_service.spreadsheets().values().get(
                        spreadsheetId=self.spreadsheet_id, range="'สเตตเมนต์'!A1:M"
                    ).execute()
                    stmt_vals = res_stmt.get('values', [])
                    if stmt_vals and len(stmt_vals) > 1:
                        s_header = stmt_vals[0]
                        s_data = stmt_vals[1:]
                        s_idx_date = next((i for i, h in enumerate(s_header) if "วันที่" in h or "เอกสาร" in h), 1)
                        s_idx_out = next((i for i, h in enumerate(s_header) if "ถอน" in h or "ออก" in h), 5)
                        s_idx_cparty = next((i for i, h in enumerate(s_header) if "คู่ค้า" in h or "รายละเอียด" in h), 11)
                        s_idx_link = next((i for i, h in enumerate(s_header) if "ลิงก์" in h), 12)
                        for r_idx, row in enumerate(s_data):
                            if len(row) <= max(s_idx_date, s_idx_out): continue
                            amount = str(row[s_idx_out]).replace(',', '').strip()
                            if amount == '-' or not amount or amount == '0.0': continue
                            statements.append({
                                'index': r_idx,
                                'date': row[s_idx_date],
                                'amount': float(amount),
                                'counterparty': row[s_idx_cparty] if len(row) > s_idx_cparty else "-",
                                'link': row[s_idx_link] if len(row) > s_idx_link else ""
                            })
                except Exception as e:
                    logger.warning(f"Error loading statements for reconciliation: {e}")

            # If absolutely no data loaded, stop.
            if not statements and not slips and not invoices:
                self.update_dashboard()
                return

            # Helper functions for Date parsing and name normalization
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
                        except Exception: continue
                    return None
                except Exception: return None

            matches = []
            matched_slip_indices = set()
            matched_invoice_indices = set()

            # Pass 1: Match from Statement (Primary Master)
            for stmt in statements:
                s_amount = stmt['amount']
                s_date = parse_date(stmt['date'])
                s_receiver = stmt['counterparty']

                matched_slip = None
                matched_inv = None

                # Find matching Payment Slip
                for slip in slips:
                    if slip['index'] in matched_slip_indices: continue
                    try:
                        slip_amt = float(slip['amount'])
                    except Exception:
                        slip_amt = 0
                    
                    if abs(slip_amt - s_amount) < 5.0:
                        slip_date = parse_date(slip['date'])
                        date_match = (abs((s_date - slip_date).days) <= 3) if s_date and slip_date else False
                        name_match = (get_name_similarity(slip['receiver'], s_receiver) > 0.7) if slip['receiver'] != '-' and s_receiver != '-' else False
                        if date_match or name_match:
                            matched_slip = slip
                            matched_slip_indices.add(slip['index'])
                            break

                # Find matching Invoice
                for inv in invoices:
                    if inv['index'] in matched_invoice_indices: continue
                    
                    # 3-Way Match Check (Gross, Net, WHT logic)
                    total_before_wht = inv['net_amount'] + inv['wht_amount'] if inv['wht_amount'] > 0 else inv['net_amount']
                    amount_match = False
                    wht_correct = True

                    if abs(s_amount - inv['net_amount']) < 5.0:
                        amount_match = True
                        wht_correct = True
                    elif inv['wht_amount'] > 0 and abs(s_amount - total_before_wht) < 5.0:
                        amount_match = True
                        wht_correct = False
                    elif inv['gross_amount'] > 0 and abs(s_amount - inv['gross_amount']) < 5.0:
                        amount_match = True
                        wht_correct = True

                    if amount_match:
                        inv_date = parse_date(inv['date'])
                        date_match = (abs((s_date - inv_date).days) <= 7) if s_date and inv_date else False
                        name_match = (get_name_similarity(inv['vendor'], s_receiver) > 0.7) if inv['vendor'] != '-' and s_receiver != '-' else False
                        if date_match or name_match:
                            matched_inv = inv
                            matched_invoice_indices.add(inv['index'])
                            break

                # Determine Status and write note
                s_date_display = stmt['date']
                s_rec_upper = s_receiver.upper()
                is_internal = "ฮาร์ทวอม" in s_rec_upper or "HEARTWARMING" in s_rec_upper
                
                # Check for other bank-specific transaction codes
                is_fee = "FEE" in s_rec_upper or "ค่าธรรมเนียม" in s_receiver

                if is_internal:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "🔄 โอนย้ายระหว่างบัญชี",
                        s_date_display,
                        s_amount,
                        s_receiver,
                        matched_slip['link'] if matched_slip else "-",
                        "-",
                        "โอนย้ายระหว่างบัญชีภายใน บจก. ฮาร์ทวอมมิ่ง (ไม่ต้องมีใบกำกับ)"
                    ])
                elif is_fee:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "✅ ชำระค่าธรรมเนียม",
                        s_date_display,
                        s_amount,
                        s_receiver,
                        "-",
                        "-",
                        "ค่าธรรมเนียมธนาคาร / บริการทางการเงิน (บันทึกรายจ่ายตรง)"
                    ])
                elif matched_slip and matched_inv:
                    # Auto-backfill slip WHT if invoice has WHT and slip doesn't
                    if matched_inv.get('wht_present') and not matched_slip.get('wht_present'):
                        try:
                            col_letter = col_idx_to_letter(idx_wht)
                            sheet_range = f"'สลิปโอนเงิน'!{col_letter}{matched_slip['index'] + 2}"
                            self.sheets_service.spreadsheets().values().update(
                                spreadsheetId=self.spreadsheet_id,
                                range=sheet_range,
                                valueInputOption="RAW",
                                body={"values": [["หัก ณ ที่จ่าย"]]}
                            ).execute()
                            logger.info(f"✨ Auto-backfilled WHT column for slip at row {matched_slip['index'] + 2} from matched invoice")
                            matched_slip['wht_present'] = True
                        except Exception as backfill_err:
                            logger.warning(f"Failed to backfill slip WHT: {backfill_err}")

                    status = "✅ จับคู่สำเร็จ (3-Way)"
                    note = f"พบจากสเตตเมนต์: จับคู่สลิปโอนเงิน + ใบกำกับภาษีเรียบร้อย"
                    if matched_inv.get('wht_present') or matched_inv['wht_amount'] > 0:
                        note += " (หัก WHT ถูกต้อง)" if wht_correct else " (⚠️ ลืมหัก WHT?)"
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        status,
                        s_date_display,
                        s_amount,
                        matched_inv['vendor'],
                        matched_slip['link'],
                        matched_inv['link'],
                        note
                    ])
                elif matched_slip and not matched_inv:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "⚠️ รอใบกำกับ (สลิปตรง)",
                        s_date_display,
                        s_amount,
                        matched_slip['receiver'],
                        matched_slip['link'],
                        "-",
                        "พบยอดในสเตตเมนต์ตรงกับสลิปโอนเงินแล้ว แต่ยังไม่พบใบกำกับภาษีที่ยอดตรงกัน"
                    ])
                elif matched_inv and not matched_slip:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "⚠️ รอสลิปโอนเงิน (ใบกำกับตรง)",
                        s_date_display,
                        s_amount,
                        matched_inv['vendor'],
                        "-",
                        matched_inv['link'],
                        "พบยอดในสเตตเมนต์ตรงกับใบกำกับภาษีแล้ว แต่ระบบตรวจไม่พบสลิปโอนเงิน"
                    ])
                else:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "❌ รอเอกสาร (ไม่พบหลักฐาน)",
                        s_date_display,
                        s_amount,
                        s_receiver,
                        "-",
                        "-",
                        "พบยอดถอนออกในสเตตเมนต์ธนาคาร แต่ยังไม่พบสลิปโอนเงินหรือใบกำกับภาษีในระบบ"
                    ])

            # Pass 2: Unmatched Slips (Check if they match any unmatched Invoice)
            for slip in slips:
                if slip['index'] in matched_slip_indices: continue
                
                # Check if this slip matches an unmatched invoice
                matched_inv = None
                try:
                    slip_amt = float(slip['amount'])
                except Exception:
                    slip_amt = 0

                for inv in invoices:
                    if inv['index'] in matched_invoice_indices: continue
                    total_before_wht = inv['net_amount'] + inv['wht_amount'] if inv['wht_amount'] > 0 else inv['net_amount']
                    amount_match = abs(slip_amt - inv['net_amount']) < 5.0 or abs(slip_amt - total_before_wht) < 5.0 or abs(slip_amt - inv['gross_amount']) < 5.0
                    
                    if amount_match:
                        s_date = parse_date(slip['date'])
                        inv_date = parse_date(inv['date'])
                        date_match = (abs((s_date - inv_date).days) <= 7) if s_date and inv_date else False
                        name_match = (get_name_similarity(inv['vendor'], slip['receiver']) > 0.7) if inv['vendor'] != '-' and slip['receiver'] != '-' else False
                        if date_match or name_match:
                            matched_inv = inv
                            matched_invoice_indices.add(inv['index'])
                            break

                if matched_inv:
                    # Auto-backfill slip WHT if invoice has WHT and slip doesn't
                    if matched_inv.get('wht_present') and not slip.get('wht_present'):
                        try:
                            col_letter = col_idx_to_letter(idx_wht)
                            sheet_range = f"'สลิปโอนเงิน'!{col_letter}{slip['index'] + 2}"
                            self.sheets_service.spreadsheets().values().update(
                                spreadsheetId=self.spreadsheet_id,
                                range=sheet_range,
                                valueInputOption="RAW",
                                body={"values": [["หัก ณ ที่จ่าย"]]}
                            ).execute()
                            logger.info(f"✨ Auto-backfilled WHT column for slip at row {slip['index'] + 2} from invoice (Pass 2)")
                            slip['wht_present'] = True
                        except Exception as backfill_err:
                            logger.warning(f"Failed to backfill slip WHT in Pass 2: {backfill_err}")

                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "📬 รอสเตตเมนต์ (สลิป ↔ ใบกำกับ)",
                        slip['date'],
                        slip_amt,
                        matched_inv['vendor'],
                        slip['link'],
                        matched_inv['link'],
                        "มีสลิปโอนเงินคู่กับใบกำกับภาษีเรียบร้อยแล้ว แต่ยังไม่พบรายการถอนแสดงในสเตตเมนต์ธนาคาร"
                    ])
                else:
                    matches.append([
                        dt.now().strftime("%d/%m/%Y %H:%M"),
                        "📬 รอสเตตเมนต์ (สลิปเปล่า)",
                        slip['date'],
                        slip_amt,
                        slip['receiver'],
                        slip['link'],
                        "-",
                        "พบสลิปโอนเงินแล้ว แต่ยังไม่มีประวัติการชำระแสดงบนสเตตเมนต์ธนาคาร"
                    ])

            # Pass 3: Unmatched Invoices
            for inv in invoices:
                if inv['index'] in matched_invoice_indices: continue
                matches.append([
                    dt.now().strftime("%d/%m/%Y %H:%M"),
                    "📬 รอสเตตเมนต์ (ใบกำกับเปล่า)",
                    inv['date'],
                    inv['net_amount'],
                    inv['vendor'],
                    "-",
                    inv['link'],
                    "มีใบกำกับภาษีเข้าระบบแล้ว แต่ยังไม่พบประวัติการทำรายการโอนจ่ายเงินในระบบและสเตตเมนต์"
                ])

            # 4. Write to "สรุปกระทบยอด"
            sheet_name = "สรุปกระทบยอด"
            headers = ["วันที่ประมวลผล", "สถานะ", "วันที่เอกสาร", "ยอดเงิน", "คู่ค้า/ร้านค้า", "ลิงก์สลิป", "ลิงก์ใบกำกับ", "หมายเหตุ"]
            try:
                self.sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id, 
                    body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
                ).execute()
            except Exception: pass

            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1",
                valueInputOption="RAW", body={"values": [headers]}
            ).execute()
            
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A2:Z"
            ).execute()
            
            if matches:
                self.sheets_service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A2",
                    valueInputOption="RAW", body={"values": matches}
                ).execute()

            self.update_dashboard()
            logger.info("🎯 3-Way Reconciliation & Dashboard updated successfully using Statement as master reference.")
        except Exception as e:
            logger.error(f"Reconciliation error: {e}")

    def update_dashboard(self):
        """Creates or updates a high-level Dashboard sheet with formulas."""
        if not self.sheets_service or not self.spreadsheet_id: return
        sheet_name = "📊 แดชบอร์ดสรุป"
        try:
            try:
                self.sheets_service.spreadsheets().batchUpdate(spreadsheetId=self.spreadsheet_id, body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}).execute()
            except Exception: pass

            dashboard_data = [
                ["สรุปภาพรวมบัญชี", "", "", f"อัปเดตล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M')}"],
                ["", "", "", ""],
                ["💰 ยอดค่าใช้จ่ายแยกตามหมวดหมู่", "", "🧾 สรุปภาษีประจำเดือน", ""],
                ["หมวดหมู่", "ยอดรวมสุทธิ", "รายการภาษี", "ยอดรวม"],
                ["สลิปโอนเงิน", "=SUM('สลิปโอนเงิน'!G:G)", "VAT (7%) รวม", "=SUM('ใบเสร็จ/ใบกำกับภาษี'!M:M)"],
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

    @thread_safe
    def log_expense(self, data, sheet_name=None, org_id=None, username=None):
        """Logs data with strict Thai headers and legacy cleanup."""
        if org_id or username:
            self.set_context(username=username, org_id=org_id)
        if not self.sheets_service:
            logger.error("❌ log_expense: sheets_service is not initialized (Google Sheets not connected)")
            return None
        self._validate_or_create_spreadsheet()
        if not self.spreadsheet_id:
            logger.error("❌ log_expense: spreadsheet_id is missing (Spreadsheet not created/found)")
            return None

        import json
        try:
            def clean_val(v):
                if v is None or v == '-': return 0.0
                try: return float(str(v).replace(',', '').strip())
                except Exception: return 0.0
                
            def clean_id(v):
                if v is None: return '-'
                s = str(v).replace('-', '').replace(' ', '').strip()
                if not s or s == '-': return '-'
                s_digits = re.sub(r'\D', '', s)
                if len(s_digits) in [10, 13]:
                    return f"'{s_digits}"
                return s

            def clean_branch(v):
                if v is None: return "00000"
                s = str(v).replace('-', '').replace(' ', '').strip()
                if not s or s == '-': return "00000"
                s_digits = re.sub(r'\D', '', s)
                if not s_digits: return "00000"
                return f"'{int(s_digits):05d}"

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
            
            # Use provided sheet_name if available, otherwise map from AI category
            if not sheet_name:
                sheet_name = category_map.get(raw_category, raw_category).strip()

            # Fetch existing sheet titles to avoid 400 Bad Request
            existing_sheets = []
            try:
                spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
            except HttpError as _he:
                if _he.resp.status == 404:
                    # Spreadsheet gone mid-execution — recreate and use new ID immediately
                    logger.warning(f"⚠️ Spreadsheet 404 in log_expense — recreating now")
                    self._create_new_spreadsheet()
                    try:
                        spreadsheet = self.sheets_service.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
                        existing_sheets = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
                    except Exception:
                        pass
                else:
                    logger.warning(f"⚠️ Could not fetch spreadsheet metadata: {_he}")
            except Exception as e:
                logger.warning(f"⚠️ Could not fetch spreadsheet metadata: {e}")

            # Retrieve schema config for this sheet
            schemas = registry.get("schemas", {})
            schema_config = schemas.get(sheet_name, schemas.get("default", {}))
            headers = schema_config.get("headers", [])
            columns_def = schema_config.get("columns", [])

            # --- 🛡️ Duplicate Slip Detection by Ref Number ---
            ref_val = get_val(['ref', 'ref_number', 'เลขที่อ้างอิง', 'transaction_id'])
            if ref_val and str(ref_val).strip() != '-':
                cleaned_ref = str(ref_val).replace('-', '').replace(' ', '').replace("'", "").strip()
                if cleaned_ref and len(cleaned_ref) >= 6:
                    if sheet_name in existing_sheets:
                        try:
                            if 'existing_rows' not in locals():
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

            # --- 🛡️ Fallback Duplicate Slip Detection by Date, Net Amount, Time, and Sender/Receiver ---
            if sheet_name in existing_sheets:
                try:
                    if 'existing_rows' not in locals():
                        res_val = self.sheets_service.spreadsheets().values().get(
                            spreadsheetId=self.spreadsheet_id, 
                            range=f"'{sheet_name}'!A1:Z1000"
                        ).execute()
                        existing_rows = res_val.get('values', [])
                    
                    new_date_raw = get_val('date')
                    new_time_raw = get_val('time')
                    new_net_amt = clean_val(get_val('net_amount'))
                    new_rec_raw = get_val('receiver')
                    new_send_raw = get_val('sender')
                    
                    def clean_str_match(s):
                        if not s or s == '-': return ""
                        return str(s).replace('/', '').replace('-', '').replace(' ', '').replace(':', '').upper().strip()
                    
                    target_date = clean_str_match(new_date_raw)
                    target_time = clean_str_match(new_time_raw)[:5] if new_time_raw else ""
                    target_rec = clean_str_match(new_rec_raw)
                    target_send = clean_str_match(new_send_raw)
                    
                    if target_date and new_net_amt > 0:
                        idx_date = -1
                        idx_time = -1
                        idx_net_amt = -1
                        idx_receiver = -1
                        idx_sender = -1
                        
                        for h_idx, h in enumerate(headers):
                            h_clean = str(h).strip()
                            if "วันที่" in h_clean and "บันทึก" not in h_clean:
                                idx_date = h_idx
                            elif "เวลา" in h_clean and "บันทึก" not in h_clean:
                                idx_time = h_idx
                            elif "ผู้รับ" in h_clean or "ลูกค้า" in h_clean:
                                idx_receiver = h_idx
                            elif "ผู้ส่ง" in h_clean or "ร้านค้า" in h_clean:
                                idx_sender = h_idx
                            elif any(k in h_clean for k in ["สุทธิ", "จำนวนเงินสุทธิ", "จำนวนเงิน", "ยอดเงิน"]):
                                idx_net_amt = h_idx
                                
                        for r_idx, row_data in enumerate(existing_rows):
                            if r_idx == 0: continue
                            
                            row_date_val = ""
                            if idx_date != -1 and idx_date < len(row_data):
                                row_date_val = clean_str_match(row_data[idx_date])
                                
                            row_amt_val = 0.0
                            if idx_net_amt != -1 and idx_net_amt < len(row_data):
                                row_amt_val = clean_val(row_data[idx_net_amt])
                                
                            row_time_val = ""
                            if idx_time != -1 and idx_time < len(row_data):
                                row_time_val = clean_str_match(row_data[idx_time])[:5]
                                
                            row_rec_val = ""
                            if idx_receiver != -1 and idx_receiver < len(row_data):
                                row_rec_val = clean_str_match(row_data[idx_receiver])
                            row_send_val = ""
                            if idx_sender != -1 and idx_sender < len(row_data):
                                row_send_val = clean_str_match(row_data[idx_sender])
                                
                            date_matches = (row_date_val == target_date)
                            amt_matches = (abs(row_amt_val - new_net_amt) < 0.01)
                            
                            time_matches = True
                            if target_time and row_time_val:
                                time_matches = (row_time_val == target_time)
                                
                            name_matches = False
                            if target_rec:
                                if target_rec in row_rec_val or row_rec_val in target_rec or target_rec in row_send_val or row_send_val in target_rec:
                                    name_matches = True
                            if target_send and not name_matches:
                                if target_send in row_rec_val or row_rec_val in target_send or target_send in row_send_val or row_send_val in target_send:
                                    name_matches = True
                            if not target_rec and not target_send:
                                name_matches = True
                                
                            if date_matches and amt_matches and time_matches and name_matches:
                                logger.warning(f"⚠️ Duplicate slip detected by fallback check! Date: {new_date_raw}, Amt: {new_net_amt} at row {r_idx + 1}")
                                return {
                                    "ok": False, 
                                    "error": "duplicate", 
                                    "sheet": sheet_name, 
                                    "row": r_idx + 1, 
                                    "ref_number": ref_val or f"FALLBACK-{target_date}-{new_net_amt}",
                                    "data": row_data
                                }
                except Exception as ex:
                    logger.error(f"Failed to check fallback duplicate: {ex}")
            
            # Retrieve schema config for this sheet
            schemas = registry.get("schemas", {})
            schema_config = schemas.get(sheet_name, schemas.get("default", {}))
            
            headers = schema_config.get("headers", [])
            columns_def = schema_config.get("columns", [])

            # Custom Value Extractor based on source string
            def extract_field_value(col_def, context_ext=None, context_data=None, col_idx=None, target_sheet_name=None):
                if context_ext is None: context_ext = ext
                if context_data is None: context_data = data
                if target_sheet_name is None: target_sheet_name = sheet_name
                
                if target_sheet_name == "peak" and context_ext is not None:
                    # Check if our own company is listed as the sender/vendor
                    sender_val = str(context_ext.get('sender_name', context_ext.get('sender', ''))).strip()
                    if not sender_val or sender_val == '-':
                        sender_val = str(context_ext.get('company_name', '')).strip()
                    if any(x in sender_val for x in ["ฮาร์ทวอมมิ่ง", "ฮาร์ทกวมมิ่ง", "ฮาร์ทออมมิ่ง", "heart warming", "heartwarming", "heart moving", "heartmoving"]):
                        # Swap sender/receiver keys in a copy of context_ext so that all queries get swapped values!
                        swapped = dict(context_ext)
                        
                        # Swap names
                        swapped['sender'] = context_ext.get('receiver', context_ext.get('payee', '-'))
                        swapped['sender_name'] = context_ext.get('receiver_name', context_ext.get('payee_name', '-'))
                        swapped['receiver'] = context_ext.get('sender', '-')
                        swapped['receiver_name'] = context_ext.get('sender_name', '-')
                        
                        # Swap tax IDs
                        swapped['tax_id'] = context_ext.get('receiver_tax_id', '-')
                        if swapped['tax_id'] == '-':
                            swapped['tax_id'] = context_ext.get('receiver_id', '-')
                        
                        # Swap addresses
                        swapped['address'] = context_ext.get('receiver_address', '-')
                        swapped['sender_address'] = context_ext.get('address', '-')
                        
                        context_ext = swapped

                src = col_def.get("source", "")
                cleaner = col_def.get("cleaner", "")
                
                # Custom WHT column override: If header name contains WHT related keywords (excluding "peak" sheet which requires numeric/rate values)
                is_wht_col = False
                if col_idx is not None and target_sheet_name != "peak":
                    target_schema = schemas.get(target_sheet_name, schemas.get("default", {}))
                    target_headers = target_schema.get("headers", [])
                    if col_idx < len(target_headers):
                        h_name = target_headers[col_idx]
                        # Only override for simple "หัก ณ ที่จ่าย" status columns, NOT for Type, Amount or Rate columns
                        # ALSO: Do NOT override when the column definition expects a numeric float amount
                        if any(x in h_name for x in ["หัก ณ ที่จ่าย", "จำนวนภาษีที่หัก"]) and not any(x in h_name for x in ["ประเภท", "จำนวน", "อัตรา"]):
                            col_def_chk = target_schema.get("columns", [])[col_idx] if col_idx < len(target_schema.get("columns", [])) else {}
                            if col_def_chk.get("cleaner") != "float" and "amount" not in col_def_chk.get("source", ""):
                                is_wht_col = True
                
                if is_wht_col:
                    has_wht = False
                    
                    # Sub-helper to get values with multiple key possibilities
                    def wht_local_get_val(keys, default='-'):
                        if isinstance(keys, str): keys = [keys]
                        for k in keys:
                            v = context_ext.get(k)
                            if v is not None and str(v).strip() != '-': return v
                        return default
                    
                    if target_sheet_name == "สลิปโอนเงิน":
                        slip_wht_amt = clean_val(wht_local_get_val(['wht_amount', 'wht']))
                        memo_str = str(wht_local_get_val('memo')).upper()
                        # If slip itself has WHT
                        if (slip_wht_amt > 0) or ("EXWHT" in memo_str) or ("หัก ณ ที่จ่าย" in memo_str) or ("WHT" in memo_str):
                            has_wht = True
                        else:
                            # 3-Way check: Look up from "ใบเสร็จ/ใบกำกับภาษี" sheet
                            invoice_has_wht = False
                            if "ใบเสร็จ/ใบกำกับภาษี" in existing_sheets:
                                try:
                                    res_val = self.sheets_service.spreadsheets().values().get(
                                        spreadsheetId=self.spreadsheet_id, 
                                        range="'ใบเสร็จ/ใบกำกับภาษี'!A1:Z1000"
                                    ).execute()
                                    inv_rows = res_val.get('values', [])
                                    if inv_rows and len(inv_rows) > 1:
                                        inv_hdr = inv_rows[0]
                                        idx_amt = next((i for i, h in enumerate(inv_hdr) if "สุทธิ" in h), 9)
                                        idx_vend = next((i for i, h in enumerate(inv_hdr) if "ผู้ส่ง" in h or "ร้านค้า" in h or "คู่ค้า" in h), 3)
                                        idx_wht = next((i for i, h in enumerate(inv_hdr) if "หัก ณ ที่จ่าย" in h), 13)
                                        
                                        slip_amt = clean_val(wht_local_get_val(['net_amount', 'amount']))
                                        slip_receiver = str(wht_local_get_val(['receiver', 'to', 'payee'])).strip()
                                        
                                        for r in inv_rows[1:]:
                                            if len(r) <= max(idx_amt, idx_vend): continue
                                            try:
                                                r_amt = clean_val(r[idx_amt])
                                                r_vend = str(r[idx_vend]).strip()
                                                if abs(r_amt - slip_amt) < 5.0:
                                                    name_match = (get_name_similarity(r_vend, slip_receiver) > 0.7) or (r_vend in slip_receiver) or (slip_receiver in r_vend)
                                                    if name_match:
                                                        r_wht = str(r[idx_wht]).strip() if len(r) > idx_wht else "-"
                                                        if r_wht == "หัก ณ ที่จ่าย" or clean_val(r_wht) > 0:
                                                            invoice_has_wht = True
                                                            break
                                            except Exception as ex:
                                                logger.warning(f"Error checking invoice matching WHT: {ex}")
                                except Exception as e:
                                    logger.warning(f"Error checking invoices: {e}")
                            
                            if invoice_has_wht:
                                has_wht = True
                                
                    elif target_sheet_name == "ใบเสร็จ/ใบกำกับภาษี":
                        inv_wht_amt = clean_val(wht_local_get_val(['wht_amount', 'wht']))
                        wht_rate_val = str(wht_local_get_val(['wht_rate', 'wht_percent', 'อัตราภาษี'])).strip()
                        wht_type_val = str(wht_local_get_val(['wht_type', 'income_type'])).strip()
                        if (inv_wht_amt > 0) or (wht_rate_val not in ['-', '', '0', '0%']) or ("หัก" in wht_type_val or "WHT" in wht_type_val.upper()):
                            has_wht = True
                            
                    elif target_sheet_name == "ใบหัก ณ ที่จ่าย":
                        has_wht = True
                        
                    return "หัก ณ ที่จ่าย" if has_wht else "-"
                
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
                elif src == "batch_id":
                    val = context_data.get('batch_id', '-')
                elif src == "verification_status":
                    val = context_data.get('verification_status', '-')
                elif src == "summary":
                    val = context_data.get('summary', '-')
                elif src == "sheet_name":
                    val = target_sheet_name
                elif src == "original_filename":
                    val = context_data.get('original_filename', context_data.get('original_name', '-'))
                    if val == '-':
                        val = context_ext.get('original_filename', context_ext.get('original_name', '-'))
                    if val == '-':
                        summary_val = context_data.get('summary', '')
                        if 'Auto-upload: ' in summary_val:
                            val = summary_val.replace('Auto-upload: ', '').strip()
                elif src == "invoice_follow_up":
                    is_et = context_ext.get("is_etax")
                    if isinstance(is_et, str):
                        is_et = is_et.strip().lower() in ['true', 'yes', '1']
                    if is_et is True:
                        val = "ไม่ต้องตาม"
                    else:
                        val = "ต้องตาม"
                elif src.startswith("const:"):
                    val = src.replace("const:", "")
                elif src.startswith("ai_keys:"):
                    keys_list = src.replace("ai_keys:", "").split(",")
                    val = local_get_val(keys_list)
                elif src == "sender_name_fallback":
                    val = local_get_val(['sender', 'from', 'vendor', 'vendor_name', 'seller', 'company_name'])
                elif src == "receiver_name_fallback":
                    val = local_get_val(['receiver', 'to', 'payee', 'buyer', 'customer', 'customer_name'])
                elif src == "line_sender_name":
                    val = context_data.get('line_sender_name', '-')
                
                # --- Custom PEAK Extraction (Image 2) ---
                elif src == "peak_seq":
                    val = str(context_data.get('peak_next_seq', 1))
                elif src == "peak_doc_date":
                    doc_d = local_get_val(['date', 'doc_date', 'document_date', 'billing_date', 'invoice_date'])
                    val = parse_to_yyyymmdd(doc_d)
                elif src == "peak_invoice_date":
                    inv_d = local_get_val(['invoice_date', 'tax_date', 'billing_date', 'receipt_date', 'date'], None)
                    if not inv_d or str(inv_d).strip() in ['-', '']:
                        val = ""
                    else:
                        val = parse_to_yyyymmdd(inv_d)
                elif src == "peak_price_type":
                    vat_val = clean_val(local_get_val(['vat_amount', 'vat', 'tax_amount', 'tax']))
                    wht_check = clean_val(local_get_val(['wht_amount', 'wht']))
                    if wht_check > 0 and abs(vat_val - wht_check) < 1.0:
                        vat_val = 0
                    vat_rate_val = local_get_val(['vat_rate', 'vat_percent', 'อัตราภาษี'])
                    _vrate_str = str(vat_rate_val).strip().lower()
                    _is_wht = any(kw in _vrate_str for kw in ('หัก', 'wht', 'withhold', 'ณ ที่จ่าย'))
                    has_vat = (vat_val > 0) or (not _is_wht and _vrate_str not in ['-', '', '0', '0%', 'no', 'no vat', 'none'])
                    val = "1" if has_vat else "3"
                elif src == "peak_account_code":
                    val = local_get_val(['account_code', 'account_number', 'account_id', 'code'], "")
                    if val == '-': val = ""
                elif src == "peak_price_unit":
                    vat_val = clean_val(local_get_val(['vat_amount', 'vat', 'tax_amount', 'tax']))
                    wht_check = clean_val(local_get_val(['wht_amount', 'wht']))
                    # If tax_amount equals WHT amount, AI confused WHT with VAT — clear it
                    if wht_check > 0 and abs(vat_val - wht_check) < 1.0:
                        vat_val = 0
                    vat_rate_val = local_get_val(['vat_rate', 'vat_percent', 'อัตราภาษี'])
                    _vrate_str = str(vat_rate_val).strip().lower()
                    _is_wht = any(kw in _vrate_str for kw in ('หัก', 'wht', 'withhold', 'ณ ที่จ่าย'))
                    has_vat = (vat_val > 0) or (not _is_wht and _vrate_str not in ['-', '', '0', '0%', 'no', 'no vat', 'none'])
                    gross_val = clean_val(local_get_val(['gross_amount', 'amount_before_vat', 'before_vat']))
                    net_val = clean_val(local_get_val(['net_amount', 'total_amount', 'amount']))
                    discount_val = clean_val(local_get_val(['discount_amount', 'discount']))
                    # Sanity check: if gross looks wrong (e.g. AI put WHT amount there), ignore it
                    if has_vat and gross_val > 0 and net_val > 0 and (gross_val < net_val * 0.5 or gross_val > net_val * 1.5):
                        gross_val = 0
                    if has_vat:
                        if gross_val > 0:
                            val = gross_val - discount_val
                        else:
                            val = round(net_val / 1.07, 2)
                    else:
                        val = gross_val if gross_val > 0 else net_val
                elif src == "peak_vat_rate":
                    vat_val = clean_val(local_get_val(['vat_amount', 'vat', 'tax_amount', 'tax']))
                    wht_check = clean_val(local_get_val(['wht_amount', 'wht']))
                    # If tax_amount equals WHT amount, AI confused WHT with VAT — clear it
                    if wht_check > 0 and abs(vat_val - wht_check) < 1.0:
                        vat_val = 0
                    vat_rate_val = local_get_val(['vat_rate', 'vat_percent', 'อัตราภาษี'])
                    _vrate_str = str(vat_rate_val).strip().lower()
                    _is_wht = any(kw in _vrate_str for kw in ('หัก', 'wht', 'withhold', 'ณ ที่จ่าย'))
                    has_vat = (vat_val > 0) or (not _is_wht and _vrate_str not in ['-', '', '0', '0%', 'no', 'no vat', 'none'])
                    val = "7%" if has_vat else "NO"
                elif src == "peak_wht_rate":
                    wht_rate_val = local_get_val(['wht_rate', 'wht_percent', 'wht_percent_rate'])
                    wht_amt = clean_val(local_get_val(['wht_amount', 'wht']))
                    
                    final_rate_num = None
                    if wht_rate_val and str(wht_rate_val).strip() != '-':
                        try:
                            final_rate_num = float(str(wht_rate_val).replace('%', '').strip())
                        except Exception: pass
                    
                    # If AI missed the rate but got the amount, calculate it!
                    if (not final_rate_num or final_rate_num <= 0) and wht_amt > 0:
                        gross_amt = clean_val(local_get_val(['gross_amount', 'amount_before_vat', 'before_vat']))
                        net_amt = clean_val(local_get_val(['net_amount', 'total_amount', 'amount']))
                        base_amt = gross_amt if gross_amt > 0 else net_amt
                        if base_amt > 0:
                            computed = (wht_amt / base_amt) * 100
                            # Snap to common Thai WHT rates with 0.3% tolerance
                            for common_rate in [1.0, 1.5, 2.0, 3.0, 5.0, 10.0, 15.0]:
                                if abs(computed - common_rate) <= 0.3:
                                    final_rate_num = common_rate
                                    break
                            if not final_rate_num:
                                final_rate_num = round(computed, 1)

                    if final_rate_num and final_rate_num > 0:
                        if float(final_rate_num).is_integer():
                            val = f"{int(final_rate_num)}%"
                        else:
                            val = f"{final_rate_num}%"
                    elif wht_amt > 0:
                        val = "3%" # Fallback to most common
                    else:
                        val = "0"
                elif src == "peak_payment_channel":
                    val = local_get_val(['payment_channel', 'payment_method', 'channel'], "")
                    if val == '-': val = ""
                elif src == "peak_wht_type":
                    wht_rate_str = extract_field_value({"source": "peak_wht_rate"}, context_ext, context_data, target_sheet_name=target_sheet_name)
                    if wht_rate_str == "0":
                        val = ""  # blank = no WHT; PEAK accepts blank for column S
                    else:
                        vendor_name = str(local_get_val(['sender', 'from', 'vendor', 'vendor_name', 'seller', 'company_name'])).strip()
                        tax_id = str(local_get_val(['tax_id', 'tax_number', 'เลขผู้เสียภาษี'])).strip()
                        is_company = False
                        for word in ['บริษัท', 'บจก', 'หจก', 'จำกัด', 'CO.', 'LTD', 'CORP', 'PUBLIC', 'มหาชน', 'ห้างหุ้นส่วน']:
                            if word in vendor_name or word.upper() in vendor_name.upper():
                                is_company = True
                                break
                        cleaned_tax = re.sub(r'\D', '', tax_id)
                        if len(cleaned_tax) == 13:
                            if cleaned_tax.startswith('0'):
                                is_company = True
                        if is_company:
                            val = "53"
                        else:
                            val = "3"
                elif src == "wht_type_smart":
                    # Thai WHT rate → income type description mapping
                    _WHT_RATE_MAP = {
                        0.75: "ค่าจ้างแรงงาน",
                        1.0:  "ค่าขนส่ง",
                        1.5:  "ดอกเบี้ย",
                        2.0:  "ค่าโฆษณา",
                        3.0:  "ค่าบริการ/ค่าจ้าง",
                        5.0:  "ค่าเช่า",
                        10.0: "วิชาชีพอิสระ",
                        15.0: "เงินปันผล",
                    }
                    # Step 1: try to get rate from AI keys
                    wht_rate_raw = local_get_val(['wht_rate', 'wht_percent', 'wht_percent_rate'])
                    wht_rate_num = None
                    if wht_rate_raw and str(wht_rate_raw).strip() not in ['-', '']:
                        try:
                            wht_rate_num = float(str(wht_rate_raw).replace('%', '').strip())
                        except Exception:
                            wht_rate_num = None
                    # Step 2: if AI returned generic text or no rate, compute from amounts
                    if not wht_rate_num or wht_rate_num <= 0:
                        wht_amt = clean_val(local_get_val(['wht_amount', 'wht']))
                        gross_amt = clean_val(local_get_val(['gross_amount', 'amount_before_vat', 'before_vat']))
                        net_amt = clean_val(local_get_val(['net_amount', 'total_amount', 'amount']))
                        base_amt = gross_amt if gross_amt > 0 else net_amt
                        if wht_amt > 0 and base_amt > 0:
                            computed = round(wht_amt / base_amt * 100, 2)
                            # snap to nearest known rate within 0.3% tolerance
                            for known in sorted(_WHT_RATE_MAP.keys()):
                                if abs(computed - known) <= 0.3:
                                    wht_rate_num = known
                                    break
                            if not wht_rate_num:
                                wht_rate_num = round(computed, 2)
                        elif wht_amt > 0:
                            wht_rate_num = 3.0  # default to 3% ค่าบริการ when amount exists but no base
                    # Step 3: format output
                    if not wht_rate_num or wht_rate_num <= 0:
                        # Step 4: Final fallback to text-based type from AI
                        val = local_get_val(['income_type', 'wht_type', 'wht_type_text'], '-')
                    else:
                        income_type = _WHT_RATE_MAP.get(wht_rate_num, "")
                        rate_str = f"{int(wht_rate_num)}%" if float(wht_rate_num).is_integer() else f"{wht_rate_num}%"
                        val = f"{rate_str} {income_type}".strip() if income_type else rate_str
                
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
                            except Exception: pass

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
                            except Exception: pass

                    if l_name_th == '-' and full_name_th != '-':
                        parts = full_name_th.split(' ', 2)
                        if len(parts) >= 2:
                            l_name_th = parts[-1]
                    val = l_name_th
                
                elif src == "id_card_first_name_en":
                    full_name_en = local_get_val(['first_name_en', 'name_en', 'full_name_en'])
                    f_name_en = local_get_val('first_name_en')
                    if f_name_en == '-' and full_name_en != '-':
                        parts = full_name_en.split(' ')
                        if len(parts) >= 2:
                            f_name_en = parts[0]
                        else:
                            f_name_en = full_name_en
                    val = f_name_en
                elif src == "id_card_last_name_en":
                    full_name_en = local_get_val(['first_name_en', 'name_en', 'full_name_en'])
                    l_name_en = local_get_val(['last_name_en', 'surname_en'])
                    if l_name_en == '-' and full_name_en != '-':
                        parts = full_name_en.split(' ')
                        if len(parts) >= 2:
                            l_name_en = " ".join(parts[1:])
                    val = l_name_en
                
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
                elif cleaner == "branch":
                    val = clean_branch(val)
                    
                return val

            # Populate row(s) dynamically
            if sheet_name == "สเตตเมนต์":
                transactions = ext.get('transactions', [])
                if transactions and isinstance(transactions, list):
                    rows = []
                    for t in transactions:
                        row_vals = []
                        for col_idx, col in enumerate(columns_def):
                            row_vals.append(extract_field_value(col, context_ext=t, col_idx=col_idx))
                        rows.append(row_vals)
                else:
                    row_vals = []
                    for col_idx, col in enumerate(columns_def):
                        row_vals.append(extract_field_value(col, col_idx=col_idx))
                    rows = [row_vals]
            else:
                row_vals = []
                for col_idx, col in enumerate(columns_def):
                    row_vals.append(extract_field_value(col, col_idx=col_idx))
                rows = [row_vals]

            # Check if sheet exists and update headers if they don't match our strict format
            if sheet_name in existing_sheets:
                try:
                    res = self.sheets_service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1:Z1").execute()
                    current_headers = res.get('values', [[]])[0]
                    # Force update if headers are English, empty, or too short (missing columns)
                    if not current_headers or len(current_headers) < (len(headers) - 2) or any(x in str(current_headers) for x in ["Log Time", "Category", "Doc Date"]):
                        logger.info(f"🔄 Updating headers for {sheet_name} to match system standards...")
                        self.sheets_service.spreadsheets().values().update(spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1", valueInputOption="RAW", body={"values": [headers]}).execute()
                except Exception as e:
                    logger.warning(f"⚠️ Header check failed: {e}")
            else:
                logger.info(f"Sheet {sheet_name} does not exist. Creating new sheet and initializing headers...")
                try:
                    self._sheet_exec(lambda: self.sheets_service.spreadsheets().batchUpdate(
                        spreadsheetId=self.spreadsheet_id,
                        body={'requests': [{'addSheet': {'properties': {'title': sheet_name}}}]}
                    ))
                except Exception as ce:
                    logger.error(f"Failed to create sheet {sheet_name}: {ce}")
                try:
                    self._sheet_exec(lambda: self.sheets_service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id, range=f"'{sheet_name}'!A1",
                        valueInputOption="RAW", body={"values": [headers]}
                    ))
                except Exception as ue:
                    logger.error(f"Failed to update headers for new sheet {sheet_name}: {ue}")

            # Lock headers (freeze first row)
            try:
                self.freeze_sheet(sheet_name)
            except Exception as fe:
                logger.warning(f"⚠️ Failed to freeze headers: {fe}")

            # Append the data
            try:
                # Sanitize values to prevent Google Sheets from auto-converting phone numbers or throwing formula errors
                sanitized_rows = []
                for r in rows:
                    sanitized_row = []
                    for val in r:
                        if isinstance(val, str):
                            val_stripped = val.strip()
                            if val_stripped and val_stripped != '-':
                                # 1. Starts with formula characters (=, +, -, @)
                                if val_stripped.startswith(('=', '+', '-', '@')):
                                    sanitized_row.append(f"'{val}")
                                # 2. Starts with '0' and represents a phone/ID (excluding '0.5' etc.)
                                elif val_stripped.startswith('0') and len(val_stripped) > 1 and not val_stripped.startswith('0.'):
                                    if any(c.isdigit() for c in val_stripped):
                                        sanitized_row.append(f"'{val}")
                                    else:
                                        sanitized_row.append(val)
                                else:
                                    sanitized_row.append(val)
                            else:
                                sanitized_row.append(val)
                        else:
                            sanitized_row.append(val)
                    sanitized_rows.append(sanitized_row)
                rows = sanitized_rows

                logger.info(f"📝 Appending row to {sheet_name} (Length: {len(rows[0])}): {rows[0][:10]}...")
                result = self._sheet_exec(lambda: self.sheets_service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"'{sheet_name}'!A2",
                    valueInputOption="USER_ENTERED",
                    body={"values": rows}
                ))
                
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
                
                # If the logged sheet is "ใบเสร็จ/ใบกำกับภาษี", duplicate the record to "peak" sheet!
                if sheet_name == "ใบเสร็จ/ใบกำกับภาษี":
                    try:
                        logger.info("🔄 Duplicating record to 'peak' sheet...")
                        peak_schema = registry.get("schemas", {}).get("peak", {})
                        peak_cols = peak_schema.get("columns", [])
                        peak_headers = peak_schema.get("headers", [])
                        
                        # Determine next sequential number for PEAK import
                        peak_next_seq = 1
                        if "peak" in existing_sheets:
                            try:
                                _seq_result = self.sheets_service.spreadsheets().values().get(
                                    spreadsheetId=self.spreadsheet_id,
                                    range="'peak'!A:A"
                                ).execute()
                                _seq_vals = _seq_result.get('values', [])
                                if len(_seq_vals) > 1:
                                    try:
                                        peak_next_seq = int(str(_seq_vals[-1][0]).strip()) + 1
                                    except (ValueError, IndexError):
                                        peak_next_seq = len(_seq_vals)
                            except Exception as _seq_err:
                                logger.warning(f"Could not read peak seq: {_seq_err}")
                        data_for_peak = {**data, 'peak_next_seq': peak_next_seq} if isinstance(data, dict) else data

                        peak_row = []
                        for col_idx, col in enumerate(peak_cols):
                            peak_row.append(extract_field_value(col, context_ext=ext, context_data=data_for_peak, col_idx=col_idx, target_sheet_name="peak"))
                        
                        # Ensure "peak" sheet exists
                        if "peak" not in existing_sheets:
                            logger.info("Sheet 'peak' does not exist. Creating new sheet and initializing headers...")
                            try:
                                self.sheets_service.spreadsheets().batchUpdate(
                                    spreadsheetId=self.spreadsheet_id, 
                                    body={'requests': [{'addSheet': {'properties': {'title': 'peak'}}}]}
                                ).execute()
                                existing_sheets.append("peak")
                            except Exception as ce:
                                logger.error(f"Failed to create sheet 'peak': {ce}")
                            try:
                                self.sheets_service.spreadsheets().values().update(
                                    spreadsheetId=self.spreadsheet_id, 
                                    range="'peak'!A1", 
                                    valueInputOption="RAW", 
                                    body={"values": [peak_headers]}
                                ).execute()
                            except Exception as ue:
                                logger.error(f"Failed to update headers for new sheet 'peak': {ue}")
                        
                        # Lock headers and style them
                        try:
                            self.freeze_sheet("peak")
                        except Exception as fe:
                            logger.warning(f"⚠️ Failed to freeze/style headers for 'peak': {fe}")
                            
                        # Append to peak
                        self.sheets_service.spreadsheets().values().append(
                            spreadsheetId=self.spreadsheet_id,
                            range="'peak'!A2",
                            valueInputOption="USER_ENTERED",
                            body={"values": [peak_row]}
                        ).execute()
                        logger.info("✅ Duplicated record to 'peak' sheet successfully.")
                    except Exception as pe:
                        logger.error(f"❌ Failed to duplicate to 'peak' sheet: {pe}")
                
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
            except Exception: pass
        except Exception as e:
            logger.error(f"Logging error: {e}")
            return {"ok": False, "error": str(e)}

    @thread_safe
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
                
                # Sanitize new_value to prevent Google Sheets from auto-converting phone numbers or throwing formula errors
                if isinstance(new_value, str):
                    val_stripped = new_value.strip()
                    if val_stripped and val_stripped != '-':
                        # 1. Starts with formula characters (=, +, -, @)
                        if val_stripped.startswith(('=', '+', '-', '@')):
                            new_value = f"'{new_value}"
                        # 2. Starts with '0' and represents a phone/ID (excluding '0.5' etc.)
                        elif val_stripped.startswith('0') and len(val_stripped) > 1 and not val_stripped.startswith('0.'):
                            if any(c.isdigit() for c in val_stripped):
                                new_value = f"'{new_value}"

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

    @thread_safe
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

    def get_monthly_summary(self, return_raw=False):
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
                        except Exception:
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
                        except Exception:
                            pass

            if return_raw:
                return total_expense, total_count, categories_breakdown

            # If no data found at all
            if total_count == 0:
                return "ไม่พบข้อมูลรายการใช้จ่ายที่บันทึกไว้ใน Google Sheets ในขณะนี้ค่ะ พี่ลองบันทึกข้อมูลก่อนนะคะ"

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
                            "text": str(cat),
                            "size": "sm",
                            "color": "#475569",
                            "flex": 6
                        },
                        {
                            "type": "text",
                            "text": f"{amt_formatted} THB",
                            "size": "sm",
                            "weight": "bold",
                            "color": "#0F172A",
                            "align": "end",
                            "flex": 4
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
                    "backgroundColor": "#F0FDF9",
                    "paddingAll": "20px",
                    "paddingBottom": "16px",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "horizontal",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "vertical",
                                    "backgroundColor": "#059669",
                                    "cornerRadius": "20px",
                                    "paddingAll": "4px",
                                    "paddingStart": "10px",
                                    "paddingEnd": "10px",
                                    "contents": [
                                        {"type": "text", "text": "SUMMARY", "size": "xxs", "color": "#FFFFFF", "weight": "bold"}
                                    ]
                                },
                                {"type": "filler"}
                            ]
                        },
                        {
                            "type": "text",
                            "text": f"{total_expense_str} THB",
                            "weight": "bold",
                            "size": "xxl",
                            "color": "#0F172A",
                            "margin": "md"
                        },
                        {
                            "type": "text",
                            "text": "รายงานสรุปรายจ่ายสะสม",
                            "size": "xs",
                            "color": "#64748B",
                            "margin": "xs"
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
                            "layout": "vertical",
                            "margin": "md",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "แยกตามประเภทบัญชี/หมวดหมู่",
                                    "weight": "bold",
                                    "size": "sm",
                                    "color": "#0F172A",
                                    "margin": "none"
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
                            "paddingAll": "12px",
                            "cornerRadius": "8px",
                            "backgroundColor": "#F8FAFC",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {"type": "text", "text": "จำนวนรายการทั้งหมด", "color": "#64748B", "size": "xs", "flex": 6},
                                        {"type": "text", "text": f"{total_count} รายการ", "color": "#0F172A", "weight": "bold", "size": "xs", "flex": 4, "align": "end"}
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "margin": "sm",
                                    "contents": [
                                        {"type": "text", "text": "ยอดเฉลี่ยต่อรายการ", "color": "#64748B", "size": "xs", "flex": 6},
                                        {"type": "text", "text": f"{avg_expense_str} THB", "color": "#0F172A", "weight": "bold", "size": "xs", "flex": 4, "align": "end"}
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
                            "color": "#059669",
                            "action": {
                                "type": "uri",
                                "label": "เปิด Google Sheets",
                                "uri": sheet_url
                            }
                        }
                    ]
                }
            }
            
            return {
                "type": "flex",
                "altText": "รายงานสรุปยอดรายจ่ายของพี่ค่ะ",
                "contents": flex_bubble
            }
            
        except Exception as e:
            logger.error(f"Error compiling monthly summary: {e}")
            return f"เกิดข้อผิดพลาดในการดึงข้อมูลรายจ่าย: {e}"


google_manager = GoogleWorkspaceManager()

def get_drive_service():
    """Returns the thread-local drive_service and sheets_service from google_manager."""
    return google_manager.drive_service, google_manager.sheets_service

def rename_file(file_id, new_name): return google_manager.rename_file(file_id, new_name)
def delete_file(file_id): return google_manager.delete_file(file_id)
def list_folder_contents(folder_id=None): return google_manager.list_subfolders(folder_id)
def move_row_between_sheets(from_sheet, row_index, to_sheet): return google_manager.move_row_between_sheets(from_sheet, row_index, to_sheet)

def sync_drive_logs_from_sheets(org_id, username=None):
    """
    Synchronizes the local SQLite drive_logs table with the live records in Google Sheets
    to resolve any database drift.
    """
    logger.info(f"🔄 Starting drive_logs sync from Google Sheets for org_id={org_id}, username={username}...")
    try:
        import database
        
        # Set context
        google_manager.set_context(username, org_id)
        
        if not google_manager.sheets_service or not google_manager.spreadsheet_id:
            logger.warning(f"⚠️ Google Sheets not connected or no spreadsheet_id found for org_id={org_id}. Sync skipped.")
            return False

        def clean_float(val):
            if not val or str(val).strip() == '-':
                return 0.0
            try:
                s = str(val).replace(',', '').strip()
                is_negative = False
                if s.startswith('(') and s.endswith(')'):
                    is_negative = True
                    s = s[1:-1]
                elif s.startswith('-'):
                    is_negative = True
                    s = s[1:]
                import re
                clean_str = re.sub(r'[^\d.]', '', s)
                result = float(clean_str) if clean_str else 0.0
                return -result if is_negative else result
            except Exception:
                return 0.0

        def parse_time_to_db(time_str):
            if not time_str or str(time_str).strip() in ['-', '']:
                return None
            s = str(time_str).strip()
            # Try parsing various formats
            for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%y %H:%M", "%d/%m/%y %H:%M:%S"):
                try:
                    from datetime import datetime as dt
                    parsed = dt.strptime(s, fmt)
                    # Handle Buddhist Era years (e.g. 2569 -> 2026)
                    year = parsed.year
                    if year > 2500:
                        year -= 543
                    return f"{year:04d}-{parsed.month:02d}-{parsed.day:02d} {parsed.hour:02d}:{parsed.minute:02d}:{parsed.second:02d}"
                except Exception:
                    continue
            return None

        # Fetch spreadsheet metadata
        spreadsheet = google_manager.sheets_service.spreadsheets().get(
            spreadsheetId=google_manager.spreadsheet_id
        ).execute()
        sheet_titles = [s['properties']['title'] for s in spreadsheet.get('sheets', [])]
        
        target_sheets = ["ใบเสร็จ/ใบกำกับภาษี", "บันทึกค่าใช้จ่าย", "สลิปโอนเงิน", "ใบหัก ณ ที่จ่าย", "บัตรประชาชน", "สเตตเมนต์", "ใบเสนอราคา", "peak"]
        db_rows = []

        for s_title in target_sheets:
            if s_title not in sheet_titles:
                continue
            
            try:
                res = google_manager.sheets_service.spreadsheets().values().get(
                    spreadsheetId=google_manager.spreadsheet_id, range=f"'{s_title}'!A1:Z"
                ).execute()
                vals = res.get('values', [])
                if not vals or len(vals) <= 1:
                    continue
                
                header = vals[0]
                
                # Find column indexes dynamically
                idx_date = next((i for i, h in enumerate(header) if "วันที่" in h), -1)
                idx_amt = next((i for i, h in enumerate(header) if any(x in h for x in ["สุทธิ", "ยอดเงิน", "จำนวนเงิน", "มูลค่ารวมภาษี", "จำนวนเงินที่ชำระ"])), -1)
                idx_cat = next((i for i, h in enumerate(header) if any(x in h for x in ["หมวดหมู่", "ประเภท", "บัญชี"])), -1)
                idx_summary = next((i for i, h in enumerate(header) if any(x in h for x in ["สรุปจาก AI", "คำอธิบาย", "หมายเหตุ", "บันทึกช่วยจำ", "รายละเอียด"])), -1)
                idx_link = next((i for i, h in enumerate(header) if any(x in h for x in ["ลิงก์ไฟล์", "ลิงก์ drive", "ลิงก์"])), -1)
                idx_user = next((i for i, h in enumerate(header) if any(x in h for x in ["ผู้ส่ง", "user_id", "LINE User"])), -1)
                idx_file = next((i for i, h in enumerate(header) if any(x in h for x in ["ไฟล์ต้นฉบับ", "ไฟล์อ้างอิง", "ชื่อไฟล์", "ไฟล์"])), -1)
                idx_timestamp = next((i for i, h in enumerate(header) if "เวลาที่บันทึก" in h or "เวลาบันทึก" in h), 0)

                for row in vals[1:]:
                    if len(row) == 0:
                        continue
                    
                    # Extract date
                    doc_date = str(row[idx_date]).strip() if (idx_date != -1 and idx_date < len(row)) else "-"
                    
                    # Extract amount
                    amt = clean_float(row[idx_amt] if (idx_amt != -1 and idx_amt < len(row)) else 0.0)
                    
                    # Extract category
                    cat_val = str(row[idx_cat]).strip() if (idx_cat != -1 and idx_cat < len(row)) else s_title
                    if not cat_val or cat_val == '-': 
                        cat_val = s_title
                        
                    # Extract summary
                    summary = str(row[idx_summary]).strip() if (idx_summary != -1 and idx_summary < len(row)) else ""
                    
                    # Extract link
                    link_val = str(row[idx_link]).strip() if (idx_link != -1 and idx_link < len(row)) else ""
                    
                    # Extract user
                    user_val = str(row[idx_user]).strip() if (idx_user != -1 and idx_user < len(row)) else ""
                    
                    # Extract filename
                    file_val = str(row[idx_file]).strip() if (idx_file != -1 and idx_file < len(row)) else ""
                    if not file_val or file_val == '-':
                        # Fallback: parse from link or use a placeholder
                        file_val = f"file_{s_title}.pdf"
                        
                    # Extract timestamp
                    ts_val = str(row[idx_timestamp]).strip() if (idx_timestamp != -1 and idx_timestamp < len(row)) else ""
                    created_at = parse_time_to_db(ts_val)
                    if not created_at:
                        from datetime import datetime as dt
                        created_at = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    db_rows.append((
                        file_val,     # filename
                        cat_val,      # category
                        amt,          # amount
                        doc_date,     # doc_date
                        summary,      # summary
                        link_val,     # file_link
                        user_val,     # user_id
                        org_id,       # org_id
                        created_at    # created_at
                    ))
            except Exception as se:
                logger.error(f"❌ Error syncing sheet '{s_title}': {se}")

        # Update SQLite database
        conn = database._get_conn()
        cursor = conn.cursor()
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        try:
            # Delete old logs for this org
            cursor.execute("DELETE FROM drive_logs WHERE org_id = ?", (org_id,))
            
            # Insert synced logs
            if db_rows:
                cursor.executemany("""
                    INSERT INTO drive_logs (filename, category, amount, doc_date, summary, file_link, user_id, org_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, db_rows)
                
            cursor.execute("COMMIT")
            logger.info(f"✅ Successfully synced {len(db_rows)} logs from Google Sheets to SQLite drive_logs table.")
            return True
        except Exception as dbe:
            cursor.execute("ROLLBACK")
            logger.error(f"❌ Database Transaction Error during sync: {dbe}")
            return False
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"❌ General Error in sync_drive_logs_from_sheets: {e}", exc_info=True)
        return False

