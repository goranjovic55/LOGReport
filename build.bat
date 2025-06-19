@echo off
REM Build script for LOGReporter

echo ============================================
echo LOGReporter BUILD SCRIPT (venv-based)
echo ============================================

echo [1/5] Activating virtual environment...
call .venv\Scripts\activate

echo [2/5] Checking for UPX...
where upx >nul 2>&1
if %errorlevel% neq 0 (
    echo UPX not found in PATH. Compression might be slower.
) else (
    echo UPX detected. Will compress binaries.
)

echo [3/5] Removing old build artifacts...
rmdir /s /q dist 2>nul
rmdir /s /q build 2>nul

echo [4/5] Building executable with PyInstaller (using LOGReporter.spec)...
echo ---------------------------------------------------
.venv\Scripts\python.exe -m PyInstaller LOGReporter.spec

if %errorlevel% neq 0 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo ---------------------------------------------------
echo [5/5] Build successful! Output in dist\LOGReporter
echo Launching application for verification...
start dist\LOGReporter\LOGReporter.exe
pause
