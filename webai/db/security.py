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


def log_audit_event(username: str, org_id: int, action: str, details: str = "", ip_address: str = ""):
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_logs (username, organization_id, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        """, (username or 'System', org_id or 1, action, details or '', ip_address or ''))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"⚠️ Error logging audit event: {e}")

# Old duplicate get_audit_logs removed - consolidated definition at bottom of file



def log_audit_event(username: str, event_type: str, action_detail: str = "", ip_address: str = "", user_agent: str = "", ai_model: str = "", tokens_used: int = 0, status: str = "success", org_id: int = 1, department: str = None) -> bool:
    """Logs security, authentication, AI usage, and admin audit events."""
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        
        # If department is not supplied, fetch from user_profiles
        if not department and username:
            try:
                cursor.execute("SELECT department FROM user_profiles WHERE username = ? COLLATE NOCASE", (username.strip(),))
                row = cursor.fetchone()
                if row and row[0]:
                    department = row[0]
            except Exception as e:
                logger.debug(f"[log_audit_event] Failed fetching user department: {e}")
            
        if not department:
            department = "General"
            
        cursor.execute("""
            INSERT INTO audit_logs (org_id, username, event_type, action_detail, ip_address, user_agent, ai_model, tokens_used, department, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (org_id, username or "Anonymous", event_type, action_detail, ip_address, user_agent, ai_model, tokens_used, department, status))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[log_audit_event] Error: {e}")
        return False


class AuditLogList(list):
    """List subclass that also supports dictionary-style access for total and logs."""
    def __init__(self, items, total=None):
        super().__init__(items)
        self.total = len(items) if total is None else total
        self.logs = list(items)

    def __getitem__(self, item):
        if item == "total":
            return self.total
        elif item == "logs":
            return self.logs
        return super().__getitem__(item)

    def get(self, key, default=None):
        if key == "total":
            return self.total
        elif key == "logs":
            return self.logs
        return default


def get_audit_logs(org_id: int = 1, limit: int = 100, offset: int = 0, event_type: str = None, username: str = None, search: str = None, action: str = None, username_filter: str = None, action_filter: str = None):
    """Fetches paginated, searchable audit log entries with HMAC verification."""
    import hmac
    import hashlib
    username = username or username_filter
    search = search or action or action_filter
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(audit_logs)")
        cols = [c[1] for c in cursor.fetchall()]
        org_col = "org_id" if "org_id" in cols else "organization_id" if "organization_id" in cols else "org_id"
        
        query = f"SELECT * FROM audit_logs WHERE {org_col} = ?"
        params = [org_id]
        
        if event_type and "event_type" in cols:
            query += " AND event_type = ?"
            params.append(event_type)
        if username and "username" in cols:
            query += " AND username LIKE ? COLLATE NOCASE"
            params.append(f"%{username.strip()}%")
        if search:
            search_conditions = []
            s = f"%{search.strip()}%"
            for candidate in ["username", "action", "action_detail", "details", "ip_address", "ai_model", "department"]:
                if candidate in cols:
                    search_conditions.append(f"{candidate} LIKE ?")
                    params.append(s)
            if search_conditions:
                query += " AND (" + " OR ".join(search_conditions) + ")"
            
        # Count total matches
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total_row = cursor.fetchone()
        total = total_row[0] if total_row else 0
        
        order_col = "id" if "id" in cols else "timestamp"
        query += f" ORDER BY {order_col} DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        
        secret_salt = os.environ.get("SECRET_KEY", "orgchat_secret_audit_salt")
        for row_dict in rows:
            oid = row_dict.get("org_id") or row_dict.get("organization_id") or 1
            uname = row_dict.get("username") or ""
            act = row_dict.get("action") or row_dict.get("event_type") or ""
            det = row_dict.get("details") or row_dict.get("action_detail") or ""
            ip = row_dict.get("ip_address") or ""
            sig = row_dict.get("hash_signature")
            payload = f"{oid}:{uname}:{act}:{det}:{ip}"
            expected_sig = hmac.new(secret_salt.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
            row_dict["is_verified"] = (sig == expected_sig) if sig else True
        
        return AuditLogList(rows, total=total)
    except Exception as e:
        logging.getLogger("OrgChatAI").error(f"[get_audit_logs error] {e}")
        return AuditLogList([], total=0)
    finally:
        conn.close()


def get_security_audit_metrics(org_id: int = 1, days: int = 30) -> dict:
    """Calculates security, login, AI usage, and department statistics for IT Security Audit Dashboard."""
    from datetime import datetime, timedelta
    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
    
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        cursor = conn.cursor()
        
        # 1. High-level totals
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN event_type IN ('login_success', 'login_failed', 'account_lockout') THEN 1 END) as total_logins,
                COUNT(CASE WHEN event_type = 'login_success' THEN 1 END) as successful_logins,
                COUNT(CASE WHEN event_type = 'login_failed' THEN 1 END) as failed_logins,
                COUNT(CASE WHEN event_type = 'account_lockout' THEN 1 END) as lockout_incidents,
                COUNT(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN 1 END) as total_ai_requests,
                COALESCE(SUM(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN tokens_used ELSE 0 END), 0) as total_tokens
            FROM audit_logs
            WHERE org_id = ? AND timestamp >= ?
        """, (org_id, since_date))
        totals_row = cursor.fetchone()
        totals = dict(totals_row) if totals_row else {}
        
        # 2. Department AI Usage Breakdown
        cursor.execute("""
            SELECT department, COUNT(*) as count, COALESCE(SUM(tokens_used), 0) as tokens
            FROM audit_logs
            WHERE org_id = ? AND event_type IN ('ai_chat', 'ai_rag_query') AND timestamp >= ?
            GROUP BY department
            ORDER BY count DESC
        """, (org_id, since_date))
        dept_usage = [dict(r) for r in cursor.fetchall()]
        
        # 3. AI Model Distribution
        cursor.execute("""
            SELECT COALESCE(NULLIF(ai_model, ''), 'Gemini-3.6-Flash') as model, COUNT(*) as count
            FROM audit_logs
            WHERE org_id = ? AND event_type IN ('ai_chat', 'ai_rag_query') AND timestamp >= ?
            GROUP BY model
            ORDER BY count DESC
        """, (org_id, since_date))
        model_dist = [dict(r) for r in cursor.fetchall()]
        
        # 4. Daily Timeline (past 14 days)
        timeline_since = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d 00:00:00")
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date_str,
                COUNT(CASE WHEN event_type = 'login_success' THEN 1 END) as logins,
                COUNT(CASE WHEN event_type = 'login_failed' THEN 1 END) as failed_logins,
                COUNT(CASE WHEN event_type IN ('ai_chat', 'ai_rag_query') THEN 1 END) as ai_requests
            FROM audit_logs
            WHERE org_id = ? AND timestamp >= ?
            GROUP BY date_str
            ORDER BY date_str ASC
        """, (org_id, timeline_since))
        timeline = [dict(r) for r in cursor.fetchall()]
        
        # 5. Top IP Addresses
        cursor.execute("""
            SELECT ip_address, COUNT(*) as activity_count, username, MAX(timestamp) as last_seen
            FROM audit_logs
            WHERE org_id = ? AND ip_address IS NOT NULL AND ip_address != '' AND timestamp >= ?
            GROUP BY ip_address
            ORDER BY activity_count DESC
            LIMIT 10
        """, (org_id, since_date))
        ip_dist = [dict(r) for r in cursor.fetchall()]

        return {
            "totals": totals,
            "department_usage": dept_usage,
            "model_distribution": model_dist,
            "timeline": timeline,
            "ip_distribution": ip_dist
        }
    finally:
        conn.close()




