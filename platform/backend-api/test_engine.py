#!/usr/bin/env python
import sys
import time

print(f"[TEST-001] START @ {time.time():.3f}", flush=True, file=sys.stderr)

print(f"[TEST-002] Importing sqlalchemy @ {time.time():.3f}", flush=True, file=sys.stderr)
sys.stderr.flush()
from sqlalchemy import create_engine

print(f"[TEST-003] Importing config @ {time.time():.3f}", flush=True, file=sys.stderr)
sys.stderr.flush()
from app.core.config import settings

print(f"[TEST-004] About to create_engine @ {time.time():.3f}", flush=True, file=sys.stderr)
sys.stderr.flush()
engine = create_engine(settings.DATABASE_URL, echo=False)

print(f"[TEST-005] Engine created @ {time.time():.3f}", flush=True, file=sys.stderr)
sys.stderr.flush()
