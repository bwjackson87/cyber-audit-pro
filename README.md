# CyberAudit Pro

A professional cybersecurity assessment and reporting platform for consultants. CyberAudit Pro guides auditors through structured control assessments against industry frameworks, tracks findings with severity ratings, and generates polished Word/PDF deliverable reports — all from a local web interface that runs without an internet connection.

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi) ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red) ![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **Multi-framework assessments** — built-in templates for NIST CSF 2.0, CIS Controls v8, and a Small Business Essentials profile; import custom JSON templates
- **Guided assessment wizard** — step through every control, mark compliance status (Compliant / Partial / Non-Compliant / N/A), and capture evidence notes
- **Automated scoring engine** — computes a 0–100 maturity score per category and overall, mapped to five maturity levels (Initial → Optimizing)
- **Finding management** — create, edit, and prioritize findings with severity (Critical → Informational), likelihood/impact scoring, remediation effort, and linked control references
- **Professional report generation** — one-click export to `.docx` (Word) and `.pdf` with executive summary, risk matrix, per-finding detail tables, and remediation roadmap
- **Client & project CRM** — manage multiple clients, contacts, and concurrent audit projects
- **Local-first architecture** — runs entirely on `127.0.0.1:8765`; all data stored in SQLite; no cloud dependency
- **Portable executable** — ships as a single `.exe` built with PyInstaller; no Python installation required for end users

## Screenshots

> Run the app and visit `http://127.0.0.1:8765` to see it in action.

## Quick Start (from source)

**Requirements:** Python 3.11 or later

```batch
# 1. Install dependencies and create virtual environment
setup.bat

# 2. Start the application
run.bat
```

The app opens in your default browser at `http://127.0.0.1:8765`.

## Build a Standalone Executable

```batch
build.bat
```

Output: `dist\CyberAuditPro\CyberAuditPro.exe` — zip the entire `dist\CyberAuditPro\` folder to distribute.

## Manual Setup (without the batch scripts)

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Web framework | FastAPI + Uvicorn |
| Templating | Jinja2 |
| Database | SQLite via SQLAlchemy 2.0 |
| Data validation | Pydantic v2 |
| Report generation | python-docx, ReportLab |
| Build/distribution | PyInstaller |

## Project Structure

```
cyberaudit/
├── main.py                         # Application entry point
├── cyberaudit.spec                 # PyInstaller build spec
├── requirements.txt
├── setup.bat                       # First-run setup script
├── run.bat                         # Launch script
├── build.bat                       # Build executable
├── app/
│   ├── config.py                   # Paths, settings, version
│   ├── database.py                 # SQLAlchemy engine + session
│   ├── models.py                   # ORM models
│   ├── api/                        # FastAPI routers
│   │   ├── clients.py
│   │   ├── projects.py
│   │   ├── assessments.py
│   │   ├── findings.py
│   │   ├── reports.py
│   │   ├── templates_api.py
│   │   ├── settings.py
│   │   └── dashboard.py
│   └── services/
│       ├── scoring.py              # Maturity scoring engine
│       ├── report_generator.py     # DOCX/PDF export
│       └── template_manager.py     # Assessment template loader
├── templates/                      # Jinja2 HTML templates
├── static/                         # CSS assets
└── data/
    └── assessment_templates/       # Built-in framework JSON files
        ├── nist_csf_2_0.json
        ├── cis_controls_v8.json
        └── small_business.json
```

## Assessment Frameworks

| Framework | Controls | Description |
|-----------|----------|-------------|
| NIST CSF 2.0 | ~100 | NIST Cybersecurity Framework v2.0 — Govern, Identify, Protect, Detect, Respond, Recover |
| CIS Controls v8 | 153 | Center for Internet Security Critical Security Controls |
| Small Business | ~30 | Streamlined profile for SMB environments |

## Maturity Model

Scores are computed on a 0–100 scale across all assessed controls:

| Score | Level |
|-------|-------|
| 0–19 | Level 1 — Initial |
| 20–39 | Level 2 — Developing |
| 40–59 | Level 3 — Defined |
| 60–79 | Level 4 — Managed |
| 80–100 | Level 5 — Optimizing |

## License

MIT — see [LICENSE](LICENSE) for details.
