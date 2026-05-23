#!/usr/bin/env python
"""
Test just importing app.core.config module.
"""

import sys
import time

print(f"[TEST] START @ {time.time():.3f}", flush=True)

print(f"[TEST] Adding backend-api to path", flush=True)
sys.path.insert(0, 'C:\\FIFA WC\\platform\\backend-api')

print(f"[TEST] About to import app.core.config @ {time.time():.3f}", flush=True)
from app.core.config import settings
print(f"[TEST] Import complete @ {time.time():.3f}", flush=True)
print(f"[TEST] settings.DATABASE_URL = {settings.DATABASE_URL}", flush=True)
