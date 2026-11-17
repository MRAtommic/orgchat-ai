"""
Tests for In-memory Cache Pruning and Sweeping (Fix 6)
Ensures caches are capped and pruned correctly without impacting ongoing operations.
"""

import time
import threading
import pytest
from routes._memcache import prune, sweep_all_caches


def test_prune_ttl():
    now = time.time()
    cache = {
        "old_1": now - 100,
        "old_2": now - 50,
        "fresh_1": now - 10,
        "fresh_2": now,
    }
    evicted = prune(cache, ttl=30, now=now)
    assert evicted == 2
    assert "old_1" not in cache
    assert "old_2" not in cache
    assert "fresh_1" in cache
    assert "fresh_2" in cache


def test_prune_max_items():
    now = time.time()
    cache = {}
    for i in range(100):
        cache[f"k_{i}"] = now + i  # k_0 is oldest, k_99 is newest

    evicted = prune(cache, max_items=25, now=now)
    assert evicted == 75
    assert len(cache) == 25
    # The oldest (k_0 ... k_74) must have been pruned, k_75..k_99 must remain
    assert "k_0" not in cache
    assert "k_74" not in cache
    assert "k_75" in cache
    assert "k_99" in cache


def test_prune_various_formats():
    now = time.time()
    # 1. Tuple with ts first: (ts, display_name, avatar)
    profile_cache = {
        "alice": (now - 400, "Alice", "/a.png"),
        "bob": (now - 10, "Bob", "/b.png")
    }
    assert prune(profile_cache, ttl=300, now=now) == 1
    assert "alice" not in profile_cache
    assert "bob" in profile_cache

    # 2. Tuple with ts second: (data, ts)
    popped_states = {
        "state_old": ({"user": "x"}, now - 500),
        "state_new": ({"user": "y"}, now - 50)
    }
    assert prune(popped_states, ttl=300, now=now) == 1
    assert "state_old" not in popped_states
    assert "state_new" in popped_states

    # 3. Dict with ts key: {"data": ..., "ts": ...}
    dash_cache = {
        1: {"data": "d1", "ts": now - 120},
        2: {"data": "d2", "ts": now - 20}
    }
    assert prune(dash_cache, ttl=60, now=now) == 1
    assert 1 not in dash_cache
    assert 2 in dash_cache


def test_prune_thread_safety():
    cache = {}
    lock = threading.Lock()
    stop_event = threading.Event()

    def inserter():
        idx = 0
        while not stop_event.is_set() and idx < 500:
            with lock:
                cache[f"t_{idx}"] = time.time()
            idx += 1
            time.sleep(0.001)

    def pruner():
        while not stop_event.is_set():
            prune(cache, ttl=0.05, max_items=50, lock=lock)
            time.sleep(0.002)

    t1 = threading.Thread(target=inserter)
    t2 = threading.Thread(target=pruner)
    t1.start()
    t2.start()

    t1.join()
    stop_event.set()
    t2.join()

    # Must not raise and cache size must be bounded
    with lock:
        assert len(cache) <= 100


def test_sweep_all_caches_runs():
    """Verify that sweep_all_caches runs without crashing across all modules."""
    res = sweep_all_caches()
    assert isinstance(res, dict)
    assert len(res) >= 1

