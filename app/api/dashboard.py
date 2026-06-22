"""Dashboard page and stats API."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Client, Project, Finding, AssessmentTemplate
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    client_count = db.query(func.count(Client.id)).scalar()
    project_count = db.query(func.count(Project.id)).scalar()
    finding_count = db.query(func.count(Finding.id)).scalar()
    template_count = db.query(func.count(AssessmentTemplate.id)).scalar()

    recent_projects = (
        db.query(Project)
        .order_by(Project.updated_at.desc())
        .limit(5)
        .all()
    )

    # Findings by severity for summary
    sev_counts = {}
    for sev in ["critical", "high", "medium", "low", "informational"]:
        count = db.query(func.count(Finding.id)).filter(Finding.severity == sev).scalar()
        sev_counts[sev] = count

    return templates.TemplateResponse(request, "dashboard.html", {
        "page": "dashboard",
        "client_count": client_count,
        "project_count": project_count,
        "finding_count": finding_count,
        "template_count": template_count,
        "recent_projects": recent_projects,
        "sev_counts": sev_counts,
    })
