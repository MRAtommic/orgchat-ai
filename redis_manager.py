import base64

_cache: dict = {}


class RedisManager:
    @staticmethod
    def set_json(key, value, expire=None):
        _cache[key] = value

    @staticmethod
    def get_json(key, default=None):
        return _cache.get(key, default)

    @staticmethod
    def delete(key):
        _cache.pop(key, None)

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
