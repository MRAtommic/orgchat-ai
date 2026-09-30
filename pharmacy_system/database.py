"""
Pharmacy Database Layer (SQLite)
Manages drug master, dispensing logs, categories, and audit trail.
"""

import sqlite3
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from config import Config

BANGKOK_TZ = ZoneInfo("Asia/Bangkok")

def get_now_str():
    return datetime.now(BANGKOK_TZ).strftime("%Y-%m-%d %H:%M:%S")

def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    with conn:
        # Table: Drugs (Master Inventory)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                generic_name TEXT,
                category TEXT DEFAULT 'ทั่วไป',
                dosage_form TEXT DEFAULT 'เม็ด (Tablet)',
                strength TEXT DEFAULT '',
                stock_qty INTEGER NOT NULL DEFAULT 0,
                unit TEXT DEFAULT 'เม็ด',
                min_threshold INTEGER DEFAULT 10,
                price REAL DEFAULT 0.0,
                cost REAL DEFAULT 0.0,
                expiry_date TEXT,
                location TEXT DEFAULT 'ตู้เก็บยาหลัก',
                qr_payload TEXT,
                instructions TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        # Table: Dispensing Logs (Stock deductions)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dispensing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id INTEGER,
                drug_code TEXT,
                drug_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                balance_before INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                channel TEXT DEFAULT 'WEB_MANUAL',
                dispensed_by TEXT DEFAULT 'เภสัชกร/เจ้าหน้าที่',
                patient_name TEXT,
                drive_file_id TEXT,
                drive_file_link TEXT,
                notes TEXT,
                synced_to_sheet INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (drug_id) REFERENCES drugs (id) ON DELETE SET NULL
            )
        """)

        # Table: Categories
        conn.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                color TEXT DEFAULT 'teal'
            )
        """)

        # Table: System Settings (e.g. Google Drive/Sheet configuration)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT
            )
        """)

        # Indexes for fast search
        conn.execute("CREATE INDEX IF NOT EXISTS idx_drugs_name ON drugs(name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_drugs_code ON drugs(code)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_created ON dispensing_logs(created_at)")
    conn.close()

# ─────────────────────────────────────────────────────────────
# Settings Management
# ─────────────────────────────────────────────────────────────

def get_setting(key, default=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_db()
    now = get_now_str()
    with conn:
        conn.execute("""
            INSERT INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
        """, (key, str(value), now))
    conn.close()

def get_all_settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in rows}

# ─────────────────────────────────────────────────────────────
# Drug CRUD Operations
# ─────────────────────────────────────────────────────────────

def get_all_drugs(search_query=None, category=None, low_stock_only=False):
    """Fetch drugs with optional search filter."""
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM drugs WHERE 1=1"
    params = []

    if search_query:
        query += " AND (name LIKE ? OR code LIKE ? OR generic_name LIKE ?)"
        q = f"%{search_query.strip()}%"
        params.extend([q, q, q])

    if category and category != "all":
        query += " AND category = ?"
        params.append(category)

    if low_stock_only:
        query += " AND stock_qty <= min_threshold"

    query += " ORDER BY name ASC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_drug_by_id(drug_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drugs WHERE id = ?", (drug_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_drug_by_code(code):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM drugs WHERE UPPER(code) = UPPER(?)", (code.strip(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Common Thai medical aliases & abbreviations mapping
THAI_DRUG_ALIASES = {
    "พารา": "paracetamol",
    "พาราเซตามอล": "paracetamol",
    "พาราเซต": "paracetamol",
    "อะม็อกซี่": "amoxicillin",
    "อาม็อกซี่": "amoxicillin",
    "แอมม็อก": "amoxicillin",
    "ไอบู": "ibuprofen",
    "ไอบูโพรเฟน": "ibuprofen",
    "โอมีพราโซล": "omeprazole",
    "ยาลดกรด": "antacid",
    "แอนตาซิล": "antacid",
    "เซทิริซีน": "cetirizine",
    "เซทริซีน": "cetirizine",
    "แนค": "nac",
    "แนคลอง": "nac",
    "วิตซี": "vitamin c",
    "วิตามินซี": "vitamin c",
    "อ็อกเมนติน": "augmentin",
    "ออคเมนติน": "augmentin",
    "น้ำเกลือ": "saline",
}

def find_drug_by_name_or_alias(query_str):
    """
    Find best matching drug by name, code, or alias (case-insensitive & fuzzy substring).
    Useful for LINE text commands like 'พารา 2' or 'Amox 1'.
    """
    if not query_str:
        return None
    raw_q = query_str.strip().lower()
    
    # Check Thai alias mapping
    q = THAI_DRUG_ALIASES.get(raw_q, raw_q)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Exact match on code, name, or generic_name
    cursor.execute("SELECT * FROM drugs WHERE LOWER(code) = ? OR LOWER(name) = ? OR LOWER(generic_name) = ?", (q, q, q))
    row = cursor.fetchone()
    if row:
        conn.close()
        return dict(row)

    # 2. Starts with query
    cursor.execute("SELECT * FROM drugs WHERE LOWER(name) LIKE ? OR LOWER(generic_name) LIKE ?", (f"{q}%", f"{q}%"))
    row = cursor.fetchone()
    if row:
        conn.close()
        return dict(row)

    # 3. Substring match
    cursor.execute("SELECT * FROM drugs WHERE LOWER(name) LIKE ? OR LOWER(generic_name) LIKE ? OR LOWER(code) LIKE ? OR LOWER(instructions) LIKE ?", (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"))
    rows = cursor.fetchall()
    conn.close()
    
    if rows:
        # Return shortest matching name (most relevant)
        sorted_rows = sorted(rows, key=lambda r: len(r["name"]))
        return dict(sorted_rows[0])
    
    return None

def add_drug(data):
    """Insert a new drug into inventory."""
    conn = get_db()
    now = get_now_str()
    code = (data.get("code") or "").strip()
    if not code:
        # Generate automatic code
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM drugs")
        count = cursor.fetchone()[0] + 1
        code = f"MED-{count:04d}"

    qr_payload = data.get("qr_payload") or f"PHARM:{code}"

    with conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO drugs (
                code, name, generic_name, category, dosage_form, strength,
                stock_qty, unit, min_threshold, price, cost, expiry_date,
                location, qr_payload, instructions, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            code,
            data.get("name", "").strip(),
            data.get("generic_name", "").strip(),
            data.get("category", "ทั่วไป"),
            data.get("dosage_form", "เม็ด (Tablet)"),
            data.get("strength", "").strip(),
            int(data.get("stock_qty") or 0),
            data.get("unit", "เม็ด").strip(),
            int(data.get("min_threshold") or 10),
            float(data.get("price") or 0.0),
            float(data.get("cost") or 0.0),
            data.get("expiry_date", ""),
            data.get("location", "ตู้เก็บยาหลัก"),
            qr_payload,
            data.get("instructions", ""),
            now,
            now
        ))
        drug_id = cursor.lastrowid
    conn.close()
    return get_drug_by_id(drug_id)

def update_drug(drug_id, data):
    """Update existing drug details."""
    conn = get_db()
    now = get_now_str()
    with conn:
        conn.execute("""
            UPDATE drugs SET
                name = COALESCE(?, name),
                generic_name = COALESCE(?, generic_name),
                category = COALESCE(?, category),
                dosage_form = COALESCE(?, dosage_form),
                strength = COALESCE(?, strength),
                stock_qty = COALESCE(?, stock_qty),
                unit = COALESCE(?, unit),
                min_threshold = COALESCE(?, min_threshold),
                price = COALESCE(?, price),
                cost = COALESCE(?, cost),
                expiry_date = COALESCE(?, expiry_date),
                location = COALESCE(?, location),
                instructions = COALESCE(?, instructions),
                updated_at = ?
            WHERE id = ?
        """, (
            data.get("name"),
            data.get("generic_name"),
            data.get("category"),
            data.get("dosage_form"),
            data.get("strength"),
            data.get("stock_qty"),
            data.get("unit"),
            data.get("min_threshold"),
            data.get("price"),
            data.get("cost"),
            data.get("expiry_date"),
            data.get("location"),
            data.get("instructions"),
            now,
            drug_id
        ))
    conn.close()
    return get_drug_by_id(drug_id)

def delete_drug(drug_id):
    """Delete drug from inventory."""
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM drugs WHERE id = ?", (drug_id,))
    conn.close()
    return True

# ─────────────────────────────────────────────────────────────
# Stock Dispensing & Deduction Flow (Atomic Transaction)
# ─────────────────────────────────────────────────────────────

def deduct_stock(drug_id_or_code, quantity, channel="WEB_MANUAL", dispensed_by="เจ้าหน้าที่", patient_name="", drive_file_id=None, drive_file_link=None, notes=""):
    """
    Atomically deduct stock from a drug and insert a dispensing log.
    Returns: (success: bool, result_dict or error_message)
    """
    if quantity <= 0:
        return False, "จำนวนที่ตัดต้องมากกว่า 0"

    conn = get_db()
    cursor = conn.cursor()
    now = get_now_str()

    try:
        with conn:
            # 1. Fetch drug with lock
            if isinstance(drug_id_or_code, int) or (isinstance(drug_id_or_code, str) and drug_id_or_code.isdigit()):
                cursor.execute("SELECT * FROM drugs WHERE id = ?", (int(drug_id_or_code),))
            else:
                cursor.execute("SELECT * FROM drugs WHERE UPPER(code) = UPPER(?) OR LOWER(name) = LOWER(?)", (str(drug_id_or_code).strip(), str(drug_id_or_code).strip()))

            row = cursor.fetchone()
            if not row:
                return False, f"ไม่พบข้อมูลยา: {drug_id_or_code}"

            drug = dict(row)
            current_stock = drug["stock_qty"]

            if current_stock < quantity:
                return False, f"สต็อกไม่เพียงพอ! มียา '{drug['name']}' เหลืออยู่เพียง {current_stock} {drug['unit']} (ต้องการตัด {quantity} {drug['unit']})"

            new_stock = current_stock - quantity

            # 2. Update stock
            cursor.execute("UPDATE drugs SET stock_qty = ?, updated_at = ? WHERE id = ?", (new_stock, now, drug["id"]))

            # 3. Insert dispensing log
            cursor.execute("""
                INSERT INTO dispensing_logs (
                    drug_id, drug_code, drug_name, quantity,
                    balance_before, balance_after, channel,
                    dispensed_by, patient_name, drive_file_id,
                    drive_file_link, notes, synced_to_sheet, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                drug["id"],
                drug["code"],
                drug["name"],
                quantity,
                current_stock,
                new_stock,
                channel,
                dispensed_by,
                patient_name,
                drive_file_id,
                drive_file_link,
                notes,
                now
            ))
            log_id = cursor.lastrowid

            result = {
                "log_id": log_id,
                "drug_id": drug["id"],
                "drug_code": drug["code"],
                "drug_name": drug["name"],
                "quantity": quantity,
                "unit": drug["unit"],
                "balance_before": current_stock,
                "balance_after": new_stock,
                "min_threshold": drug["min_threshold"],
                "is_low_stock": new_stock <= drug["min_threshold"],
                "channel": channel,
                "dispensed_by": dispensed_by,
                "created_at": now,
                "drive_file_link": drive_file_link
            }
            return True, result
    except Exception as e:
        return False, f"เกิดข้อผิดพลาดในการตัดสต็อก: {str(e)}"
    finally:
        conn.close()

