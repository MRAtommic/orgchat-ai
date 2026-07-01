import hashlib
import hmac
import time
import json
import logging
import requests
from datetime import datetime, timedelta

import database

logger = logging.getLogger("OrgChatAI")

PEAK_API_BASE = "https://api.peakaccount.com"

_client_token_caches = {} # Dict of org_id -> {"token": None, "expires_at": 0}


def get_credentials(org_id: int = 1):
    return {
        "connect_id": database.get_app_setting(f"peak_connect_id_{org_id}") or database.get_app_setting("peak_connect_id") or "",
        "password": database.get_app_setting(f"peak_password_{org_id}") or database.get_app_setting("peak_password") or "",
        "user_token": database.get_app_setting(f"peak_user_token_{org_id}") or database.get_app_setting("peak_user_token") or "",
    }


def save_credentials(connect_id: str, password: str, user_token: str, org_id: int = 1):
    database.set_app_setting(f"peak_connect_id_{org_id}", connect_id.strip())
    database.set_app_setting(f"peak_password_{org_id}", password.strip())
    database.set_app_setting(f"peak_user_token_{org_id}", user_token.strip())
    if org_id in _client_token_caches:
        del _client_token_caches[org_id]


def _make_time_signature(connect_id: str) -> tuple[str, str]:
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    sig = hmac.new(connect_id.encode(), ts.encode(), hashlib.sha1).hexdigest()  # type: ignore[attr-defined]
    return ts, sig


def _get_client_token(connect_id: str, password: str, org_id: int = 1) -> str:
    now = time.time()
    cache = _client_token_caches.get(org_id)
    if cache and cache["token"] and now < cache["expires_at"]:
        return cache["token"]

    ts, sig = _make_time_signature(connect_id)
    resp = requests.post(
        f"{PEAK_API_BASE}/api/v1/ClientToken",
        json={"PeakClientToken": {"connectId": connect_id, "password": password}},
        headers={
            "Content-Type": "application/json",
            "Time-Stamp": ts,
            "Time-Signature": sig,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data.get("clientToken") or data.get("token") or data.get("data", {}).get("clientToken", "")
    if not token:
        raise ValueError(f"PEAK: ไม่พบ client token ในผลตอบกลับ: {data}")

    _client_token_caches[org_id] = {
        "token": token,
        "expires_at": now + 23 * 3600  # refresh ก่อนหมดอายุ 1 ชม.
    }
    return token


def _build_headers(connect_id: str, password: str, user_token: str, org_id: int = 1) -> dict:
    ts, sig = _make_time_signature(connect_id)
    client_token = _get_client_token(connect_id, password, org_id)
    return {
        "Content-Type": "application/json",
        "Time-Stamp": ts,
        "Time-Signature": sig,
        "User-Token": user_token,
        "Client-Token": client_token,
    }


def fetch_receipts(start_date: str = None, end_date: str = None, org_id: int = 1) -> list[dict]:
    """
    ดึงข้อมูล receipts จาก PEAK API
    start_date / end_date รูปแบบ YYYY-MM-DD (ถ้าไม่ระบุ = เดือนปัจจุบัน)
    คืนค่าเป็น list ของ dict พร้อม key ที่ reconciliation_service ต้องการ
    """
    creds = get_credentials(org_id)
    if not creds["connect_id"] or not creds["user_token"]:
        raise ValueError("ยังไม่ได้ตั้งค่า PEAK API credentials")

    if not start_date:
        start_date = datetime.today().replace(day=1).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.today().strftime("%Y-%m-%d")

    headers = _build_headers(creds["connect_id"], creds["password"], creds["user_token"], org_id)

    all_rows = []
    page = 1
    while True:
        params = {"limit": 200, "page": page}
        resp = requests.get(
            f"{PEAK_API_BASE}/api/v1/Receipts",
            headers=headers,
            params=params,
            timeout=30,
        )
        resp.raise_for_status()
        body = resp.json()

        items = (
            body.get("data")
            or body.get("items")
            or body.get("receipts")
            or (body if isinstance(body, list) else [])
        )
        if not items:
            break

        for item in items:
            row = _parse_receipt(item)
            if row:
                # กรองตามวันที่
                doc_date = row.get("_doc_date", "")
                if doc_date and (doc_date < start_date or doc_date > end_date):
                    continue
                all_rows.append(row)

        if len(items) < 200:
            break
        page += 1

    logger.info(f"[PEAK] ดึงข้อมูล {len(all_rows)} รายการ ({start_date} ถึง {end_date})")
    return all_rows


def _parse_receipt(item: dict) -> dict | None:
    """แปลง PEAK API response เป็น format ที่ reconciliation_service ใช้"""
    if not item:
        return None

    def _get(*keys):
        for k in keys:
            v = item.get(k)
            if v is not None and str(v).strip() not in ("", "None", "null"):
                return str(v).strip()
        return ""

    def _get_float(*keys):
        for k in keys:
            v = item.get(k)
            if v is not None:
                try:
                    return float(v)
                except (ValueError, TypeError):
                    pass
        return 0.0

    ref_id = _get(
        "referenceDocumentNo", "referenceNo", "refDocumentNo",
        "reference", "referenceNumber", "externalRef",
    )
    invoice_id = _get(
        "documentNo", "taxInvoiceNo", "invoiceNo",
        "receiptNo", "docNo", "number",
    )
    status = _get("status", "documentStatus", "statusName")
    amount = _get_float(
        "totalAmountIncludeVat", "totalAmount", "grandTotal",
        "netAmount", "amount",
    )
    vat = _get_float("vatAmount", "vat", "taxAmount")

    raw_date = _get(
        "issueDate", "documentDate", "createdDate", "date", "docDate",
    )
    doc_date = ""
    if raw_date:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
            try:
                doc_date = datetime.strptime(raw_date[:10], fmt[:10]).strftime("%Y-%m-%d")
                break
            except ValueError:
                continue

    if not ref_id and not invoice_id:
        return None

    return {
        "shipnity_id": ref_id,
        "peak_invoice_id": invoice_id,
        "status_peak": status,
        "amount_peak": amount,
        "tax_amount": vat,
        "_doc_date": doc_date,
    }
