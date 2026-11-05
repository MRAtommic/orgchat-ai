# -*- coding: utf-8 -*-
"""
line_inbox.py — กล่องขาเข้าถาวรของ LINE webhook

ปัญหาเดิม: webhook ตอบ 200 แล้วค่อยประมวลผลใน thread ถ้าเซิร์ฟเวอร์รีสตาร์ต/ล่มกลางคัน ข้อความนั้นหายเงียบ
และตัวกันซ้ำอยู่ในหน่วยความจำ (หายตอนรีสตาร์ต)

วิธีใหม่: บันทึกทุกเหตุการณ์ลง SQLite ก่อนตอบ 200 → ประมวลผล → ทำเครื่องหมาย done
  • ตอนเริ่มระบบ/ทุก 1 นาที: เหตุการณ์ที่ค้าง (pending/processing เกิน 90 วินาที) จะถูกประมวลผลซ้ำ
    สูงสุด MAX_ATTEMPTS ครั้ง และเฉพาะเหตุการณ์ที่ยังไม่เก่าเกิน MAX_AGE_SECONDS (กันตอบข้อความเก่ามากๆ)
  • กันซ้ำแบบถาวร (event_id เป็น primary key) แม้รีสตาร์ตระหว่างที่ LINE ส่งซ้ำ
  • ลบรายการที่เสร็จแล้วเก่ากว่า 7 วัน
"""
import hashlib
import json
import logging
import threading
import time

from db.connection import _get_conn

logger = logging.getLogger("OrgChatAI.LineInbox")

STALE_PROCESSING_SECONDS = 90
MAX_ATTEMPTS = 2
MAX_AGE_SECONDS = 600
RETAIN_DONE_DAYS = 7
_lock = threading.Lock()


def _ensure(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS line_event_inbox (
            event_id TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempts INTEGER NOT NULL DEFAULT 0,
            received_at REAL NOT NULL,
            started_at REAL,
            finished_at REAL,
            error TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_line_inbox_status ON line_event_inbox(status, received_at)")


def event_key(event: dict) -> str:
    eid = event.get("webhookEventId")
    if not eid and event.get("type") == "message":
        eid = (event.get("message") or {}).get("id")
    if not eid:
        eid = "h_" + hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:32]
    return str(eid)


def accept(event: dict) -> tuple:
    """บันทึกเหตุการณ์ลงกล่อง  คืน (event_id, is_new)  is_new=False = เคยได้รับแล้ว (ซ้ำ)"""
    eid = event_key(event)
    conn = _get_conn()
    try:
        _ensure(conn)
        cur = conn.execute("INSERT OR IGNORE INTO line_event_inbox (event_id, payload, received_at) VALUES (?,?,?)",
                           (eid, json.dumps(event, ensure_ascii=False), time.time()))
        conn.commit()
        return eid, cur.rowcount == 1
    finally:
        conn.close()


def _claim(eid: str) -> bool:
    """ขอสิทธิ์ประมวลผลแบบ atomic (กัน 2 thread ทำเหตุการณ์เดียวกัน)"""
    conn = _get_conn()
    try:
        _ensure(conn)
        now = time.time()
        cur = conn.execute(
            "UPDATE line_event_inbox SET status='processing', started_at=?, attempts=attempts+1 "
            "WHERE event_id=? AND (status='pending' OR (status='processing' AND started_at < ?)) AND attempts < ?",
            (now, eid, now - STALE_PROCESSING_SECONDS, MAX_ATTEMPTS))
        conn.commit()
        return cur.rowcount == 1
    finally:
        conn.close()


def _finish(eid: str, error: str = None):
    conn = _get_conn()
    try:
        conn.execute("UPDATE line_event_inbox SET status=?, finished_at=?, error=? WHERE event_id=?",
                     ("failed" if error else "done", time.time(), (error or "")[:300] or None, eid))
        conn.commit()
    finally:
        conn.close()


def run(eid: str, event: dict, processor) -> bool:
    """ประมวลผลเหตุการณ์หนึ่งรายการ (ถ้าได้สิทธิ์) แล้วทำเครื่องหมายผล"""
    if not _claim(eid):
        return False
    try:
        processor(event)
        _finish(eid)
    except Exception as e:  # processor ปกติจับ error เอง; ถ้าหลุดมาให้บันทึกไว้
        logger.error(f"[inbox] event {eid} failed: {e}")
        _finish(eid, repr(e))
    return True


def recover(processor, limit: int = 20) -> int:
    """ประมวลผลเหตุการณ์ที่ค้างจากการรีสตาร์ต/ล่ม  คืนจำนวนที่เริ่มทำ"""
    now = time.time()
    conn = _get_conn()
    try:
        _ensure(conn)
        rows = conn.execute(
            "SELECT event_id, payload FROM line_event_inbox "
            "WHERE ((status='pending' AND received_at < ?) OR (status='processing' AND started_at < ?)) "
            "AND attempts < ? AND received_at > ? ORDER BY received_at LIMIT ?",
            (now - 15, now - STALE_PROCESSING_SECONDS, MAX_ATTEMPTS, now - MAX_AGE_SECONDS, limit)).fetchall()
        # รายการค้างที่เก่าเกินหรือลองครบแล้ว → ปิดเป็น expired เพื่อไม่ให้วนซ้ำ
        conn.execute(
            "UPDATE line_event_inbox SET status='expired', finished_at=? "
            "WHERE status IN ('pending','processing') AND (received_at <= ? OR "
            "(attempts >= ? AND (status='pending' OR started_at < ?)))",
            (now, now - MAX_AGE_SECONDS, MAX_ATTEMPTS, now - STALE_PROCESSING_SECONDS))
        conn.execute("DELETE FROM line_event_inbox WHERE status IN ('done','expired','failed') AND finished_at < ?",
                     (now - RETAIN_DONE_DAYS * 86400,))
        conn.commit()
    finally:
        conn.close()
    started = 0
    for eid, payload in rows:
        try:
            event = json.loads(payload)
        except Exception:
            _finish(eid, "bad payload")
            continue
        logger.warning(f"[inbox] recovering unfinished LINE event {eid}")
        threading.Thread(target=run, args=(eid, event, processor), daemon=True).start()
        started += 1
    return started


def stats() -> dict:
    conn = _get_conn()
    try:
        _ensure(conn)
        return {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM line_event_inbox GROUP BY status").fetchall()}
    finally:
        conn.close()
