#!/usr/bin/env python
"""
Debug import tracer - identifies exact hang point during app.main import.
Run this to see which import step hangs.
"""

import sys
import time

def trace_import(step_name):
    """Print import progress with timestamp."""
    print(f"[IMPORT] {step_name:<50} @ {time.time():.3f}", flush=True)

# ─────────────────────────────────────────────────────────────
# TRACE: stdlib + fastapi
# ─────────────────────────────────────────────────────────────
trace_import("START")
trace_import("importing: fastapi")
from fastapi import FastAPI
trace_import("importing: fastapi.middleware.cors")
from fastapi.middleware.cors import CORSMiddleware
trace_import("importing: contextlib")
from contextlib import asynccontextmanager
trace_import("importing: logging, os")
import logging
import os
trace_import("SUCCESS: stdlib + fastapi imports complete")

# ─────────────────────────────────────────────────────────────
# TRACE: app.core.config
# ─────────────────────────────────────────────────────────────
trace_import("importing: app.core.config")
from app.core.config import settings
trace_import("SUCCESS: settings loaded")

# ─────────────────────────────────────────────────────────────
# TRACE: app.core.logging
# ─────────────────────────────────────────────────────────────
trace_import("importing: app.core.logging")
from app.core.logging import setup_logging
trace_import("calling: setup_logging()")
setup_logging()
trace_import("SUCCESS: logging initialized")

# ─────────────────────────────────────────────────────────────
# TRACE: app.core.database
# ─────────────────────────────────────────────────────────────
trace_import("importing: app.core.database")
from app.core.database import init_db
trace_import("SUCCESS: database module imported")

# ─────────────────────────────────────────────────────────────
# TRACE: app.api.v1.endpoints.health
# ─────────────────────────────────────────────────────────────
trace_import("importing: app.api.v1.endpoints.health")
from app.api.v1.endpoints import health
trace_import("SUCCESS: health endpoint imported")

# ─────────────────────────────────────────────────────────────
# TRACE: app.api.v1.router (THIS IMPORTS ALL ENDPOINTS)
# ─────────────────────────────────────────────────────────────
trace_import("importing: app.api.v1.router")
from app.api.v1 import router as router_module
trace_import("SUCCESS: router module imported")

# ─────────────────────────────────────────────────────────────
# TRACE: app creation
# ─────────────────────────────────────────────────────────────
trace_import("creating: FastAPI app")
api_router = router_module.api_router
trace_import("SUCCESS: app created, import complete")

print("\n✅ ALL IMPORTS SUCCESSFUL - NO HANG DETECTED")
