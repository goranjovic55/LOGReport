@echo off
SETLOCAL ENABLEDELAYEDEXPANSION

echo.
echo ===================================================
echo LOGReporter BUILD SCRIPT - SIP Module Fix
echo ===================================================
echo.

REM Get PyQt6.sip location
for /f "delims=" %%a in ('python -c "import PyQt6.sip, os; print(os.path.dirname(PyQt6.sip.__file__))"') do set SIP_DIR=%%a

echo Detected PyQt6.sip directory: !SIP_DIR!

REM Set Qt6 bin directory
set QT_BIN=C:\Program Files\Python311\Lib\site-packages\PyQt6\Qt6\bin

REM Ensure requirements are installed
echo [1/4] Installing dependencies...
pip install -r requirements-narrow.txt

echo.
echo [2/4] Building executable with PyInstaller...
echo Adding PyQt6.sip directory: !SIP_DIR!
echo ---------------------------------------------------
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "LOGReporter" ^
    --add-binary "!SIP_DIR!\*;PyQt6" ^
    --add-data "src;src" ^
    --add-data "_PROJECT;_PROJECT" ^
    --add-data "test_logs;test_logs" ^
    --add-data "nodes.json;." ^
    --add-binary "!QT_BIN!\Qt6Core.dll;." ^
    --add-binary "!QT_BIN!\Qt6Gui.dll;." ^
    --add-binary "!QT_BIN!\Qt6Widgets.dll;." ^
    --hidden-import PyQt6.sip ^
    --clean ^
    src\main.py

IF ERRORLEVEL 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Build complete! 
echo ---------------------------------------------------
echo.
echo [4/4] Launching application...
echo ===================================================
TIMEOUT /T 1
START "" "dist\LOGReporter.exe"
