import sqlite3
import json
import os
import re
import random
import time
import threading
import logging
import secrets
import uuid
import hmac
import hashlib
from pathlib import Path
from datetime import datetime, date, timedelta
from functools import wraps

from .connection import *
from .connection import (
    _get_conn, _get_pg_pool, _pg_pool, _pg_pool_initialized, _pg_pool_lock,
    _db_url, _dt, _dt_mod, _j, _json, _re, _t_mod, _time_mod
)


def add_drive_log(filename, category=None, amount=None, doc_date=None, summary=None, file_link=None, user_id=None, org_id=1, sync_status="synced", local_filepath=None):
    """Log a file upload/analysis event to the database with connection safety."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drive_logs (filename, category, amount, doc_date, summary, file_link, user_id, org_id, sync_status, local_filepath)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (filename, category, amount, doc_date, summary, file_link, user_id, org_id or 1, sync_status, local_filepath))
            log_id = cursor.lastrowid
            return log_id
    except Exception as e:
        print(f"❌ Error adding drive log: {e}")
        return None

def add_offline_upload(org_id=1, username=None, user_id=None, original_filename="", local_filepath="",
                       mimetype=None, folder_id=None, folder_name=None, analysis=None,
                       extracted_data=None, verification_status="-", line_sender_name=None):
    """Register an offline or local receipt upload for subsequent cloud sync."""
    try:
        import json
        analysis_json = json.dumps(analysis, ensure_ascii=False) if analysis else None
        extracted_data_json = json.dumps(extracted_data, ensure_ascii=False) if extracted_data else None
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO offline_upload_queue (
                    org_id, username, user_id, original_filename, local_filepath,
                    mimetype, folder_id, folder_name, analysis_json, extracted_data_json,
                    verification_status, line_sender_name, sync_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (
                org_id or 1, username, user_id, original_filename, local_filepath,
                mimetype, folder_id, folder_name, analysis_json, extracted_data_json,
                verification_status, line_sender_name
            ))
            return cursor.lastrowid
    except Exception as e:
        print(f"❌ Error adding offline upload queue item: {e}")
        return None

def get_pending_offline_uploads(limit=20):
    """Retrieve pending offline uploads that need syncing to Google Drive/Sheets."""
    try:
        import json
        with _get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM offline_upload_queue
                WHERE sync_status = 'pending' OR (sync_status = 'failed' AND retry_count < 10)
                ORDER BY id ASC LIMIT ?
            """, (limit,))
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            items = []
            for row in rows:
                d = dict(zip(columns, row))
                if d.get("analysis_json"):
                    try: d["analysis"] = json.loads(d["analysis_json"])
                    except (ValueError, TypeError): d["analysis"] = None
                else:
                    d["analysis"] = None
                if d.get("extracted_data_json"):
                    try: d["extracted_data"] = json.loads(d["extracted_data_json"])
                    except (ValueError, TypeError): d["extracted_data"] = None
                else:
                    d["extracted_data"] = None
                items.append(d)
            return items
    except Exception as e:
        print(f"❌ Error retrieving pending offline uploads: {e}")
        return []

def update_offline_upload_status(upload_id: int, sync_status: str, drive_link: str = None, sheets_row: int = None, error_message: str = None):
    """Update sync status of an item in the offline upload queue, and update drive_logs if synced."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            if sync_status == 'synced':
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?, drive_link = COALESCE(?, drive_link),
                        sheets_row = COALESCE(?, sheets_row), error_message = NULL,
                        synced_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (sync_status, drive_link, sheets_row, upload_id))
                if drive_link:
                    cursor.execute("""
                        SELECT local_filepath FROM offline_upload_queue WHERE id = ?
                    """, (upload_id,))
                    lfp_row = cursor.fetchone()
                    if lfp_row and lfp_row[0]:
                        cursor.execute("""
                            UPDATE drive_logs
                            SET file_link = ?, sync_status = 'synced'
                            WHERE local_filepath = ?
                        """, (drive_link, lfp_row[0]))
            elif sync_status == 'failed':
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?, error_message = ?, retry_count = retry_count + 1
                    WHERE id = ?
                """, (sync_status, str(error_message)[:500] if error_message else None, upload_id))
            else:
                cursor.execute("""
                    UPDATE offline_upload_queue
                    SET sync_status = ?
                    WHERE id = ?
                """, (sync_status, upload_id))
            return True
    except Exception as e:
        print(f"❌ Error updating offline upload status: {e}")
        return False

