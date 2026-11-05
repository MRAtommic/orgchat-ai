"""
Redis Manager — Hybrid Cache (Real Redis / In-Memory Fallback)
==============================================================
ถ้ามี REDIS_URL → ใช้ Redis จริง (ข้อมูลอยู่รอด server restart)
ถ้าไม่มี → fallback เป็น in-memory dict (เหมือนเดิม)
"""

import base64
import json
import logging
import os
import threading
import time

logger = logging.getLogger(__name__)

# ─── In-Memory Fallback Store ────────────────────────────────
_cache: dict = {}
_cache_expiry: dict = {}
_cache_lock = threading.Lock()  # ป้องกัน race condition บน in-memory cache


def _get_redis_client():
    """สร้าง Redis client ถ้ามี REDIS_URL — return None ถ้าไม่มี/ต่อไม่ได้"""
    url = os.environ.get("REDIS_URL", "").strip()
    if not url:
        return None
    try:
        import redis
        client = redis.from_url(url, decode_responses=True, socket_connect_timeout=3)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"⚠️ Redis connection failed ({e}) — using in-memory fallback")
        return None


# Lazy singleton
_redis_client = None
_redis_checked = False


def _r():
    """Get Redis client (lazy init, singleton)"""
    global _redis_client, _redis_checked
    if not _redis_checked:
        _redis_checked = True
        _redis_client = _get_redis_client()
        if _redis_client:
            logger.info("✅ RedisManager: Connected to real Redis")
        else:
            logger.info("ℹ️ RedisManager: Using in-memory fallback (no REDIS_URL)")
    return _redis_client


