@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo ===================================================
echo LOGReporter EXECUTABLE BUILD SCRIPT
echo Now with robust icon handling
echo ===================================================
echo.

REM Ensure requirements are installed
echo [1/4] Checking dependencies...
pip install -r requirements-narrow.txt

REM Create necessary directories
echo.
echo [2/4] Preparing directories...
mkdir assets 2>nul
mkdir dist 2>nul

REM Handle icon file presence
set ICON_FLAG=
if exist assets\logo.ico (
    echo Valid icon found at assets\logo.ico
    set ICON_FLAG=--icon assets\logo.ico
) else (
    echo WARNING: No valid icon found. Building without application icon.
    echo You can add a .ico file to: assets\logo.ico
    set ICON_FLAG=
)

REM Run PyInstaller build
echo.
echo [3/4] Building executable with PyInstaller...
echo Using flags: !ICON_FLAG!
echo ---------------------------------------------------
pyinstaller --onefile --windowed --name "LOGReporter" ^
    !ICON_FLAG! ^
    --add-data "src;src" ^
    --add-data "_PROJECT;_PROJECT" ^
    --add-data "test_logs;test_logs" ^
    --add-data "nodes.json;." ^
    --version-file version_info.txt ^
    --hidden-import PyQt6.sip ^
    --hidden-import PyQt6.QtPrintSupport ^
    --hidden-import reportlab.pdfbase._fontdata ^
    --hidden-import reportlab.lib.fonts ^
    --clean ^
    src\main.py -- --gui

IF ERRORLEVEL 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Final message
echo.
echo [4/4] Build complete!
echo ---------------------------------------------------
echo.
echo Executable created at: %cd%\dist\LOGReporter.exe
echo.
if not exist assets\logo.ico (
    echo NOTE: You can add a custom icon later:
    echo       1. Create a valid .ico file
    echo       2. Save it as assets\logo.ico
    echo       3. Rebuild the executable
)
echo ==================== COMPLETE ====================
timeout /t 10
