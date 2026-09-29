# -*- coding: utf-8 -*-
"""
offline_storage.py — Zero Data Loss Offline-First Storage & Cloud Sync Queue
=============================================================================
Manages local backup storage of uploaded receipts/slips, and provides
resilient queueing & syncing to Google Drive and Google Sheets.
"""

import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

DATA_ROOT = os.environ.get("DATA_DIR", ".")
BACKUP_BASE_DIR = os.path.join(DATA_ROOT, "uploads", "receipts_backup")


def save_local_receipt_backup(content: bytes, original_filename: str) -> tuple[str, str, str]:
    """
    Saves file bytes locally into uploads/receipts_backup/YYYY/MM/<unique_filename>.
    
    Returns:
        (rel_path, abs_path, web_url)
        where:
        - rel_path: e.g. "2026/09/uuid_receipt.jpg" (for URL / database)
        - abs_path: absolute file system path
        - web_url: "/uploads/receipts_backup/2026/09/uuid_receipt.jpg"
    """
    now = datetime.now()
    year_str = now.strftime("%Y")
    month_str = now.strftime("%m")
    
    target_dir = os.path.join(BACKUP_BASE_DIR, year_str, month_str)
    os.makedirs(target_dir, exist_ok=True)
    
    # Clean filename
    clean_name = secure_filename(os.path.basename(original_filename or "receipt"))
    if not clean_name:
        clean_name = "file.bin"
        
    unique_prefix = uuid.uuid4().hex[:12]
    saved_filename = f"{unique_prefix}_{clean_name}"
    
    abs_path = os.path.join(target_dir, saved_filename)
    with open(abs_path, "wb") as f:
        f.write(content)
        
    rel_path = f"{year_str}/{month_str}/{saved_filename}"
    web_url = f"/uploads/receipts_backup/{rel_path}"
    
    logger.info(f"💾 [OfflineStorage] Saved local backup: {abs_path} (size={len(content)} bytes)")
    return rel_path, abs_path, web_url


def sync_single_offline_upload(item: dict) -> tuple[bool, str]:
    """
    Attempts to sync a single queued offline upload to Google Drive and Google Sheets.
    
    Args:
        item: dictionary row from offline_upload_queue
        
    Returns:
        (success: bool, message: str)
    """
    import database
    from google_drive_service import google_manager
    
    upload_id = item.get("id")
    local_filepath = item.get("local_filepath")
    org_id = item.get("org_id") or 1
    username = item.get("username")
    original_filename = item.get("original_filename") or "receipt"
    mimetype = item.get("mimetype") or "image/jpeg"
    folder_id = item.get("folder_id")
    folder_name = item.get("folder_name") or "ทั่วไป"
    analysis = item.get("analysis") or {}
    extracted_data = item.get("extracted_data") or {}
    verification_status = item.get("verification_status") or "-"
    line_sender_name = item.get("line_sender_name")
    
    if not local_filepath or not os.path.exists(local_filepath):
        err = f"Local file not found: {local_filepath}"
        database.update_offline_upload_status(upload_id, "failed", error_message=err)
        return False, err
        
    try:
        with open(local_filepath, "rb") as f:
            content = f.read()
            
        google_manager.set_context(username=username, org_id=org_id)
        
        # 1. Upload to Google Drive
        drive_link, upload_err = google_manager.upload_file(
            content, original_filename, mimetype,
            folder_id=folder_id, org_id=org_id, username=username
        )
        
        if not drive_link:
            err = f"Drive upload failed: {upload_err}"
            database.update_offline_upload_status(upload_id, "failed", error_message=err)
            return False, err
            
        # 2. Log to Google Sheets
        log_data = {
            "file_link": drive_link,
            "summary": analysis.get("summary", f"Synced: {original_filename}") if analysis else f"Synced: {original_filename}",
            "original_filename": original_filename,
            "extracted_data": extracted_data,
            "line_sender_name": line_sender_name,
            "verification_status": verification_status
        }
        log_res = google_manager.log_expense(log_data, org_id=org_id, username=username)
        sheets_row = log_res.get("row") if log_res else None
        
        # 3. Mark as synced in database
        database.update_offline_upload_status(
            upload_id=upload_id,
            sync_status="synced",
            drive_link=drive_link,
            sheets_row=sheets_row
        )
        logger.info(f"✅ [OfflineStorage] Successfully synced item #{upload_id} to Drive & Sheets ({drive_link})")
        return True, "Synced successfully"
        
    except Exception as e:
        logger.error(f"❌ [OfflineStorage] Error syncing item #{upload_id}: {e}")
        database.update_offline_upload_status(upload_id, "failed", error_message=str(e))
        return False, str(e)


def sync_all_pending_offline_uploads(limit: int = 20) -> dict:
    """
    Syncs pending offline uploads up to limit.
    
    Returns:
        dict: {"synced": int, "failed": int, "total_processed": int, "errors": list}
    """
    import database
    pending_items = database.get_pending_offline_uploads(limit=limit)
    synced_count = 0
    failed_count = 0
    errors = []
    
    for item in pending_items:
        success, msg = sync_single_offline_upload(item)
        if success:
            synced_count += 1
        else:
            failed_count += 1
            errors.append({"id": item.get("id"), "error": msg})
            
    return {
        "synced": synced_count,
        "failed": failed_count,
        "total_processed": len(pending_items),
        "errors": errors
    }