class RedisManager:
    # ─────────────────────────────────────────────────────────
    # Generic JSON get/set/delete
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def set_json(key, value, expire=None):
        r = _r()
        if r:
            try:
                r.set(key, json.dumps(value, ensure_ascii=False, default=str))
                if expire:
                    r.expire(key, int(expire))
                return
            except Exception as e:
                logger.warning(f"Redis set_json error: {e}")
        # fallback
        _cache[key] = value
        if expire:
            _cache_expiry[key] = time.monotonic() + expire
        else:
            _cache_expiry.pop(key, None)

    @staticmethod
    def get_json(key, default=None):
        r = _r()
        if r:
            try:
                val = r.get(key)
                if val is None:
                    return default
                return json.loads(val)
            except Exception as e:
                logger.warning(f"Redis get_json error: {e}")
        # fallback
        exp = _cache_expiry.get(key)
        if exp is not None and time.monotonic() > exp:
            _cache.pop(key, None)
            _cache_expiry.pop(key, None)
            return default
        return _cache.get(key, default)

    @staticmethod
    def delete(key):
        r = _r()
        if r:
            try:
                r.delete(key)
                return
            except Exception as e:
                logger.warning(f"Redis delete error: {e}")
        _cache.pop(key, None)
        _cache_expiry.pop(key, None)

    # ─────────────────────────────────────────────────────────
    # Edit Session
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def set_active_edit_session(user_id, data):
        RedisManager.set_json(f"edit_session:{user_id}", data, expire=600)

    @staticmethod
    def get_active_edit_session(user_id):
        return RedisManager.get_json(f"edit_session:{user_id}")

    @staticmethod
    def clear_active_edit_session(user_id):
        RedisManager.delete(f"edit_session:{user_id}")

    # ─────────────────────────────────────────────────────────
    # Pending Files (binary safe — base64 encode content)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def set_pending_files(user_id, files_list):
        encoded = []
        for f in files_list:
            f_copy = f.copy()
            if isinstance(f_copy.get("content"), bytes):
                f_copy["content"] = base64.b64encode(f_copy["content"]).decode("utf-8")
            encoded.append(f_copy)
        RedisManager.set_json(f"pending_files:{user_id}", encoded, expire=600)

    @staticmethod
    def pop_pending_files(user_id):
        key = f"pending_files:{user_id}"
        r = _r()
        if r:
            try:
                val = r.get(key)
                r.delete(key)
                if val:
                    encoded = json.loads(val)
                else:
                    encoded = []
            except Exception as e:
                logger.warning(f"Redis pop_pending_files error: {e}")
                encoded = _cache.pop(key, [])
        else:
            encoded = _cache.pop(key, [])
            _cache_expiry.pop(key, None)

        decoded = []
        for f in encoded:
            f_copy = f.copy()
            if "content" in f_copy and isinstance(f_copy["content"], str):
                try:
                    f_copy["content"] = base64.b64decode(f_copy["content"])
                except Exception:
                    pass
            decoded.append(f_copy)
        return decoded

    # ─────────────────────────────────────────────────────────
    # Upload Lock (atomic)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def try_claim_upload(pending_id: str) -> bool:
        """
        Atomic check-and-lock สำหรับ upload slot
        - คืน True ถ้า claim สำเร็จ (ยังไม่มีใครจอง + มีไฟล์รออยู่)
        - คืน False ถ้ามีคนจองไปแล้ว หรือไม่มีไฟล์เหลือ
        """
        lock_key = f"upload_lock:{pending_id}"
        pending_key = f"pending_files:{pending_id}"
        r = _r()

        if r:
            try:
                # Redis SETNX is atomic
                acquired = r.set(lock_key, "1", nx=True, ex=120)
                if not acquired:
                    return False
                if not r.exists(pending_key):
                    r.delete(lock_key)
                    return False
                return True
            except Exception as e:
                logger.warning(f"Redis try_claim_upload error: {e}")

        # fallback — in-memory with threading.Lock
        now = time.monotonic()
        with _cache_lock:
            exp = _cache_expiry.get(lock_key)
            lock_alive = _cache.get(lock_key) and (exp is None or now <= exp)
            if lock_alive:
                return False
            if not _cache.get(pending_key):
                return False
            _cache[lock_key] = True
            _cache_expiry[lock_key] = now + 120  # lock expire 2 นาที กันค้างตลอดไป
            return True

    @staticmethod
    def release_upload_lock(pending_id: str):
        lock_key = f"upload_lock:{pending_id}"
        r = _r()
        if r:
            try:
                r.delete(lock_key)
                return
            except Exception as e:
                logger.warning(f"Redis release_upload_lock error: {e}")
        with _cache_lock:
            _cache.pop(lock_key, None)
            _cache_expiry.pop(lock_key, None)

    # ─────────────────────────────────────────────────────────
    # Distributed Lock (for cross-process synchronization)
    # ─────────────────────────────────────────────────────────
    @staticmethod
    def acquire_lock(lock_key: str, expire: int = 30, timeout: int = 15) -> bool:
        """
        Acquires a global distributed lock (Redis SETNX or fallback in-memory cache).
        Polls every 100ms until acquired or timeout.
        """
        r = _r()
        start_time = time.monotonic()
        
        while time.monotonic() - start_time < timeout:
            if r:
                try:
                    # NX=True makes it set only if key does not exist
                    if r.set(lock_key, "locked", nx=True, ex=expire):
                        return True
                except Exception as e:
                    logger.warning(f"Redis acquire_lock error: {e}")
            else:
                # In-memory lock fallback
                with _cache_lock:
                    now = time.monotonic()
                    exp = _cache_expiry.get(lock_key)
                    lock_alive = _cache.get(lock_key) and (exp is None or now <= exp)
                    if not lock_alive:
                        _cache[lock_key] = True
                        _cache_expiry[lock_key] = now + expire
                        return True
            time.sleep(0.1)
        return False

    @staticmethod
    def release_lock(lock_key: str):
        """Releases a global distributed lock."""
        r = _r()
        if r:
            try:
                r.delete(lock_key)
                return
            except Exception as e:
                logger.warning(f"Redis release_lock error: {e}")
        with _cache_lock:
            _cache.pop(lock_key, None)
            _cache_expiry.pop(lock_key, None)

