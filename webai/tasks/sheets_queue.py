"""
Sheets Queue — Serial Task Queue สำหรับ Google Sheets Write
============================================================
ป้องกันข้อมูลทับซ้อนเมื่อหลายคนส่งไฟล์พร้อมกัน
โดย task ในคิว sheets-write จะถูกประมวลผลทีละตัว (concurrency=1)

วิธีใช้:
    from tasks.sheets_queue import enqueue_sheet_append
    result = enqueue_sheet_append(spreadsheet_id, sheet_name, rows, org_id, username)
"""

import logging
import time

from celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.sheets_queue.sheet_append_row",
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    queue="sheets-write",
    rate_limit="10/m",  # max 10 writes/minute per worker ป้องกัน 429
)
def sheet_append_row(self, spreadsheet_id, sheet_name, rows, org_id=None, username=None):
    """
    Append rows to a Google Sheet — runs serially via Celery queue.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID
        sheet_name: ชื่อ sheet tab ที่จะ append
        rows: list of lists (row data)
        org_id: organization ID for context
        username: username for context
    
    Returns:
        dict with {ok, row_idx, updated_range} or {ok: False, error}
    """
    import re
    try:
        from google_drive_service import google_manager
        from googleapiclient.errors import HttpError

        # Set context for multi-tenant
        if org_id or username:
            google_manager.set_context(username=username, org_id=org_id)

        if not google_manager.sheets_service:
            raise Exception("sheets_service not initialized")

        # Resolve spreadsheet_id dynamically from google_manager if set context loaded it,
        # otherwise fallback to the passed spreadsheet_id.
        resolved_spreadsheet_id = google_manager.spreadsheet_id or spreadsheet_id
        logger.info(f"📝 [Queue] Appending {len(rows)} row(s) to '{sheet_name}' (spreadsheet={resolved_spreadsheet_id[:15]}...)")

        result = google_manager._sheet_exec(
            lambda: google_manager.sheets_service.spreadsheets().values().append(
                spreadsheetId=google_manager.spreadsheet_id or spreadsheet_id,
                range=f"'{sheet_name}'!A2",
                valueInputOption="USER_ENTERED",
                body={"values": rows}
            )
        )

        # Extract row index from updatedRange
        updated_range = result.get('updates', {}).get('updatedRange', '')
        row_idx = 1
        if '!' in updated_range:
            range_part = updated_range.split('!')[1]
            match = re.search(r'\d+', range_part)
            if match:
                row_idx = int(match.group())

        logger.info(f"✅ [Queue] Appended to '{sheet_name}' row {row_idx}")
        return {"ok": True, "row_idx": row_idx, "updated_range": updated_range}

    except HttpError as e:
        if e.resp.status == 429:
            logger.warning(f"⚠️ [Queue] Sheets 429 rate limit — retrying in {self.default_retry_delay}s")
            raise self.retry(exc=e)
        logger.error(f"❌ [Queue] Sheets HTTP error: {e}")
        return {"ok": False, "error": str(e)}

    except Exception as e:
        logger.error(f"❌ [Queue] Sheet append failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"ok": False, "error": str(e)}

    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except Exception:
            pass


@celery_app.task(
    name="tasks.sheets_queue.sheet_append_quotation",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
    queue="sheets-write",
)
def sheet_append_quotation(self, spreadsheet_id, tab_name, row_data, org_id=None, username=None):
    """
    Append a quotation row to Google Sheets — serial queue.
    """
    try:
        from google_drive_service import google_manager
        
        if org_id or username:
            google_manager.set_context(username=username, org_id=org_id)

        sheets_svc = google_manager.sheets_service
        if not sheets_svc or not spreadsheet_id:
            return {"ok": False, "error": "sheets not initialized"}

        # Ensure tab exists
        try:
            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
            sheet_exists = any(s['properties']['title'] == tab_name for s in spreadsheet.get('sheets', []))
        except Exception:
            sheet_exists = False

        if not sheet_exists:
            requests = [{'addSheet': {'properties': {'title': tab_name}}}]
            sheets_svc.spreadsheets().batchUpdate(
                spreadsheetId=google_manager.spreadsheet_id, body={'requests': requests}
            ).execute()
            headers = [["วันที่ทำรายการ", "เลขที่ใบเสนอราคา", "ชื่อลูกค้า/บริษัท", "ข้อมูลติดต่อ",
                        "ยอดรวมก่อนลด", "ส่วนลด", "ยอดสุทธิ (VAT 7%)", "ผู้ออกเอกสาร", "ลิงก์ไฟล์ PDF"]]
            sheets_svc.spreadsheets().values().update(
                spreadsheetId=google_manager.spreadsheet_id, range=f"'{tab_name}'!A1",
                valueInputOption="USER_ENTERED", body={"values": headers}
            ).execute()

            # Style headers
            spreadsheet = sheets_svc.spreadsheets().get(spreadsheetId=google_manager.spreadsheet_id).execute()
            sheet_id = next(
                s['properties']['sheetId'] for s in spreadsheet.get('sheets', [])
                if s['properties']['title'] == tab_name
            )
            format_req = {
                "repeatCell": {
                    "range": {"sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 1,
                              "startColumnIndex": 0, "endColumnIndex": len(headers[0])},
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": {"red": 0.1, "green": 0.4, "blue": 0.8},
                            "textFormat": {"foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                                           "bold": True, "fontSize": 11},
                            "horizontalAlignment": "CENTER"
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)"
                }
            }
            sheets_svc.spreadsheets().batchUpdate(
                spreadsheetId=google_manager.spreadsheet_id, body={"requests": [format_req]}
            ).execute()

        # Append the row
        sheets_svc.spreadsheets().values().append(
            spreadsheetId=google_manager.spreadsheet_id, range=f"'{tab_name}'!A1",
            valueInputOption="USER_ENTERED", body={"values": [row_data]}
        ).execute()

        logger.info(f"✅ [Queue] Quotation appended to '{tab_name}'")
        return {"ok": True}

    except Exception as e:
        logger.error(f"❌ [Queue] Quotation append failed: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        return {"ok": False, "error": str(e)}

    finally:
        try:
            from google_drive_service import google_manager
            google_manager.clear_context()
        except Exception:
            pass