# ─────────────────────────────────────────────────────────────
# Dispensing Logs & Analytics
# ─────────────────────────────────────────────────────────────

def get_dispensing_logs(limit=100, drug_id=None, date_filter=None, channel_filter=None):
    """Retrieve dispensing history with filters."""
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM dispensing_logs WHERE 1=1"
    params = []

    if drug_id:
        query += " AND drug_id = ?"
        params.append(drug_id)

    if date_filter:
        query += " AND created_at LIKE ?"
        params.append(f"{date_filter}%")

    if channel_filter and channel_filter != "all":
        query += " AND channel = ?"
        params.append(channel_filter)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_dashboard_stats():
    """Summary metrics for the clinical dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM drugs")
    total_drugs = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(stock_qty) FROM drugs")
    total_units = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM drugs WHERE stock_qty <= min_threshold")
    low_stock_count = cursor.fetchone()[0]

    # Today's dispensing count
    today_str = datetime.now(BANGKOK_TZ).strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*), SUM(quantity) FROM dispensing_logs WHERE created_at LIKE ?", (f"{today_str}%",))
    disp_count_row = cursor.fetchone()
    today_dispense_count = disp_count_row[0] or 0
    today_units_dispensed = disp_count_row[1] or 0

    # Expiring soon (within 90 days)
    # Basic check against YYYY-MM-DD
    cursor.execute("SELECT COUNT(*) FROM drugs WHERE expiry_date IS NOT NULL AND expiry_date != '' AND expiry_date <= date('now', '+90 days')")
    expiring_soon_count = cursor.fetchone()[0]

    conn.close()
    return {
        "total_drugs": total_drugs,
        "total_units": total_units,
        "low_stock_count": low_stock_count,
        "today_dispense_count": today_dispense_count,
        "today_units_dispensed": today_units_dispensed,
        "expiring_soon_count": expiring_soon_count
    }

# Initialize on module import
init_db()
