"""Loads assessment templates from JSON files into the database on startup."""

import json
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import AssessmentTemplate
from app.config import settings

log = logging.getLogger(__name__)


def load_builtin_templates(db: Session) -> None:
    """Load (or refresh) all built-in JSON templates into the DB."""
    template_dir: Path = settings.TEMPLATES_DIR
    if not template_dir.exists():
        log.warning("Assessment templates directory not found: %s", template_dir)
        return

    for path in sorted(template_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            log.error("Failed to load template %s: %s", path.name, exc)
            continue

        key = data.get("id") or path.stem
        existing = db.query(AssessmentTemplate).filter_by(template_key=key).first()

        if existing:
            # Refresh template data in case the JSON was updated
            existing.name = data.get("name", existing.name)
            existing.version = data.get("version", existing.version)
            existing.framework = data.get("framework", existing.framework)
            existing.description = data.get("description", existing.description)
            existing.category = data.get("category", existing.category)
            existing.template_data = data
        else:
            tmpl = AssessmentTemplate(
                template_key=key,
                name=data.get("name", key),
                version=data.get("version", ""),
                framework=data.get("framework", ""),
                description=data.get("description", ""),
                category=data.get("category", ""),
                is_builtin=True,
                template_data=data,
            )
            db.add(tmpl)
        db.commit()
        log.info("Loaded template: %s", key)


def get_all_controls(template_data: dict) -> list[dict]:
    """
    Flatten all controls from a template into a single list.
    Works for templates that use 'functions' (NIST CSF style) or
    'domains' / 'controls' (CIS / Small Business style).
    Each returned dict has at minimum: id, name, question, category_id, category_name.
    """
    controls = []

    # NIST CSF style: functions → categories → controls
    for func in template_data.get("functions", []):
        func_id = func.get("id", "")
        func_name = func.get("name", "")
        for cat in func.get("categories", []):
            cat_id = cat.get("id", "")
            cat_name = cat.get("name", "")
            for ctrl in cat.get("controls", []):
                controls.append({
                    **ctrl,
                    "function_id": func_id,
                    "function_name": func_name,
                    "category_id": cat_id,
                    "category_name": cat_name,
                })

    # CIS Controls / flat style: domains → controls
    for domain in template_data.get("domains", []):
        domain_id = domain.get("id", "")
        domain_name = domain.get("name", "")
        for ctrl in domain.get("controls", []):
            controls.append({
                **ctrl,
                "function_id": domain_id,
                "function_name": domain_name,
                "category_id": domain_id,
                "category_name": domain_name,
            })

    # Flat style: top-level controls list
    for ctrl in template_data.get("controls", []):
        controls.append({
            **ctrl,
            "function_id": ctrl.get("domain_id", ""),
            "function_name": ctrl.get("domain_name", ""),
            "category_id": ctrl.get("category_id", ""),
            "category_name": ctrl.get("category_name", ""),
        })

    return controls


def get_control_by_id(template_data: dict, control_id: str) -> dict | None:
    for ctrl in get_all_controls(template_data):
        if ctrl.get("id") == control_id:
            return ctrl
    return None


def get_grouped_controls(template_data: dict) -> list[dict]:
    """
    Returns controls grouped by top-level function/domain for display.
    Each group: {id, name, description, categories: [{id, name, controls: [...]}]}
    """
    groups = []

    # NIST CSF style
    for func in template_data.get("functions", []):
        group = {
            "id": func.get("id"),
            "name": func.get("name"),
            "description": func.get("description", ""),
            "categories": [],
        }
        for cat in func.get("categories", []):
            group["categories"].append({
                "id": cat.get("id"),
                "name": cat.get("name"),
                "description": cat.get("description", ""),
                "controls": cat.get("controls", []),
            })
        groups.append(group)

    # CIS/flat domain style
    for domain in template_data.get("domains", []):
        group = {
            "id": domain.get("id"),
            "name": domain.get("name"),
            "description": domain.get("description", ""),
            "categories": [{
                "id": domain.get("id"),
                "name": domain.get("name"),
                "description": domain.get("description", ""),
                "controls": domain.get("controls", []),
            }],
        }
        groups.append(group)

    return groups