def get_offline_queue_stats(org_id=None):
    """Get counts of pending, synced, and failed items in offline upload queue."""
    try:
        with _get_conn() as conn:
            cursor = conn.cursor()
            if org_id is not None:
                cursor.execute("""
                    SELECT sync_status, COUNT(*) FROM offline_upload_queue
                    WHERE org_id = ? GROUP BY sync_status
                """, (org_id,))
            else:
                cursor.execute("SELECT sync_status, COUNT(*) FROM offline_upload_queue GROUP BY sync_status")
            rows = cursor.fetchall()
            counts = {"pending": 0, "synced": 0, "failed": 0, "total": 0}
            for status, cnt in rows:
                if status in counts:
                    counts[status] = cnt
                counts["total"] += cnt
            return counts
    except Exception as e:
        print(f"❌ Error getting offline queue stats: {e}")
        return {"pending": 0, "synced": 0, "failed": 0, "total": 0}


def optimize_and_checkpoint_db():
    """Performs WAL checkpoint (TRUNCATE), PRAGMA optimize, and incremental vacuum to maintain SQLite health."""
    try:
        with _get_conn() as conn:
            # Commit pending WAL frames back to main database file and truncate WAL to 0 bytes
            res = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            res_row = res.fetchone() if res else None
            # Analyze query planner stats
            conn.execute("PRAGMA optimize")
            # Free unused pages
            try:
                conn.execute("PRAGMA incremental_vacuum(500)")
            except Exception:
                pass
            import logging
            logger = logging.getLogger("database")
            logger.info(f"🧹 [DB Maintenance] SQLite WAL Checkpoint (TRUNCATE) & Optimize completed. Status: {res_row}")
            return {"ok": True, "wal_checkpoint": list(res_row) if res_row else None}
    except Exception as e:
        import logging
        logger = logging.getLogger("database")
        logger.warning(f"⚠️ [DB Maintenance] Optimization error: {e}")
        return {"ok": False, "error": str(e)}


def get_drive_logs(limit=50, offset=0, user_id=None, org_id=None):
    """Retrieve recent drive logs filtered by org."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        where_clauses = []
        params = []
        if org_id is not None:
            where_clauses.append("org_id = ?")
            params.append(org_id)
        if user_id:
            where_clauses.append("user_id = ?")
            params.append(user_id)
        query = "SELECT * FROM drive_logs"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error fetching drive logs: {e}")
        return []

def search_drive_logs(search_query, limit=20):
    """Search drive logs by filename or summary."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        query = """
            SELECT * FROM drive_logs 
            WHERE filename LIKE ? OR summary LIKE ? OR category LIKE ?
            ORDER BY created_at DESC LIMIT ?
        """
        like_query = f"%{search_query}%"
        cursor.execute(query, (like_query, like_query, like_query, limit))
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        print(f"❌ Error searching drive logs: {e}")
        return []

def get_drive_stats(org_id=None):
    """Get statistics for the dashboard, scoped to a specific org."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        where = "WHERE org_id = ?" if org_id is not None else ""
        base_params = (org_id,) if org_id is not None else ()

        cursor.execute(f"SELECT COUNT(*) FROM drive_logs {where}", base_params)
        total_files = cursor.fetchone()[0]

        amt_where = "WHERE org_id = ? AND amount IS NOT NULL" if org_id is not None else "WHERE amount IS NOT NULL"
        amt_params = (org_id,) if org_id is not None else ()
        cursor.execute(f"SELECT SUM(amount) FROM drive_logs {amt_where}", amt_params)
        total_amount = cursor.fetchone()[0] or 0

        cat_where = "WHERE org_id = ?" if org_id is not None else ""
        cursor.execute(f"SELECT category, COUNT(*) as count FROM drive_logs {cat_where} GROUP BY category", base_params)
        categories = dict(cursor.fetchall())

        recent_where = "WHERE org_id = ? AND created_at > datetime('now', '-1 day')" if org_id is not None else "WHERE created_at > datetime('now', '-1 day')"
        cursor.execute(f"SELECT COUNT(*) FROM drive_logs {recent_where}", base_params)
        recent_count = cursor.fetchone()[0]

        conn.close()
        return {
            "total_files": total_files,
            "total_amount": total_amount,
            "categories": categories,
            "recent_count": recent_count
        }
    except Exception as e:
        print(f"❌ Error fetching drive stats: {e}")
        return {}





