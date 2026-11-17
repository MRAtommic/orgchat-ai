"""
In-memory Cache Pruning and Sweeping Utility (R6 / Fix 6)
Safely prunes expired entries and caps dictionary sizes to prevent memory leaks in long-running servers.
"""

import time
import logging
import threading

logger = logging.getLogger("OrgChatAI.MemCache")


def _extract_ts(val):
    """Helper to extract timestamp from various cache storage formats."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, (tuple, list)) and len(val) > 0:
        if isinstance(val[0], (int, float)):
            return float(val[0])
        if len(val) > 1 and isinstance(val[1], (int, float)):
            return float(val[1])
    if isinstance(val, dict):
        for key in ('ts', 'timestamp', 'time', 'created_at'):
            if key in val and isinstance(val[key], (int, float)):
                return float(val[key])
    return None


def prune(d: dict, ttl: float = None, max_items: int = 1000, now: float = None,
          lock: threading.Lock = None, get_ts=None) -> int:
    """
    Thread-safely removes expired items (if ttl is given) and caps dict size to max_items.
    Evicts oldest items first when exceeding max_items.
    Returns the total number of items evicted.
    """
    if d is None or not isinstance(d, dict):
        return 0

    if now is None:
        now = time.time()

    evicted = 0

    def _do_prune():
        nonlocal evicted
        # 1. TTL-based sweep
        if ttl is not None and ttl > 0:
            stale_keys = []
            for k, v in list(d.items()):
                item_ts = get_ts(v) if get_ts else _extract_ts(v)
                if item_ts is not None and (now - item_ts) > ttl:
                    stale_keys.append(k)
            for k in stale_keys:
                if d.pop(k, None) is not None:
                    evicted += 1

        # 2. Capacity-based trim (FIFO / Oldest-first)
        if max_items is not None and max_items > 0 and len(d) > max_items:
            excess = len(d) - max_items
            # Try sorting by timestamp if available
            items_with_ts = []
            for k, v in list(d.items()):
                item_ts = get_ts(v) if get_ts else _extract_ts(v)
                items_with_ts.append((k, item_ts if item_ts is not None else 0))

            items_with_ts.sort(key=lambda x: x[1])
            keys_to_drop = [k for k, _ in items_with_ts[:excess]]
            for k in keys_to_drop:
                if d.pop(k, None) is not None:
                    evicted += 1

        return evicted

    if lock is not None:
        with lock:
            return _do_prune()
    else:
        try:
            return _do_prune()
        except RuntimeError:
            # Handle potential dict mutation by another thread during iteration
            time.sleep(0.005)
            try:
                return _do_prune()
            except Exception:
                return evicted


def sweep_all_caches() -> dict:
    """
    Sweeps stale entries across all registered in-memory module caches.
    Called periodically (e.g., every 5 minutes) by the background scheduler.
    """
    now = time.time()
    results = {}

    # 1. routes.chat
    try:
        from routes import chat
        if hasattr(chat, '_profile_cache'):
            results['chat_profile'] = prune(chat._profile_cache, ttl=300, max_items=2000, now=now)
        if hasattr(chat, '_typing_last'):
            results['chat_typing_last'] = prune(chat._typing_last, ttl=60, max_items=1000, now=now)
        if hasattr(chat, '_rtc_last_offer'):
            results['chat_rtc_offer'] = prune(chat._rtc_last_offer, ttl=300, max_items=1000, now=now)
        if hasattr(chat, '_pending_calls'):
            lock = getattr(chat, '_pending_lock', None)
            ttl = getattr(chat, '_PENDING_TTL', 45) + 30
            results['chat_pending_calls'] = prune(chat._pending_calls, ttl=ttl, max_items=500, now=now, lock=lock)
        if hasattr(chat, '_limit_warn_cache'):
            results['chat_limit_warn'] = prune(chat._limit_warn_cache, ttl=3600, max_items=1000, now=now)
        if hasattr(chat, '_kb_filenames_cache'):
            results['chat_kb_filenames'] = prune(chat._kb_filenames_cache, ttl=300, max_items=500, now=now)
    except Exception as e:
        logger.debug(f"[MemCache] chat sweep skipped: {e}")

    # 2. routes.line_webhook
    try:
        from routes import line_webhook
        if hasattr(line_webhook, '_PROCESSED_WEBHOOK_EVENTS'):
            lock = getattr(line_webhook, '_PROCESSED_WEBHOOK_LOCK', None)
            results['webhook_events'] = prune(line_webhook._PROCESSED_WEBHOOK_EVENTS, ttl=120, max_items=2000, now=now, lock=lock)
        if hasattr(line_webhook, '_limit_warn_cache'):
            results['webhook_limit_warn'] = prune(line_webhook._limit_warn_cache, ttl=300, max_items=1000, now=now)
        if hasattr(line_webhook, '_line_batch_timer'):
            # Prune stalled batch timers older than 180s
            def _get_batch_ts(v):
                if isinstance(v, dict) and 'files' in v and v['files']:
                    first_file = v['files'][0]
                    return first_file.get('ts') if isinstance(first_file, dict) else None
                return None
            results['webhook_batch_timer'] = prune(line_webhook._line_batch_timer, ttl=180, max_items=500, now=now, get_ts=_get_batch_ts)
    except Exception as e:
        logger.debug(f"[MemCache] line_webhook sweep skipped: {e}")

    # 3. routes.auth
    try:
        from routes import auth
        if hasattr(auth, '_RECENT_LINE_CALLBACK_CACHE'):
            results['auth_line_callback'] = prune(auth._RECENT_LINE_CALLBACK_CACHE, ttl=300, max_items=1000, now=now)
        if hasattr(auth, '_qr_tokens'):
            results['auth_qr_tokens'] = prune(auth._qr_tokens, ttl=300, max_items=200, now=now)
    except Exception as e:
        logger.debug(f"[MemCache] auth sweep skipped: {e}")

    # 4. routes.shared
    try:
        from routes import shared
        if hasattr(shared, '_RECENT_POPPED_STATES'):
            results['shared_popped_states'] = prune(shared._RECENT_POPPED_STATES, ttl=300, max_items=1000, now=now)
    except Exception as e:
        logger.debug(f"[MemCache] shared sweep skipped: {e}")

    # 5. routes.admin
    try:
        from routes import admin
        if hasattr(admin, '_DASHBOARD_CACHE'):
            lock = getattr(admin, '_DASHBOARD_CACHE_LOCK', None)
            results['admin_dashboard'] = prune(admin._DASHBOARD_CACHE, ttl=60, max_items=500, now=now, lock=lock)
        if hasattr(admin, '_recon_cache'):
            lock = getattr(admin, '_recon_lock', None)
            results['admin_recon'] = prune(admin._recon_cache, ttl=600, max_items=20, now=now, lock=lock)
    except Exception as e:
        logger.debug(f"[MemCache] admin sweep skipped: {e}")

    # 6. routes.social
    try:
        from routes import social
        if hasattr(social, '_MAPS_SEARCH_CACHE'):
            results['social_maps_search'] = prune(social._MAPS_SEARCH_CACHE, ttl=3600, max_items=1000, now=now)
        if hasattr(social, '_MAPS_REVERSE_CACHE'):
            results['social_maps_reverse'] = prune(social._MAPS_REVERSE_CACHE, ttl=3600, max_items=1000, now=now)
    except Exception as e:
        logger.debug(f"[MemCache] social sweep skipped: {e}")

    # 7. db.org_security
    try:
        from db import org_security
        if hasattr(org_security, '_CACHE'):
            results['org_security'] = prune(org_security._CACHE, ttl=60, max_items=500, now=now)
    except Exception as e:
        logger.debug(f"[MemCache] org_security sweep skipped: {e}")

    return results

