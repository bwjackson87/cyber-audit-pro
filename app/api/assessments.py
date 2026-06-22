"""Assessment wizard routes — guided Q&A per control."""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Project, AssessmentResponse, Finding
from app.services.scoring import (
    compute_project_score, score_for_status, severity_from_status, next_finding_ref
)
from app.services.template_manager import get_grouped_controls, get_all_controls, get_control_by_id
from app.config import settings

router = APIRouter(prefix="/assessments")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))


@router.get("/{project_id}", response_class=HTMLResponse)
def assessment_wizard(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not project.template:
        return RedirectResponse(f"/projects/{project_id}", status_code=303)

    template_data = project.template.template_data or {}
    grouped = get_grouped_controls(template_data)
    all_controls = get_all_controls(template_data)

    # Build response lookup {control_id: response}
    responses = db.query(AssessmentResponse).filter_by(project_id=project_id).all()
    response_map = {r.control_id: r for r in responses}

    score_data = compute_project_score(responses)

    return templates.TemplateResponse(request, "assessment/wizard.html", {
        "page": "projects",
        "project": project,
        "grouped": grouped,
        "all_controls": all_controls,
        "response_map": response_map,
        "score_data": score_data,
        "total_controls": len(all_controls),
    })


@router.post("/{project_id}/respond")
def save_response(
    project_id: int,
    control_id: str = Form(...),
    status: str = Form("not_assessed"),
    notes: str = Form(""),
    evidence_notes: str = Form(""),
    db: Session = Depends(get_db),
):
    """Save or update a single control response. Called via HTMX or form POST."""
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    response = db.query(AssessmentResponse).filter_by(
        project_id=project_id, control_id=control_id
    ).first()

    score = score_for_status(status)

    if response:
        response.status = status
        response.notes = notes.strip()
        response.evidence_notes = evidence_notes.strip()
        response.score = score
    else:
        response = AssessmentResponse(
            project_id=project_id,
            control_id=control_id,
            status=status,
            notes=notes.strip(),
            evidence_notes=evidence_notes.strip(),
            score=score,
        )
        db.add(response)

    db.commit()

    # Recalculate and persist overall score
    all_responses = db.query(AssessmentResponse).filter_by(project_id=project_id).all()
    score_data = compute_project_score(all_responses)
    project.overall_score = score_data["overall_score"]
    project.maturity_level = score_data["maturity_level"]
    db.commit()

    return JSONResponse({"ok": True, "score_data": score_data})


@router.post("/{project_id}/auto-finding")
def auto_create_finding(
    project_id: int,
    control_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Auto-generate a finding from a non-compliant or partial response."""
    project = db.query(Project).filter_by(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    response = db.query(AssessmentResponse).filter_by(
        project_id=project_id, control_id=control_id
    ).first()
    if not response:
        raise HTTPException(status_code=404, detail="Response not found")

    # Check no finding already exists for this control
    existing = db.query(Finding).filter_by(project_id=project_id, control_ref=control_id).first()
    if existing:
        return JSONResponse({"ok": True, "finding_id": existing.id, "finding_ref": existing.finding_ref, "exists": True})

    # Get control details from template
    ctrl = None
    if project.template and project.template.template_data:
        ctrl = get_control_by_id(project.template.template_data, control_id)

    existing_refs = [f.finding_ref for f in db.query(Finding).filter_by(project_id=project_id).all()]
    ref = next_finding_ref(existing_refs)

    severity = severity_from_status(response.status)
    default_likelihood = 3 if response.status == "partial" else 4
    default_impact = 3

    finding = Finding(
        project_id=project_id,
        finding_ref=ref,
        finding_type="finding",
        control_ref=control_id,
        title=ctrl.get("name", control_id) if ctrl else control_id,
        description=(
            (ctrl.get("question", "") if ctrl else "")
            + ("\n\nNotes: " + response.notes if response.notes else "")
        ).strip(),
        severity=severity,
        risk_impact=ctrl.get("risk_impact", "") if ctrl else "",
        recommendation=ctrl.get("remediation_guidance", "") if ctrl else "",
        current_state=response.notes or "",
        required_state=ctrl.get("required_state", "") if ctrl else "",
        remediation_effort="medium",
        remediation_priority=2 if severity == "high" else 3,
        is_confirmed=True,
        likelihood=default_likelihood,
        impact=default_impact,
        risk_score=float(default_likelihood * default_impact),
    )
    db.add(finding)
    db.commit()
    db.refresh(finding)

    return JSONResponse({"ok": True, "finding_id": finding.id, "finding_ref": finding.finding_ref, "exists": False})


@router.get("/{project_id}/scores")
def get_scores(project_id: int, db: Session = Depends(get_db)):
    """Return current score data as JSON (for live score refresh)."""
    responses = db.query(AssessmentResponse).filter_by(project_id=project_id).all()
    return compute_project_score(responses)
