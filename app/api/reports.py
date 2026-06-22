"""Report generation and download routes."""

import os
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, ReportExport
from app.services.report_generator import generate_docx, generate_pdf, generate_csv_risk_register
from app.config import settings

router = APIRouter(prefix="/reports")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))

REPORT_TYPES = [
    ("full", "Full Assessment Report", "Complete report including all sections"),
    ("executive", "Executive Summary", "High-level overview for leadership"),
    ("findings", "Technical Findings Report", "Detailed findings for technical teams"),
    ("risk_register", "Risk Register", "Complete risk register with scoring"),
    ("remediation", "Remediation Roadmap", "Prioritized remediation plan"),
]


@router.get("/{project_id}", response_class=HTMLResponse)
def reports_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    exports = (
        db.query(ReportExport)
        .filter_by(project_id=project_id)
        .order_by(ReportExport.generated_at.desc())
        .all()
    )

    return templates.TemplateResponse(request, "reports/generate.html", {
        "page": "projects",
        "project": project,
        "exports": exports,
        "report_types": REPORT_TYPES,
    })


@router.post("/{project_id}/generate")
def generate_report(
    project_id: int,
    report_type: str = Form("full"),
    format: str = Form("docx"),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        if format == "docx":
            path = generate_docx(db, project_id, report_type)
        elif format == "pdf":
            path = generate_pdf(db, project_id, report_type)
        elif format == "csv":
            path = generate_csv_risk_register(db, project_id)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown format: {format}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    return RedirectResponse(f"/reports/{project_id}/download/{path.name}", status_code=303)


@router.get("/{project_id}/download/{filename}")
def download_report(project_id: int, filename: str):
    """Serve a generated report file for download."""
    path = settings.EXPORTS_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report file not found")

    # Determine media type
    suffix = path.suffix.lower()
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pdf": "application/pdf",
        ".csv": "text/csv",
    }
    media_type = media_types.get(suffix, "application/octet-stream")

    return FileResponse(str(path), media_type=media_type, filename=filename)
