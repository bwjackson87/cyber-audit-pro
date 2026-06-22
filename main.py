"""
CyberAudit Pro — Local Cybersecurity Assessment Tool
Entry point: starts the FastAPI server and opens the browser.
"""

import logging
import os
import sys
import threading
import time
import webbrowser
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import init_db, SessionLocal
from app.services.template_manager import load_builtin_templates
from app.api import dashboard, clients, projects, assessments, findings, reports, templates_api, settings as settings_api

# When packaged as a windowless exe, stdout/stderr are None.
# Point them at devnull so any writes don't crash, and suppress all logging.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

logging.disable(logging.CRITICAL)

# Minimal uvicorn log config — no custom formatters, nothing that calls isatty.
_SILENT_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {},
    "loggers": {},
}

log = logging.getLogger("cyberaudit")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    settings.ensure_dirs()
    init_db()

    db = SessionLocal()
    try:
        load_builtin_templates(db)
    finally:
        db.close()

    if settings.OPEN_BROWSER:
        url = f"http://{settings.HOST}:{settings.PORT}"
        threading.Thread(
            target=lambda: (time.sleep(1.2), webbrowser.open(url)),
            daemon=True,
        ).start()

    yield


app = FastAPI(
    title="CyberAudit Pro",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
)

# Static files
app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

# Routers
app.include_router(dashboard.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(assessments.router)
app.include_router(findings.router)
app.include_router(reports.router)
app.include_router(templates_api.router)
app.include_router(settings_api.router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        reload=False,
        log_config=_SILENT_LOG_CONFIG,
    )
