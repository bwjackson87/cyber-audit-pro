"""Findings and risk register management routes."""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Project, Finding
from app.services.scoring import compute_risk_score, next_finding_ref
from app.config import settings

router = APIRouter(prefix="/findings")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))

SEVERITY_OPTIONS = ["critical", "high", "medium", "low", "informational"]
EFFORT_OPTIONS = ["low", "medium", "high"]


@router.get("/{project_id}", response_class=HTMLResponse)
def list_findings(
    project_id: int,
    request: Request,
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    query = db.query(Finding).filter_by(project_id=project_id)
    if severity:
        query = query.filter(Finding.severity == severity)

    findings = query.order_by(Finding.finding_ref).all()

    sev_counts = {s: 0 for s in SEVERITY_OPTIONS}
    all_findings = db.query(Finding).filter_by(project_id=project_id).all()
    for f in all_findings:
        if f.severity in sev_counts:
            sev_counts[f.severity] += 1

    return templates.TemplateResponse(request, "findings/list.html", {
        "page": "projects",
        "project": project,
        "findings": findings,
        "sev_counts": sev_counts,
        "severity_filter": severity,
        "severity_options": SEVERITY_OPTIONS,
    })


@router.get("/{project_id}/new", response_class=HTMLResponse)
def new_finding_form(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return templates.TemplateResponse(request, "findings/form.html", {
        "page": "projects",
        "project": project,
        "finding": None,
        "action": "create",
        "severity_options": SEVERITY_OPTIONS,
        "effort_options": EFFORT_OPTIONS,
    })


@router.post("/{project_id}/new")
def create_finding(
    project_id: int,
    title: str = Form(...),
    finding_type: str = Form("finding"),
    control_ref: str = Form(""),
    description: str = Form(""),
    severity: str = Form("medium"),
    affected_systems: str = Form(""),
    current_state: str = Form(""),
    required_state: str = Form(""),
    risk_impact: str = Form(""),
    recommendation: str = Form(""),
    remediation_detail: str = Form(""),
    remediation_effort: str = Form("medium"),
    remediation_priority: int = Form(3),
    compensating_controls: str = Form(""),
    is_confirmed: bool = Form(True),
    likelihood: int = Form(3),
    impact: int = Form(3),
    db: Session = Depends(get_db),
):
    existing_refs = [f.finding_ref for f in db.query(Finding).filter_by(project_id=project_id).all()]
    ref = next_finding_ref(existing_refs)
    risk_score = compute_risk_score(likelihood, impact)

    finding = Finding(
        project_id=project_id,
        finding_ref=ref,
        finding_type=finding_type,
        control_ref=control_ref.strip(),
        title=title.strip(),
        description=description.strip(),
        severity=severity,
        affected_systems=affected_systems.strip(),
        current_state=current_state.strip(),
        required_state=required_state.strip(),
        risk_impact=risk_impact.strip(),
        recommendation=recommendation.strip(),
        remediation_detail=remediation_detail.strip(),
        remediation_effort=remediation_effort,
        remediation_priority=remediation_priority,
        compensating_controls=compensating_controls.strip(),
        is_confirmed=is_confirmed,
        likelihood=likelihood,
        impact=impact,
        risk_score=risk_score,
    )
    db.add(finding)
    db.commit()
    return RedirectResponse(f"/findings/{project_id}", status_code=303)


@router.get("/{project_id}/{finding_id}/edit", response_class=HTMLResponse)
def edit_finding_form(project_id: int, finding_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    finding = db.query(Finding).filter_by(id=finding_id, project_id=project_id).first()
    if not project or not finding:
        raise HTTPException(status_code=404, detail="Not found")
    return templates.TemplateResponse(request, "findings/form.html", {
        "page": "projects",
        "project": project,
        "finding": finding,
        "action": "edit",
        "severity_options": SEVERITY_OPTIONS,
        "effort_options": EFFORT_OPTIONS,
    })


@router.post("/{project_id}/{finding_id}/edit")
def update_finding(
    project_id: int,
    finding_id: int,
    title: str = Form(...),
    finding_type: str = Form("finding"),
    control_ref: str = Form(""),
    description: str = Form(""),
    severity: str = Form("medium"),
    affected_systems: str = Form(""),
    current_state: str = Form(""),
    required_state: str = Form(""),
    risk_impact: str = Form(""),
    recommendation: str = Form(""),
    remediation_detail: str = Form(""),
    remediation_effort: str = Form("medium"),
    remediation_priority: int = Form(3),
    compensating_controls: str = Form(""),
    is_confirmed: bool = Form(True),
    likelihood: int = Form(3),
    impact: int = Form(3),
    db: Session = Depends(get_db),
):
    finding = db.query(Finding).filter_by(id=finding_id, project_id=project_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")

    risk_score = compute_risk_score(likelihood, impact)

    finding.title = title.strip()
    finding.finding_type = finding_type
    finding.control_ref = control_ref.strip()
    finding.description = description.strip()
    finding.severity = severity
    finding.affected_systems = affected_systems.strip()
    finding.current_state = current_state.strip()
    finding.required_state = required_state.strip()
    finding.risk_impact = risk_impact.strip()
    finding.recommendation = recommendation.strip()
    finding.remediation_detail = remediation_detail.strip()
    finding.remediation_effort = remediation_effort
    finding.remediation_priority = remediation_priority
    finding.compensating_controls = compensating_controls.strip()
    finding.is_confirmed = is_confirmed
    finding.likelihood = likelihood
    finding.impact = impact
    finding.risk_score = risk_score
    db.commit()
    return RedirectResponse(f"/findings/{project_id}", status_code=303)


@router.post("/{project_id}/{finding_id}/delete")
def delete_finding(project_id: int, finding_id: int, db: Session = Depends(get_db)):
    finding = db.query(Finding).filter_by(id=finding_id, project_id=project_id).first()
    if finding:
        db.delete(finding)
        db.commit()
    return RedirectResponse(f"/findings/{project_id}", status_code=303)
