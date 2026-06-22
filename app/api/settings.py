"""Application settings routes — consultant branding, defaults."""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AppSetting
from app.config import settings as app_settings

router = APIRouter(prefix="/settings")
templates = Jinja2Templates(directory=str(app_settings.HTML_TEMPLATES_DIR))

SETTING_KEYS = [
    "consultant_name",
    "consultant_company",
    "consultant_email",
    "consultant_title",
    "default_disclaimer",
]


def _get_all_settings(db: Session) -> dict:
    rows = db.query(AppSetting).all()
    return {r.key: r.value for r in rows}


def _set_setting(db: Session, key: str, value: str):
    row = db.query(AppSetting).filter_by(key=key).first()
    if row:
        row.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    db.commit()


@router.get("/", response_class=HTMLResponse)
def settings_page(request: Request, db: Session = Depends(get_db)):
    current = _get_all_settings(db)
    return templates.TemplateResponse(request, "settings/index.html", {
        "page": "settings",
        "s": current,
        "default_disclaimer": app_settings.DEFAULT_DISCLAIMER,
    })


@router.post("/save")
def save_settings(
    consultant_name: str = Form(""),
    consultant_company: str = Form(""),
    consultant_email: str = Form(""),
    consultant_title: str = Form(""),
    default_disclaimer: str = Form(""),
    db: Session = Depends(get_db),
):
    _set_setting(db, "consultant_name", consultant_name.strip())
    _set_setting(db, "consultant_company", consultant_company.strip())
    _set_setting(db, "consultant_email", consultant_email.strip())
    _set_setting(db, "consultant_title", consultant_title.strip())
    _set_setting(db, "default_disclaimer", default_disclaimer.strip())
    return RedirectResponse("/settings/?saved=1", status_code=303)
