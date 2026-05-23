#!/usr/bin/env python
"""
TEST 2: Import SQLAlchemy submodules one at a time.
Identify which specific import hangs.
"""

import sys
import time

def test_import(module_name):
    print(f"[TEST2] Attempting: {module_name}", flush=True)
    start = time.time()
    try:
        __import__(module_name)
        elapsed = time.time() - start
        print(f"[TEST2] SUCCESS {module_name} @ {elapsed:.3f}s", flush=True)
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"[TEST2] FAILED {module_name}: {e} @ {elapsed:.3f}s", flush=True)
        return False

print(f"[TEST2] START @ {time.time():.3f}", flush=True)

# Test individual imports
test_import("sqlalchemy.sql")
test_import("sqlalchemy.pool")
test_import("sqlalchemy.dialects")
test_import("sqlalchemy.ext")

print(f"[TEST2] COMPLETE", flush=True)