# ═══════════════════════════════════════════════════════════════
# 🛡️ Infosec & Cryptographic Integrity Helpers (Chapter 1 & 4)
# ═══════════════════════════════════════════════════════════════

def compute_sha256_file(filepath: str) -> str:
    """Compute SHA-256 hash of a file for File Integrity Monitoring (FIM)."""
    import hashlib
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def register_file_integrity(filepath: str, category: str = "uploads") -> bool:
    """Store baseline SHA-256 hash of a file for FIM detection."""
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        return False
    
    sha = compute_sha256_file(str(p))
    if not sha:
        return False
        
    size = p.stat().st_size
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO file_integrity_records (file_path, file_name, sha256_hash, file_size, category, last_checked)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_path) DO UPDATE SET
                sha256_hash = excluded.sha256_hash,
                file_size = excluded.file_size,
                last_checked = CURRENT_TIMESTAMP
        """, (str(p), p.name, sha, size, category))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to register FIM for {filepath}: {e}")
        return False
    finally:
        conn.close()


def verify_file_integrity(filepath: str) -> tuple[bool, str]:
    """Verify if a file has been modified/tampered with against its baseline hash."""
    p = Path(filepath)
    if not p.exists() or not p.is_file():
        return False, "File does not exist on disk"
        
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT sha256_hash FROM file_integrity_records WHERE file_path = ?", (str(p),))
        row = cur.fetchone()
        if not row:
            # Register new baseline if never seen
            register_file_integrity(str(p))
            return True, "Baseline created"
            
        expected_hash = row[0]
        current_hash = compute_sha256_file(str(p))
        if current_hash == expected_hash:
            cur.execute("UPDATE file_integrity_records SET last_checked = CURRENT_TIMESTAMP WHERE file_path = ?", (str(p),))
            conn.commit()
            return True, "Integrity verified (OK)"
        else:
            logger.warning(f"🚨 [FIM ALERT] File {p.name} TAMPERED! Expected={expected_hash} Got={current_hash}")
            return False, f"Tampered! Expected {expected_hash[:8]}... got {current_hash[:8]}..."
    finally:
        conn.close()


def log_audit_event(username: str = "System", action: str = "GENERAL", details: str = "", ip_address: str = "", org_id: int = 1, **kwargs) -> bool:
    """
    Log an audit event with HMAC-SHA256 signature for tamper-evident accounting.
    Supports flexible positional arguments and legacy kwargs (event_type, action_detail, etc.).
    """
    import hmac
    import hashlib

    # Handle legacy positional ordering: log_audit_event(user, org_id, action, details, ip)
    if isinstance(action, int) or (isinstance(action, str) and action.isdigit()):
        # swap org_id and action
        actual_org_id = int(action)
        actual_action = details if details else "GENERAL"
        actual_details = ip_address if ip_address else ""
        actual_ip = kwargs.get("ip_address", "127.0.0.1")
        action = actual_action
        details = actual_details
        ip_address = actual_ip
        org_id = actual_org_id

    # Handle legacy kwargs
    if "event_type" in kwargs and (not action or action == "GENERAL"):
        action = kwargs.get("event_type", "GENERAL")
    if "action_detail" in kwargs and not details:
        details = kwargs.get("action_detail", "")
    if "org_id" in kwargs:
        try:
            org_id = int(kwargs.get("org_id", 1))
        except (ValueError, TypeError):
            org_id = 1
    
    secret_salt = os.environ.get("SECRET_KEY", "orgchat_secret_audit_salt")
    payload = f"{org_id}:{username}:{action}:{details}:{ip_address}"
    sig = hmac.new(secret_salt.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO audit_logs (org_id, username, action, details, ip_address, hash_signature)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (org_id, username or 'System', action, details, ip_address, sig))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to insert audit log: {e}")
        return False
    finally:
        conn.close()





# ═══════════════════════════════════════════════════════════════
# 🛑 Anti-Prompt Injection & Jailbreak Guardrail (Chapter 2)
# ═══════════════════════════════════════════════════════════════

_INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)disregard\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules)",
    r"(?i)system\s+prompt",
    r"(?i)you\s+are\s+now\s+(DAN|unrestricted|jailbroken|an\s+evil|a\s+hacker)",
    r"(?i)reveal\s+(your\s+)?(instructions|secret|internal\s+prompt|api\s*key)",
    r"(?i)show\s+me\s+your\s+(initial\s+)?(system\s+)?instructions",
    r"(?i)bypass\s+(content\s+filter|safety\s+filter|guardrail)",
    r"(?i)print\s+the\s+system\s+message",
    r"(?i)\bjailbreak\b",
    r"(?i)(tell|show|output|leak|share|print|repeat)\s+(me\s+)?(your\s+)?(hidden|secret|internal)?\s*(system\s*prompt|prompt|instructions|api\s*key)",
    r"(?i)pretend\s+you\s+(are|have)\s+no\s+(rules|limits|restrictions|filters)",
    r"(?i)act\s+as\s+(an?\s+)?(unfiltered|unrestricted|evil)",
    r"(?i)ลืมคำสั่ง(ก่อนหน้า|ทั้งหมด|เดิม)",
    r"(?i)แสดง\s*(system\s*prompt|คำสั่งระบบ|ความลับของระบบ|api\s*key)",
    r"(?i)ปลดล็อกกฎเกณฑ์ทั้งหมด",
    r"(?i)ขอดู\s*(system\s*prompt|คำสั่งระบบ|คำสั่งเบื้องหลัง|api\s*key)",
    r"(?i)บอก\s*(system\s*prompt|คำสั่งตั้งต้น|ความลับระบบ|api\s*key)",
    r"(?i)(แกล้งทำเป็นว่า|สมมติว่า)\s*(ไม่มีกฎ|ไม่มีข้อห้าม|ปลดล็อก)",
]


def detect_prompt_injection(text: str) -> tuple[bool, str]:
    """Detect prompt injection and jailbreak attempts in user query."""
    if not text:
        return False, ""
    import re
    for pattern in _INJECTION_PATTERNS:
        match = re.search(pattern, text)
        if match:
            matched_phrase = match.group(0)
            logger.warning(f"🚨 [PROMPT INJECTION DETECTED] Triggered by: '{matched_phrase}' in text: '{text[:80]}...'")
            return True, matched_phrase
    return False, ""


def get_security_health_status(org_id: int = 1) -> dict:
    """Generate a real-time security health score and defense metrics report."""
    import datetime as _dt_mod
    import time as _time_mod
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # 1. Total audit logs and integrity score
        logs = get_audit_logs(org_id=org_id, limit=100)
        total_logs = len(logs)
        verified_logs = sum(1 for l in logs if l.get('is_verified'))
        log_integrity_pct = int((verified_logs / total_logs) * 100) if total_logs > 0 else 100

        # 2. File Integrity Monitoring (FIM) stats
        cur.execute("SELECT COUNT(*), COUNT(CASE WHEN datetime(last_checked) >= datetime('now', '-24 hours') THEN 1 END) FROM file_integrity_records")
        fim_row = cur.fetchone()
        total_tracked_files = fim_row[0] if fim_row else 0
        recent_scanned_files = fim_row[1] if fim_row else 0

        # 3. Failed login attempts in last 24h
        cur.execute("SELECT COUNT(*) FROM login_attempts WHERE success = 0 AND ts >= ?", (int(_time_mod.time()) - 86400,))
        failed_attempts_24h = cur.fetchone()[0]

        # 4. MFA / 2FA Adoption Stats
        cur.execute("SELECT COUNT(*), COUNT(CASE WHEN totp_enabled = 1 THEN 1 END) FROM user_settings")
        user_row = cur.fetchone()
        total_users = user_row[0] if user_row else 1
        mfa_users = user_row[1] if user_row else 0
        mfa_pct = int((mfa_users / total_users) * 100) if total_users > 0 else 0

        # 5. Calculate overall security score (0 - 100)
        score = 100
        if log_integrity_pct < 100:
            score -= (100 - log_integrity_pct)
        if failed_attempts_24h > 10:
            score = max(50, score - 15)

        return {
            "overall_health_score": score,
            "status": "EXCELLENT" if score >= 90 else "GOOD" if score >= 75 else "ATTENTION_REQUIRED",
            "log_integrity_percent": log_integrity_pct,
            "total_audit_logs": total_logs,
            "verified_audit_logs": verified_logs,
            "fim_tracked_files": total_tracked_files,
            "fim_recent_scans": recent_scanned_files,
            "failed_logins_24h": failed_attempts_24h,
            "mfa_enabled_users": mfa_users,
            "total_users": total_users,
            "mfa_adoption_percent": mfa_pct,
            "timestamp": _dt_mod.datetime.now().isoformat()
        }
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# 🛑 Automated IP Blacklist & Threat Defense Guard (Enterprise)
# ═══════════════════════════════════════════════════════════════

def is_ip_blacklisted(ip_address: str) -> tuple[bool, str]:
    """Check if an IP address is currently blocked in the blacklist."""
    if not ip_address or ip_address in ("127.0.0.1", "localhost", "::1"):
        return False, ""
    
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT reason, blocked_until FROM ip_blacklist 
            WHERE ip_address = ? AND (blocked_until IS NULL OR datetime(blocked_until) > datetime('now'))
        """, (ip_address,))
        row = cur.fetchone()
        if row:
            return True, row[0] or "Threat defense security lockout"
        return False, ""
    finally:
        conn.close()


