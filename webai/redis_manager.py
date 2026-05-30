import base64
import threading
import time

_cache: dict = {}
_cache_expiry: dict = {}
_cache_lock = threading.Lock()  # ป้องกัน race condition บน in-memory cache


class RedisManager:
    @staticmethod
    def set_json(key, value, expire=None):
        _cache[key] = value
        if expire:
            _cache_expiry[key] = time.monotonic() + expire
        else:
            _cache_expiry.pop(key, None)

    @staticmethod
    def get_json(key, default=None):
        exp = _cache_expiry.get(key)
        if exp is not None and time.monotonic() > exp:
            _cache.pop(key, None)
            _cache_expiry.pop(key, None)
            return default
        return _cache.get(key, default)

    @staticmethod
    def delete(key):
        _cache.pop(key, None)
        _cache_expiry.pop(key, None)

    @staticmethod
    def set_active_edit_session(user_id, data):
        _cache[f"edit_session:{user_id}"] = data

    @staticmethod
    def get_active_edit_session(user_id):
        return _cache.get(f"edit_session:{user_id}")

    @staticmethod
    def clear_active_edit_session(user_id):
        _cache.pop(f"edit_session:{user_id}", None)

    @staticmethod
    def set_pending_files(user_id, files_list):
        encoded = []
        for f in files_list:
            f_copy = f.copy()
            if isinstance(f_copy.get("content"), bytes):
                f_copy["content"] = base64.b64encode(f_copy["content"]).decode("utf-8")
            encoded.append(f_copy)
        _cache[f"pending_files:{user_id}"] = encoded

    @staticmethod
    def pop_pending_files(user_id):
        encoded = _cache.pop(f"pending_files:{user_id}", [])
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

    @staticmethod
    def try_claim_upload(pending_id: str) -> bool:
        """
        Atomic check-and-lock สำหรับ upload slot
        - คืน True ถ้า claim สำเร็จ (ยังไม่มีใครจอง + มีไฟล์รออยู่)
        - คืน False ถ้ามีคนจองไปแล้ว หรือไม่มีไฟล์เหลือ
        ใช้ threading.Lock เพื่อป้องกันการกดซ้ำพร้อมกัน
        """
        lock_key    = f"upload_lock:{pending_id}"
        pending_key = f"pending_files:{pending_id}"
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
        with _cache_lock:
            _cache.pop(lock_key, None)
            _cache_expiry.pop(lock_key, None)
