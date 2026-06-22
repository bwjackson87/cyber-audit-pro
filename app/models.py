"""SQLAlchemy ORM models for CyberAudit Pro."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Float, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    industry = Column(String(100))
    address = Column(Text)
    website = Column(String(200))
    phone = Column(String(50))
    email = Column(String(200))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("Contact", back_populates="client", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    name = Column(String(200), nullable=False)
    title = Column(String(100))
    email = Column(String(200))
    phone = Column(String(50))
    is_primary = Column(Boolean, default=False)

    client = relationship("Client", back_populates="contacts")


class AssessmentTemplate(Base):
    __tablename__ = "assessment_templates"

    id = Column(Integer, primary_key=True, index=True)
    template_key = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(String(20))
    framework = Column(String(100))
    description = Column(Text)
    category = Column(String(100))
    is_builtin = Column(Boolean, default=False)
    template_data = Column(JSON)  # Full template JSON stored here
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects = relationship("Project", back_populates="template")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("assessment_templates.id"))
    name = Column(String(200), nullable=False)
    # Status: draft | in_progress | review | complete
    status = Column(String(50), default="in_progress")
    scope = Column(Text)
    out_of_scope = Column(Text)
    methodology = Column(Text)
    assumptions = Column(Text)
    limitations = Column(Text)
    assessment_date = Column(DateTime)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    consultant_name = Column(String(200))
    consultant_company = Column(String(200))
    consultant_email = Column(String(200))
    consultant_title = Column(String(200))
    report_disclaimer = Column(Text)
    executive_summary = Column(Text)
    overall_score = Column(Float)
    maturity_level = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client = relationship("Client", back_populates="projects")
    template = relationship("AssessmentTemplate", back_populates="projects")
    responses = relationship("AssessmentResponse", back_populates="project", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="project", cascade="all, delete-orphan", order_by="Finding.finding_ref")
    exports = relationship("ReportExport", back_populates="project", cascade="all, delete-orphan")


class AssessmentResponse(Base):
    """One row per control per project — stores the consultant's answer."""

    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    control_id = Column(String(100), nullable=False)
    # compliant | partial | non_compliant | na | not_assessed
    status = Column(String(50), default="not_assessed")
    notes = Column(Text)
    evidence_notes = Column(Text)
    score = Column(Float)  # 0.0–4.0 derived from status
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="responses")


class Finding(Base):
    """A documented finding or observation within a project."""

    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    finding_ref = Column(String(50))          # e.g. F-001
    # finding_type: finding | observation
    finding_type = Column(String(50), default="finding")
    control_ref = Column(String(100))          # e.g. GV.OC-01
    title = Column(String(500), nullable=False)
    description = Column(Text)
    # severity: critical | high | medium | low | informational
    severity = Column(String(50), default="medium")
    affected_systems = Column(Text)
    current_state = Column(Text)
    required_state = Column(Text)
    risk_impact = Column(Text)
    recommendation = Column(Text)
    remediation_detail = Column(Text)
    # remediation_effort: low | medium | high
    remediation_effort = Column(String(50))
    remediation_priority = Column(Integer)     # 1 (immediate) – 5 (long-term)
    compensating_controls = Column(Text)
    is_confirmed = Column(Boolean, default=True)
    likelihood = Column(Integer)               # 1–5
    impact = Column(Integer)                   # 1–5
    risk_score = Column(Float)                 # likelihood × impact
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="findings")


class ReportExport(Base):
    __tablename__ = "report_exports"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_type = Column(String(100))
    format = Column(String(20))
    filepath = Column(String(500))
    generated_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="exports")


class AppSetting(Base):
    """Key/value store for application settings."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
