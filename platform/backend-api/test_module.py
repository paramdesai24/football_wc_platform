#!/usr/bin/env python
import sys
import time

print(f"[T1] START", flush=True)

print(f"[T2] Importing sqlalchemy", flush=True)
from sqlalchemy import create_engine, DeclarativeBase
from sqlalchemy.orm import sessionmaker

print(f"[T3] Imported sqlalchemy OK", flush=True)

print(f"[T4] Importing app.core.config", flush=True)
from app.core.config import settings

print(f"[T5] Imported config OK: {settings.PROJECT_NAME}", flush=True)

print(f"[T6] Defining module-level code", flush=True)

_engine = None
_SessionLocal = None

def _get_engine():
    global _engine
    if _engine is None:
        print(f"[T7] Inside _get_engine, about to call create_engine", flush=True)
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        print(f"[T8] create_engine returned", flush=True)
    return _engine

class Base(DeclarativeBase):
    pass

print(f"[T9] Module-level code complete", flush=True)
