# PowerShell script to create virtual environment for LOGReporter

# Verify python is available
$pythonPath = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
if (-not $pythonPath) {
    Write-Host "ERROR: Python not found in PATH. Please install Python 3.10+ and add it to PATH."
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment in .venv"
python -m venv .venv

# Activate virtual environment
Write-Host "Activating virtual environment"
.\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies from requirements-narrow.txt"
pip install -r requirements-narrow.txt

# Verify installation
Write-Host "`nVirtual environment setup complete!"
Write-Host "Run the application with:`n    .\.venv\Scripts\python .\src\main.py"
Write-Host "Or build it with:`n    .\build.bat"