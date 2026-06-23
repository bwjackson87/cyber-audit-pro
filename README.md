---
> **Security & Sanitization Notice:** This repository contains sanitized, lab-safe code and documentation. It does not include proprietary, classified, sensitive, or employer-owned data. Hostnames, domains, usernames, IP addresses, and operational details are fictionalized or generalized. See [SECURITY_NOTICE.md](SECURITY_NOTICE.md) for full details.
---

# CyberAudit Pro

## Overview
A local-first cybersecurity assessment and reporting platform for consultants and security practitioners. CyberAudit Pro guides auditors through structured control assessments against industry frameworks, tracks findings with severity ratings and remediation effort scores, and generates polished Word and PDF deliverable reports — all from a browser-based interface that runs entirely on the local machine with no internet connection required.

## Problem It Solves
Cybersecurity assessments are often conducted using a patchwork of spreadsheets, Word documents, and manual copy-paste — making it time-consuming to produce consistent, professional deliverables and easy to lose track of finding status across engagements. CyberAudit Pro replaces that workflow with a structured, database-backed platform that enforces consistency across every assessment, generates client-ready reports in one click, and keeps all engagement data local and under the practitioner's control.

## Key Features
- **Multi-framework assessments** — built-in templates for NIST CSF 2.0, CIS Controls v8, and a Small Business Essentials profile; import custom JSON templates
- **Guided assessment wizard** — step through every control, mark compliance (Compliant / Partial / Non-Compliant / N/A), and capture evidence notes
- **Automated scoring engine** — computes a 0–100 maturity score per category and overall, mapped to five maturity levels (Initial → Optimizing)
- **Finding management** — severity (Critical → Informational), likelihood/impact scoring, remediation effort, and linked control references
- **One-click report export** — `.docx` and `.pdf` with executive summary, risk matrix, per-finding tables, and remediation roadmap
- **Client & project CRM** — manage multiple clients, contacts, and concurrent audit engagements
- **Local-first architecture** — runs on `127.0.0.1:8765`; all data in SQLite; no cloud dependency
- **Portable executable** — ships as a single `.exe` via PyInstaller; no Python installation required on the end-user machine

## Technologies Used
- Python 3.11+
- FastAPI + Uvicorn (web framework and server)
- Jinja2 (HTML templating)
- SQLite via SQLAlchemy 2.0 (local database)
- Pydantic v2 (data validation)
- python-docx + ReportLab (Word and PDF report generation)
- PyInstaller (portable executable build)

## Example Use Case
A security consultant is engaged to assess a mid-sized manufacturer against NIST CSF 2.0. They open CyberAudit Pro, create a new project for the client, and work through the 100+ controls over two days of interviews and documentation review — marking each control compliant or non-compliant and attaching evidence notes. At the end of the engagement, they click Export and hand the client a branded Word report with an executive summary, a color-coded risk matrix, and a prioritized remediation roadmap — work that previously took an additional half-day of formatting.

## How to Run

**Requirements:** Python 3.11 or later

```batch
# First-time setup — creates virtual environment and installs dependencies
setup.bat

# Launch the application
run.bat
```

Open your browser to `http://127.0.0.1:8765`.

**Build a standalone executable (no Python required on target machine):**

```batch
build.bat
```

Output: `dist\CyberAuditPro\CyberAuditPro.exe`

**Manual setup (without batch scripts):**

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Example Output

**Maturity scoring output:**

| Score Range | Maturity Level |
|---|---|
| 0–19 | Level 1 — Initial |
| 20–39 | Level 2 — Developing |
| 40–59 | Level 3 — Defined |
| 60–79 | Level 4 — Managed |
| 80–100 | Level 5 — Optimizing |

**Generated report includes:**
- Executive summary with overall maturity score
- Per-category score breakdown (Identify, Protect, Detect, Respond, Recover)
- Risk matrix (severity × likelihood heatmap)
- Findings table with control reference, severity, and remediation effort
- Prioritized remediation roadmap

## Security Notes
- All data is stored locally in SQLite — no data leaves the machine
- The application binds only to `127.0.0.1` — it is not accessible from the network by default
- Do not expose the application on `0.0.0.0` or behind a reverse proxy without adding authentication
- Assessment data may contain sensitive client information — protect the SQLite database file accordingly and exclude it from version control (`.gitignore`)
- Authorized use only — intended for use during authorized security assessments

## Lessons Learned
- FastAPI's automatic OpenAPI docs (`/docs`) are useful during development but should be disabled in any deployment that handles sensitive client data
- SQLAlchemy 2.0's `Session.execute()` with explicit `select()` statements is more predictable than the 1.x-style `Session.query()` when working with async-adjacent patterns, even in a synchronous app
- Generating `.docx` output with `python-docx` requires careful table and paragraph style management — building a base template document first and populating it programmatically produces far more consistent results than constructing the document entirely from code
- Pydantic v2's `model_validator` and `field_validator` replace the v1 `@validator` decorator; migrating early in the project saved significant refactoring effort later
