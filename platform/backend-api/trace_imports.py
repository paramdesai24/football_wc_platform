#!/usr/bin/env python
"""
Detailed import tracer to find the next hang point.
"""

import sys
import time

def trace(msg):
    print(f"[TRACE] {msg:<60} @ {time.time():.3f}", flush=True)

trace("START")
trace("importing: app.core.config")
from app.core.config import settings
trace("SUCCESS: config")

trace("importing: app.core.database")
from app.core.database import init_db
trace("SUCCESS: database")

trace("importing: app.core.logging")
from app.core.logging import setup_logging
trace("calling: setup_logging()")
setup_logging()
trace("SUCCESS: logging")

trace("importing: fastapi components")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
trace("SUCCESS: fastapi")

trace("importing: app.api.v1.endpoints.health")
from app.api.v1.endpoints import health
trace("SUCCESS: health endpoint")

trace("importing: app.api.v1.router")
from app.api.v1.router import api_router
trace("SUCCESS: api router")

trace("DONE - all imports successful!")
