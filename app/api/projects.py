"""Project management routes."""

from datetime import datetime
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Client, Project, AssessmentTemplate, AssessmentResponse, AppSetting
from app.services.scoring import compute_project_score
from app.config import settings

router = APIRouter(prefix="/projects")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))


def _get_setting(db: Session, key: str, default: str = "") -> str:
    s = db.query(AppSetting).filter_by(key=key).first()
    return s.value if s else default


@router.get("/", response_class=HTMLResponse)
def list_projects(request: Request, db: Session = Depends(get_db)):
    projects = (
        db.query(Project)
        .order_by(Project.updated_at.desc())
        .all()
    )
    return templates.TemplateResponse(request, "projects/list.html", { "page": "projects", "projects": projects
    })


@router.get("/new", response_class=HTMLResponse)
def new_project_form(request: Request, client_id: Optional[int] = None, db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.name).all()
    assessment_templates = db.query(AssessmentTemplate).order_by(AssessmentTemplate.name).all()
    selected_client = db.query(Client).filter_by(id=client_id).first() if client_id else None
    return templates.TemplateResponse(request, "projects/form.html", {
        "page": "projects",
        "project": None,
        "action": "create",
        "clients": clients,
        "assessment_templates": assessment_templates,
        "selected_client": selected_client,
        "default_consultant_name": _get_setting(db, "consultant_name"),
        "default_consultant_company": _get_setting(db, "consultant_company"),
        "default_consultant_email": _get_setting(db, "consultant_email"),
        "default_consultant_title": _get_setting(db, "consultant_title", "Cybersecurity Consultant"),
        "default_disclaimer": _get_setting(db, "default_disclaimer", settings.DEFAULT_DISCLAIMER),
    })


@router.post("/new")
def create_project(
    client_id: int = Form(...),
    template_id: int = Form(...),
    name: str = Form(...),
    scope: str = Form(""),
    out_of_scope: str = Form(""),
    methodology: str = Form(""),
    assumptions: str = Form(""),
    limitations: str = Form(""),
    assessment_date: str = Form(""),
    consultant_name: str = Form(""),
    consultant_company: str = Form(""),
    consultant_email: str = Form(""),
    consultant_title: str = Form(""),
    report_disclaimer: str = Form(""),
    db: Session = Depends(get_db),
):
    adate = None
    if assessment_date:
        try:
            adate = datetime.strptime(assessment_date, "%Y-%m-%d")
        except ValueError:
            pass

    project = Project(
        client_id=client_id,
        template_id=template_id if template_id else None,
        name=name.strip(),
        scope=scope.strip(),
        out_of_scope=out_of_scope.strip(),
        methodology=methodology.strip(),
        assumptions=assumptions.strip(),
        limitations=limitations.strip(),
        assessment_date=adate,
        consultant_name=consultant_name.strip(),
        consultant_company=consultant_company.strip(),
        consultant_email=consultant_email.strip(),
        consultant_title=consultant_title.strip(),
        report_disclaimer=report_disclaimer.strip(),
        status="in_progress",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return RedirectResponse(f"/projects/{project.id}", status_code=303)


@router.get("/{project_id}", response_class=HTMLResponse)
def project_detail(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    responses = db.query(AssessmentResponse).filter_by(project_id=project_id).all()
    score_data = compute_project_score(responses)

    return templates.TemplateResponse(request, "projects/detail.html", {
        "page": "projects",
        "project": project,
        "score_data": score_data,
    })


@router.get("/{project_id}/edit", response_class=HTMLResponse)
def edit_project_form(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    clients = db.query(Client).order_by(Client.name).all()
    assessment_templates = db.query(AssessmentTemplate).order_by(AssessmentTemplate.name).all()
    return templates.TemplateResponse(request, "projects/form.html", {
        "page": "projects",
        "project": project,
        "action": "edit",
        "clients": clients,
        "assessment_templates": assessment_templates,
        "default_disclaimer": settings.DEFAULT_DISCLAIMER,
    })


@router.post("/{project_id}/edit")
def update_project(
    project_id: int,
    client_id: int = Form(...),
    template_id: int = Form(None),
    name: str = Form(...),
    status: str = Form("in_progress"),
    scope: str = Form(""),
    out_of_scope: str = Form(""),
    methodology: str = Form(""),
    assumptions: str = Form(""),
    limitations: str = Form(""),
    assessment_date: str = Form(""),
    consultant_name: str = Form(""),
    consultant_company: str = Form(""),
    consultant_email: str = Form(""),
    consultant_title: str = Form(""),
    report_disclaimer: str = Form(""),
    executive_summary: str = Form(""),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    adate = None
    if assessment_date:
        try:
            adate = datetime.strptime(assessment_date, "%Y-%m-%d")
        except ValueError:
            pass

    project.client_id = client_id
    project.template_id = template_id
    project.name = name.strip()
    project.status = status
    project.scope = scope.strip()
    project.out_of_scope = out_of_scope.strip()
    project.methodology = methodology.strip()
    project.assumptions = assumptions.strip()
    project.limitations = limitations.strip()
    project.assessment_date = adate
    project.consultant_name = consultant_name.strip()
    project.consultant_company = consultant_company.strip()
    project.consultant_email = consultant_email.strip()
    project.consultant_title = consultant_title.strip()
    project.report_disclaimer = report_disclaimer.strip()
    project.executive_summary = executive_summary.strip()
    db.commit()
    return RedirectResponse(f"/projects/{project_id}", status_code=303)


@router.post("/{project_id}/delete")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return RedirectResponse("/projects/", status_code=303)