def get_cash_flow_projection(org_id=1):
    """
    Analyzes last 3 months of expenses and predicts next month's spending.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get last 4 months of data (including current)
    cursor.execute("""
        SELECT strftime('%Y-%m', created_at) as month, SUM(amount) as total
        FROM drive_logs
        WHERE org_id = ? AND created_at >= date('now', '-4 months')
        GROUP BY month
        ORDER BY month DESC
    """, (org_id,))
    history = cursor.fetchall()
    
    # Get top 3 expense categories
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM drive_logs
        WHERE org_id = ? AND created_at >= date('now', '-1 month')
        GROUP BY category
        ORDER BY total DESC LIMIT 3
    """, (org_id,))
    top_categories = cursor.fetchall()
    
    conn.close()
    
    totals = [r['total'] for r in history if r['total']]
    avg_projection = sum(totals) / len(totals) if totals else 0
    
    return {
        "history": [dict(r) for r in history],
        "projection": avg_projection,
        "top_categories": [dict(r) for r in top_categories]
    }



def add_expense_claim(line_user_id, username, vendor, amount, expense_date, file_link):
    conn = _get_conn()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO expense_claims (line_user_id, username, vendor, amount, expense_date, file_link)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (line_user_id, username, vendor, amount, expense_date, file_link))
    claim_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return claim_id


def search_drive_logs(query, limit=5):
    """Search for logs related to Google Drive activities."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    q = f"%{query}%"
    cursor.execute("SELECT * FROM drive_logs WHERE filename LIKE ? OR summary LIKE ? ORDER BY created_at DESC LIMIT ?", (q, q, limit))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows




def quotation_create(org_id: int, data: dict) -> int:
    conn = _get_conn()
    cur = conn.cursor()
    # auto-generate quotation number
    ym = __import__('datetime').date.today().strftime('%Y%m')
    prefix = 'INV' if data.get('type') == 'invoice' else 'QT'
    cur.execute("SELECT COUNT(*) FROM quotations WHERE org_id=? AND strftime('%Y%m', created_at)=?", (org_id, ym))
    seq = (cur.fetchone()[0] or 0) + 1
    qno = data.get('quotation_no') or f"{prefix}{ym}{seq:03d}"
    cur.execute("""
        INSERT INTO quotations (org_id, quotation_no, type, customer_name, customer_company,
            customer_address, customer_tax_id, customer_email, customer_phone,
            items, subtotal, discount, vat_rate, vat_amount, wht_rate, wht_amount, total,
            status, notes, valid_until, created_by)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (org_id, qno, data.get('type','quotation'), data.get('customer_name',''),
         data.get('customer_company',''), data.get('customer_address',''),
         data.get('customer_tax_id',''), data.get('customer_email',''), data.get('customer_phone',''),
         __import__('json').dumps(data.get('items',[])),
         data.get('subtotal',0), data.get('discount',0), data.get('vat_rate',7),
         data.get('vat_amount',0), data.get('wht_rate',0), data.get('wht_amount',0),
         data.get('total',0), data.get('status','draft'), data.get('notes',''),
         data.get('valid_until',''), data.get('created_by',''))
    )
    qid = cur.lastrowid
    conn.commit(); conn.close()
    return qid

