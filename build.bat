@echo off
setlocal

echo =====================================================
echo  CyberAudit Pro - Build Executable
echo =====================================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or later.
    pause & exit /b 1
)

:: Install/upgrade PyInstaller
echo [1/3] Checking PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: Failed to install PyInstaller.
    pause & exit /b 1
)

:: Clean previous build
echo [2/3] Cleaning previous build...
if exist "dist\CyberAuditPro" rmdir /s /q "dist\CyberAuditPro"
if exist "build\CyberAuditPro" rmdir /s /q "build\CyberAuditPro"

:: Build
echo [3/3] Building executable (this takes 1-3 minutes)...
pyinstaller cyberaudit.spec --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed. Check output above for details.
    pause & exit /b 1
)

echo.
echo =====================================================
echo  Build complete!
echo  Executable folder: dist\CyberAuditPro\
echo  Run: dist\CyberAuditPro\CyberAuditPro.exe
echo.
echo  To distribute: zip the entire dist\CyberAuditPro\ folder.
echo =====================================================
echo.
pause
