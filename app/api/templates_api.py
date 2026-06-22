"""Assessment template management routes."""

import json
from fastapi import APIRouter, Depends, Request, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models import AssessmentTemplate
from app.services.template_manager import get_all_controls
from app.config import settings

router = APIRouter(prefix="/templates")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def list_templates(request: Request, db: Session = Depends(get_db)):
    tmpl_list = db.query(AssessmentTemplate).order_by(AssessmentTemplate.name).all()
    return templates.TemplateResponse(request, "templates_mgr/list.html", { "page": "templates", "template_list": tmpl_list
    })


@router.get("/{template_id}/view", response_class=HTMLResponse)
def view_template(template_id: int, request: Request, db: Session = Depends(get_db)):
    tmpl = db.query(AssessmentTemplate).filter_by(id=template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    controls = get_all_controls(tmpl.template_data or {})
    return templates.TemplateResponse(request, "templates_mgr/detail.html", {
        "page": "templates",
        "tmpl": tmpl,
        "controls": controls,
        "control_count": len(controls),
    })


@router.post("/{template_id}/duplicate")
def duplicate_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(AssessmentTemplate).filter_by(id=template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    new_data = dict(tmpl.template_data or {})
    new_key = f"{tmpl.template_key}_copy_{int(datetime.utcnow().timestamp())}"
    new_data["id"] = new_key
    new_data["name"] = f"{tmpl.name} (Copy)"

    new_tmpl = AssessmentTemplate(
        template_key=new_key,
        name=f"{tmpl.name} (Copy)",
        version=tmpl.version,
        framework=tmpl.framework,
        description=tmpl.description,
        category=tmpl.category,
        is_builtin=False,
        template_data=new_data,
    )
    db.add(new_tmpl)
    db.commit()
    return RedirectResponse("/templates/", status_code=303)


@router.get("/{template_id}/export")
def export_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(AssessmentTemplate).filter_by(id=template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")

    settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"template_{tmpl.template_key}.json"
    path = settings.EXPORTS_DIR / filename
    path.write_text(json.dumps(tmpl.template_data, indent=2), encoding="utf-8")
    return FileResponse(str(path), media_type="application/json", filename=filename)


@router.post("/import")
async def import_template(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    key = data.get("id") or file.filename.replace(".json", "")
    # Make key unique if it already exists
    existing = db.query(AssessmentTemplate).filter_by(template_key=key).first()
    if existing:
        key = f"{key}_{int(datetime.utcnow().timestamp())}"
        data["id"] = key

    tmpl = AssessmentTemplate(
        template_key=key,
        name=data.get("name", key),
        version=data.get("version", ""),
        framework=data.get("framework", ""),
        description=data.get("description", ""),
        category=data.get("category", "Custom"),
        is_builtin=False,
        template_data=data,
    )
    db.add(tmpl)
    db.commit()
    return RedirectResponse("/templates/", status_code=303)


@router.post("/{template_id}/delete")
def delete_template(template_id: int, db: Session = Depends(get_db)):
    tmpl = db.query(AssessmentTemplate).filter_by(id=template_id).first()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    if tmpl.is_builtin:
        raise HTTPException(status_code=400, detail="Cannot delete a built-in template")
    db.delete(tmpl)
    db.commit()
    return RedirectResponse("/templates/", status_code=303)
