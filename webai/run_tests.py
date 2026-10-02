# -*- coding: utf-8 -*-
"""
webai/run_tests.py — Automated Test Runner for OrgChat AI
Discovers and executes all unit & integration tests in webai/tests/.
"""

import sys
import os
import unittest
from pathlib import Path

# Fix Windows console encoding
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add webai to sys.path
BASE_DIR = Path(__file__).parent.absolute()
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

def run_tests():
    print("=" * 70)
    print("🧪 OrgChat AI — Automated Test Suite")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    start_dir = str(BASE_DIR / "tests")
    suite = loader.discover(start_dir=start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures : {len(result.failures)}")
    print(f"Errors   : {len(result.errors)}")
    
    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        return 0
    else:
        print("❌ SOME TESTS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())
