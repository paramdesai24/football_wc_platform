#!/usr/bin/env python
"""
Test if Pydantic Settings instantiation itself hangs.
"""

import sys
import time
from pathlib import Path

print(f"[TEST] START @ {time.time():.3f}", flush=True)

print(f"[TEST] Setting PROJECT_ROOT", flush=True)
PROJECT_ROOT = Path(__file__).parent.parent

print(f"[TEST] Importing pydantic_settings", flush=True)
from pydantic_settings import BaseSettings

print(f"[TEST] Defining Settings class", flush=True)

class Settings(BaseSettings):
    PROJECT_NAME: str = "FIFA WC 2026 Intelligence API"
    DATABASE_URL: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'fifa_wc_2026.db').as_posix()}"

    class Config:
        case_sensitive = True

print(f"[TEST] Settings class defined, instantiating @ {time.time():.3f}", flush=True)
settings = Settings()
print(f"[TEST] Settings instantiated successfully @ {time.time():.3f}", flush=True)
print(f"[TEST] settings.PROJECT_NAME = {settings.PROJECT_NAME}", flush=True)