def quotation_list(org_id: int, status: str = None, type_: str = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = "SELECT * FROM quotations WHERE org_id=?"
    params = [org_id]
    if status: q += " AND status=?"; params.append(status)
    if type_:  q += " AND type=?";   params.append(type_)
    q += " ORDER BY created_at DESC"
    rows = [dict(r) for r in cur.execute(q, params).fetchall()]
    conn.close()
    for r in rows:
        try: r['items'] = json.loads(r.get('items') or '[]')
        except (ValueError, TypeError): r['items'] = []
    return rows

def quotation_get(qid: int, org_id: int) -> dict | None:
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM quotations WHERE id=? AND org_id=?", (qid, org_id)).fetchone()
    conn.close()
    if not row: return None
    r = dict(row)
    try: r['items'] = json.loads(r.get('items') or '[]')
    except (ValueError, TypeError): r['items'] = []
    return r

def quotation_update(qid: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    items = data.get('items', [])
    cur.execute("""UPDATE quotations SET
        customer_name=?, customer_company=?, customer_address=?, customer_tax_id=?,
        customer_email=?, customer_phone=?, items=?, subtotal=?, discount=?,
        vat_rate=?, vat_amount=?, wht_rate=?, wht_amount=?, total=?,
        status=?, notes=?, valid_until=?, type=?, updated_at=CURRENT_TIMESTAMP
        WHERE id=? AND org_id=?""",
        (data.get('customer_name',''), data.get('customer_company',''),
         data.get('customer_address',''), data.get('customer_tax_id',''),
         data.get('customer_email',''), data.get('customer_phone',''),
         _json.dumps(items), data.get('subtotal',0), data.get('discount',0),
         data.get('vat_rate',7), data.get('vat_amount',0), data.get('wht_rate',0),
         data.get('wht_amount',0), data.get('total',0),
         data.get('status','draft'), data.get('notes',''), data.get('valid_until',''),
         data.get('type','quotation'), qid, org_id)
    )
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def quotation_delete(qid: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM quotations WHERE id=? AND org_id=?", (qid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def quotation_set_status(qid: int, org_id: int, status: str) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("UPDATE quotations SET status=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND org_id=?",
                (status, qid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok


# ══════════════════════════════════════════════════════════════
# CRM CRUD
# ══════════════════════════════════════════════════════════════

def crm_customer_list(org_id: int, q: str = '') -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    if q:
        rows = cur.execute("SELECT * FROM crm_customers WHERE org_id=? AND (name LIKE ? OR company LIKE ? OR email LIKE ? OR phone LIKE ?) ORDER BY name",
                           (org_id, f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()
    else:
        rows = cur.execute("SELECT * FROM crm_customers WHERE org_id=? ORDER BY name", (org_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def crm_customer_get(cid: int, org_id: int) -> dict | None:
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM crm_customers WHERE id=? AND org_id=?", (cid, org_id)).fetchone()
    conn.close()
    return dict(row) if row else None

def crm_customer_create(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO crm_customers (org_id, name, company, email, phone, address, tax_id, tags, notes, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (org_id, data.get('name',''), data.get('company',''), data.get('email',''),
                 data.get('phone',''), data.get('address',''), data.get('tax_id',''),
                 __import__('json').dumps(data.get('tags',[])), data.get('notes',''), data.get('created_by','')))
    cid = cur.lastrowid; conn.commit(); conn.close(); return cid

def crm_customer_update(cid: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE crm_customers SET name=?, company=?, email=?, phone=?, address=?, tax_id=?, tags=?, notes=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND org_id=?""",
                (data.get('name',''), data.get('company',''), data.get('email',''),
                 data.get('phone',''), data.get('address',''), data.get('tax_id',''),
                 __import__('json').dumps(data.get('tags',[])), data.get('notes',''), cid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_customer_delete(cid: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM crm_customers WHERE id=? AND org_id=?", (cid, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_deal_list(org_id: int, customer_id: int = None, stage: str = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = """SELECT d.*, c.name as customer_name, c.company as customer_company
           FROM crm_deals d LEFT JOIN crm_customers c ON d.customer_id=c.id
           WHERE d.org_id=?"""
    params = [org_id]
    if customer_id: q += " AND d.customer_id=?"; params.append(customer_id)
    if stage: q += " AND d.stage=?"; params.append(stage)
    q += " ORDER BY d.created_at DESC"
    rows = cur.execute(q, params).fetchall()
    conn.close(); return [dict(r) for r in rows]

def crm_deal_create(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""INSERT INTO crm_deals (org_id, customer_id, title, value, stage, probability, expected_close, assigned_to, notes, created_by)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (org_id, data.get('customer_id'), data.get('title',''), data.get('value',0),
                 data.get('stage','lead'), data.get('probability',50), data.get('expected_close',''),
                 data.get('assigned_to',''), data.get('notes',''), data.get('created_by','')))
    did = cur.lastrowid; conn.commit(); conn.close(); return did

def crm_deal_update(did: int, org_id: int, data: dict) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("""UPDATE crm_deals SET customer_id=?, title=?, value=?, stage=?, probability=?, expected_close=?, assigned_to=?, notes=?, updated_at=CURRENT_TIMESTAMP
                   WHERE id=? AND org_id=?""",
                (data.get('customer_id'), data.get('title',''), data.get('value',0),
                 data.get('stage','lead'), data.get('probability',50), data.get('expected_close',''),
                 data.get('assigned_to',''), data.get('notes',''), did, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_deal_delete(did: int, org_id: int) -> bool:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM crm_deals WHERE id=? AND org_id=?", (did, org_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def crm_activity_add(org_id: int, data: dict) -> int:
    conn = _get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO crm_activities (org_id, deal_id, customer_id, type, content, created_by) VALUES (?,?,?,?,?,?)",
                (org_id, data.get('deal_id'), data.get('customer_id'), data.get('type','note'),
                 data.get('content',''), data.get('created_by','')))
    aid = cur.lastrowid; conn.commit(); conn.close(); return aid

def crm_activities_get(org_id: int, deal_id: int = None, customer_id: int = None) -> list:
    conn = _get_conn(); conn.row_factory = sqlite3.Row; cur = conn.cursor()
    q = "SELECT * FROM crm_activities WHERE org_id=?"
    params = [org_id]
    if deal_id: q += " AND deal_id=?"; params.append(deal_id)
    if customer_id: q += " AND customer_id=?"; params.append(customer_id)
    q += " ORDER BY created_at DESC LIMIT 50"
    rows = cur.execute(q, params).fetchall()
    conn.close(); return [dict(r) for r in rows]




def get_custom_categories(org_id: int) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, category_name, account_code, parent_id, created_at
            FROM custom_expense_categories
            WHERE org_id = ?
            ORDER BY category_name ASC
        """, (str(org_id),))
        return [
            {
                "id": r[0],
                "category_name": r[1],
                "account_code": r[2] or "",
                "parent_id": r[3],
                "created_at": str(r[4])
            }
            for r in cursor.fetchall()
        ]
    finally:
        conn.close()

def add_custom_category(org_id: int, category_name: str, account_code: str = "", parent_id: int = None) -> int:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO custom_expense_categories (org_id, category_name, account_code, parent_id)
            VALUES (?, ?, ?, ?)
        """, (str(org_id), category_name.strip(), account_code.strip(), parent_id))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def delete_custom_category(org_id: int, category_id: int) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM custom_expense_categories WHERE id = ? AND org_id = ?", (category_id, str(org_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_ai_category_rules(org_id: int) -> list[dict]:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, keyword, category_name, rule_type, created_at
            FROM ai_category_rules
            WHERE org_id = ?
            ORDER BY id DESC
        """, (str(org_id),))
        return [
            {
                "id": r[0],
                "keyword": r[1],
                "category_name": r[2],
                "rule_type": r[3] or "contains",
                "created_at": str(r[4])
            }
            for r in cursor.fetchall()
        ]
    finally:
        conn.close()

def add_ai_category_rule(org_id: int, keyword: str, category_name: str, rule_type: str = "contains") -> int:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO ai_category_rules (org_id, keyword, category_name, rule_type)
            VALUES (?, ?, ?, ?)
        """, (str(org_id), keyword.strip().lower(), category_name.strip(), rule_type))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def delete_ai_category_rule(org_id: int, rule_id: int) -> bool:
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM ai_category_rules WHERE id = ? AND org_id = ?", (rule_id, str(org_id)))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# Account Lockout & Brute-Force Protection Functions
# ═══════════════════════════════════════════════════════════════



