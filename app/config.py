"""Application configuration — handles both normal and PyInstaller bundle execution."""

import os
import sys
from pathlib import Path


def _bundle_dir() -> Path:
    """Return the base directory for bundled read-only assets (templates, data, static)."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller bundle — assets are in the temp extraction dir
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


def _data_dir() -> Path:
    """Return a writable directory for user data (DB, exports)."""
    if getattr(sys, "frozen", False):
        # Use %APPDATA%\CyberAuditPro when running as an exe
        base = Path(os.environ.get("APPDATA", Path.home())) / "CyberAuditPro"
    else:
        base = Path(__file__).resolve().parent.parent
    return base


BUNDLE = _bundle_dir()
DATA = _data_dir()


class Settings:
    APP_NAME: str = "CyberAudit Pro"
    APP_VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8765
    OPEN_BROWSER: bool = True

    DB_PATH: Path = DATA / "data" / "db" / "cyberaudit.db"
    TEMPLATES_DIR: Path = BUNDLE / "data" / "assessment_templates"
    EXPORTS_DIR: Path = DATA / "exports"
    STATIC_DIR: Path = BUNDLE / "static"
    HTML_TEMPLATES_DIR: Path = BUNDLE / "templates"

    DEFAULT_CONSULTANT_TITLE: str = "Cybersecurity Consultant"

    DEFAULT_DISCLAIMER: str = (
        "This report represents a point-in-time assessment based on information provided "
        "during the assessment period. The findings and recommendations contained herein "
        "reflect conditions observed at the time of the assessment and do not constitute "
        "a guarantee of security, compliance certification, or legal opinion. "
        "The organization is solely responsible for implementing and maintaining "
        "appropriate security controls. This report is confidential and intended solely "
        "for the use of the named client organization."
    )

    def ensure_dirs(self):
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


settings = Settings()
