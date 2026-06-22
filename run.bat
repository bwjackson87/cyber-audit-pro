@echo off
cd /d "%~dp0"
echo CyberAudit Pro - Starting at http://127.0.0.1:8765
echo Press Ctrl+C to stop.
echo.

:: Use venv if available, else system Python
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe main.py
) else (
    python main.py
)

if errorlevel 1 (
    echo.
    echo ERROR: Server failed to start. Make sure dependencies are installed:
    echo   pip install -r requirements.txt
    pause
)
