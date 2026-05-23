#!/usr/bin/env python
"""
TEST 1: SQLAlchemy import in isolation - no app code, no config.
Proves whether SQLAlchemy itself hangs on import.
"""

import sys
import time

print(f"[SQLALCHEMY-ONLY] START @ {time.time():.3f}", flush=True)

print(f"[SQLALCHEMY-ONLY] importing: sqlalchemy", flush=True)
start = time.time()
from sqlalchemy import create_engine
elapsed = time.time() - start
print(f"[SQLALCHEMY-ONLY] SUCCESS: create_engine imported @ {time.time():.3f} (took {elapsed:.3f}s)", flush=True)

print(f"[SQLALCHEMY-ONLY] importing: sqlalchemy.orm", flush=True)
start = time.time()
from sqlalchemy.orm import sessionmaker, DeclarativeBase
elapsed = time.time() - start
print(f"[SQLALCHEMY-ONLY] SUCCESS: sessionmaker, DeclarativeBase imported @ {time.time():.3f} (took {elapsed:.3f}s)", flush=True)

print(f"[SQLALCHEMY-ONLY] defining: Base = DeclarativeBase()", flush=True)
start = time.time()
class Base(DeclarativeBase):
    pass
elapsed = time.time() - start
print(f"[SQLALCHEMY-ONLY] SUCCESS: Base class created @ {time.time():.3f} (took {elapsed:.3f}s)", flush=True)

print(f"[SQLALCHEMY-ONLY] creating: create_engine with SQLite", flush=True)
start = time.time()
db_url = "sqlite:///test.db"
engine = create_engine(db_url, echo=False)
elapsed = time.time() - start
print(f"[SQLALCHEMY-ONLY] SUCCESS: engine created @ {time.time():.3f} (took {elapsed:.3f}s)", flush=True)

print(f"[SQLALCHEMY-ONLY] creating: SessionLocal", flush=True)
start = time.time()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
elapsed = time.time() - start
print(f"[SQLALCHEMY-ONLY] SUCCESS: SessionLocal created @ {time.time():.3f} (took {elapsed:.3f}s)", flush=True)

print("\n✅ SQLALCHEMY TEST COMPLETE - NO HANG")