def block_ip(ip_address: str, reason: str = "Automated threat lockout", duration_minutes: int = 60):
    """Add or increment violation for an IP address and lock it out."""
    if not ip_address or ip_address in ("127.0.0.1", "localhost", "::1"):
        return

    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO ip_blacklist (ip_address, reason, blocked_until, violation_count, created_at)
            VALUES (?, ?, datetime('now', '+' || ? || ' minutes'), 1, datetime('now'))
            ON CONFLICT(ip_address) DO UPDATE SET
                reason = excluded.reason,
                blocked_until = datetime('now', '+' || ? || ' minutes'),
                violation_count = ip_blacklist.violation_count + 1
        """, (ip_address, reason, duration_minutes, duration_minutes))
        conn.commit()
    finally:
        conn.close()


def unblock_ip(ip_address: str) -> bool:
    """Remove an IP address from blacklist (Admin Unban)."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM ip_blacklist WHERE ip_address = ?", (ip_address,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def get_blacklisted_ips() -> list[dict]:
    """Retrieve all actively blocked IPs with violation history."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ip_address, reason, blocked_until, violation_count, created_at
            FROM ip_blacklist
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        return [
            {
                "ip_address": r[0],
                "reason": r[1],
                "blocked_until": r[2],
                "violation_count": r[3],
                "created_at": r[4]
            }
            for r in rows
        ]
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════
# 🛡️ Automated PII Data Masking & Anonymizer Guard (PDPA Compliance)
# ═══════════════════════════════════════════════════════════════

# Pre-compiled Regex patterns for Sensitive PII data
_THAI_NATIONAL_ID_PATTERN = re.compile(r'\b[1-9]\d{12}\b|\b[1-9]\s?\d{4}\s?\d{5}\s?\d{2}\s?\d\b|\b[1-9]-\d{4}-\d{5}-\d{2}-\d\b')
_CREDIT_CARD_PATTERN = re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|6(?:011|5[0-9][0-9])[0-9]{12}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|(?:2131|1800|35\d{3})\d{11})\b|\b(?:\d{4}[-\s]){3}\d{4}\b')
_THAI_PHONE_PATTERN = re.compile(r'\b(?:0[689]\d{8}|0[2-57]\d{7})\b|\b(?:0[689]\d{1}-\d{3}-\d{4}|0[689]\d{2}-\d{3}-\d{3}|0[2-57]-\d{3}-\d{4})\b')
_EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')


def mask_pii_data(text: str) -> tuple[str, list[dict]]:
    """
    Scans and anonymizes sensitive Personally Identifiable Information (PII)
    in compliance with Thailand's PDPA and GDPR.
    
    Returns:
      (masked_text, detected_pii_items)
    """
    if not text or not isinstance(text, str):
        return text, []

    detected_items = []
    masked = text

    # 1. Thai National ID (13 digits)
    def _mask_national_id(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) == 13:
            detected_items.append({"type": "THAI_NATIONAL_ID", "original": raw})
            return f"[ID: {clean[:1]}-XXXX-XXXXX-XX-{clean[-1:]}]"
        return raw
    masked = _THAI_NATIONAL_ID_PATTERN.sub(_mask_national_id, masked)

    # 2. Credit Card Numbers (15-16 digits)
    def _mask_credit_card(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) in (15, 16):
            detected_items.append({"type": "CREDIT_CARD", "original": raw})
            return f"[CARD: ****-****-****-{clean[-4:]}]"
        return raw
    masked = _CREDIT_CARD_PATTERN.sub(_mask_credit_card, masked)

    # 3. Thai Phone Numbers (9-10 digits)
    def _mask_phone(match):
        raw = match.group(0)
        clean = re.sub(r'[-\s]', '', raw)
        if len(clean) in (9, 10):
            detected_items.append({"type": "PHONE_NUMBER", "original": raw})
            return f"[PHONE: {clean[:3]}-***-{clean[-3:]}]"
        return raw
    masked = _THAI_PHONE_PATTERN.sub(_mask_phone, masked)

    # 4. Email Addresses
    def _mask_email(match):
        raw = match.group(0)
        parts = raw.split('@')
        if len(parts) == 2:
            uname, domain = parts
            detected_items.append({"type": "EMAIL", "original": raw})
            masked_uname = uname[:2] + "***" if len(uname) > 2 else uname[:1] + "***"
            return f"[EMAIL: {masked_uname}@{domain}]"
        return raw
    masked = _EMAIL_PATTERN.sub(_mask_email, masked)
    return masked, detected_items


# ═══════════════════════════════════════════════════════════════
# 🤖 AI Security Threat Intelligence Sentinel (UEBA & DLP Guard)
# ═══════════════════════════════════════════════════════════════

def analyze_user_threat_behavior(username: str, client_ip: str, action: str, details: str = "", org_id: int = 1) -> dict:
    """
    User & Entity Behavior Analytics (UEBA):
    Detects abnormal activity spikes, data exfiltration patterns,
    and rapid query harvesting attempts.
    """
    import time as _t_mod
    conn = _get_conn()
    cur = conn.cursor()
    try:
        now_ts = int(_t_mod.time())
        one_hour_ago = now_ts - 3600
        five_min_ago = now_ts - 300

        # 1. Query rate analysis (Burst Detection in last 5 min)
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE username = ? AND datetime(timestamp) >= datetime('now', '-5 minutes')
        """, (username,))
        burst_count = cur.fetchone()[0]

        # 2. Total security alerts triggered in last 24h
        cur.execute("""
            SELECT COUNT(*) FROM audit_logs 
            WHERE (username = ? OR ip_address = ?) 
              AND action LIKE 'SECURITY_%' 
              AND datetime(timestamp) >= datetime('now', '-24 hours')
        """, (username, client_ip))
        alert_count = cur.fetchone()[0]

        # 3. Assess Threat Level & Anomaly Flags
        threat_level = "LOW"
        risk_score = 10
        anomalies = []

        if burst_count > 30:
            threat_level = "HIGH"
            risk_score += 40
            anomalies.append(f"High-frequency request burst ({burst_count} actions in 5 min) - Possible scraping/exfiltration")
        elif burst_count > 15:
            threat_level = "MEDIUM"
            risk_score += 20
            anomalies.append(f"Moderate activity surge ({burst_count} actions in 5 min)")

        if alert_count >= 5:
            threat_level = "CRITICAL"
            risk_score += 50
            anomalies.append(f"Repeated security violations ({alert_count} alerts in 24h) - Auto containment recommended")
        elif alert_count >= 2:
            if threat_level != "CRITICAL":
                threat_level = "HIGH"
            risk_score += 25
            anomalies.append(f"Multiple security violations ({alert_count} alerts in 24h)")

        risk_score = min(100, risk_score)

        return {
            "username": username,
            "ip_address": client_ip,
            "threat_level": threat_level,
            "risk_score": risk_score,
            "burst_count_5m": burst_count,
            "security_alerts_24h": alert_count,
            "anomalies": anomalies,
            "recommended_action": "BLOCK_IP" if threat_level == "CRITICAL" else "MONITOR_CLOSELY" if threat_level == "HIGH" else "NORMAL"
        }
    finally:
        conn.close()


def get_security_threat_intel(org_id: int = 1) -> dict:
    """Aggregates enterprise-wide threat telemetry for the SOC Security Dashboard."""
    conn = _get_conn()
    cur = conn.cursor()
    try:
        # Top active threat IPs
        cur.execute("""
            SELECT ip_address, COUNT(*) as cnt 
            FROM audit_logs 
            WHERE action LIKE 'SECURITY_%' AND datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY ip_address 
            ORDER BY cnt DESC LIMIT 5
        """)
        threat_ips = [{"ip": r[0], "incidents": r[1]} for r in cur.fetchall()]

        # Top flagged actions
        cur.execute("""
            SELECT action, COUNT(*) as cnt 
            FROM audit_logs 
            WHERE action LIKE 'SECURITY_%' AND datetime(timestamp) >= datetime('now', '-24 hours')
            GROUP BY action 
            ORDER BY cnt DESC LIMIT 5
        """)
        flagged_actions = [{"action": r[0], "count": r[1]} for r in cur.fetchall()]

        return {
            "ok": True,
            "active_threat_ips": threat_ips,
            "top_flagged_actions": flagged_actions,
            "intel_engine_status": "ONLINE (Sentinel v3.4 Active)"
        }
    finally:
        conn.close()










