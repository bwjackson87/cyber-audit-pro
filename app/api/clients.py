"""Client and contact management routes."""

from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Client, Contact
from app.config import settings

router = APIRouter(prefix="/clients")
templates = Jinja2Templates(directory=str(settings.HTML_TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def list_clients(request: Request, db: Session = Depends(get_db)):
    clients = db.query(Client).order_by(Client.name).all()
    return templates.TemplateResponse(request, "clients/list.html", { "page": "clients", "clients": clients
    })


@router.get("/new", response_class=HTMLResponse)
def new_client_form(request: Request):
    return templates.TemplateResponse(request, "clients/form.html", { "page": "clients", "client": None, "action": "create"
    })


@router.post("/new")
def create_client(
    request: Request,
    name: str = Form(...),
    industry: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    client = Client(
        name=name.strip(),
        industry=industry.strip(),
        address=address.strip(),
        website=website.strip(),
        phone=phone.strip(),
        email=email.strip(),
        notes=notes.strip(),
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return RedirectResponse(f"/clients/{client.id}", status_code=303)


@router.get("/{client_id}", response_class=HTMLResponse)
def client_detail(client_id: int, request: Request, db: Session = Depends(get_db)):
    client = db.query(Client).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return templates.TemplateResponse(request, "clients/detail.html", { "page": "clients", "client": client
    })


@router.get("/{client_id}/edit", response_class=HTMLResponse)
def edit_client_form(client_id: int, request: Request, db: Session = Depends(get_db)):
    client = db.query(Client).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return templates.TemplateResponse(request, "clients/form.html", { "page": "clients", "client": client, "action": "edit"
    })


@router.post("/{client_id}/edit")
def update_client(
    client_id: int,
    name: str = Form(...),
    industry: str = Form(""),
    address: str = Form(""),
    website: str = Form(""),
    phone: str = Form(""),
    email: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db),
):
    client = db.query(Client).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    client.name = name.strip()
    client.industry = industry.strip()
    client.address = address.strip()
    client.website = website.strip()
    client.phone = phone.strip()
    client.email = email.strip()
    client.notes = notes.strip()
    db.commit()
    return RedirectResponse(f"/clients/{client_id}", status_code=303)


@router.post("/{client_id}/delete")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.query(Client).filter_by(id=client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    return RedirectResponse("/clients/", status_code=303)


# ── Contacts ──────────────────────────────────────────────────────────────────

@router.post("/{client_id}/contacts/add")
def add_contact(
    client_id: int,
    name: str = Form(...),
    title: str = Form(""),
    email: str = Form(""),
    phone: str = Form(""),
    is_primary: bool = Form(False),
    db: Session = Depends(get_db),
):
    contact = Contact(
        client_id=client_id,
        name=name.strip(),
        title=title.strip(),
        email=email.strip(),
        phone=phone.strip(),
        is_primary=is_primary,
    )
    db.add(contact)
    db.commit()
    return RedirectResponse(f"/clients/{client_id}", status_code=303)


@router.post("/{client_id}/contacts/{contact_id}/delete")
def delete_contact(client_id: int, contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(Contact).filter_by(id=contact_id, client_id=client_id).first()
    if contact:
        db.delete(contact)
        db.commit()
    return RedirectResponse(f"/clients/{client_id}", status_code=303)
