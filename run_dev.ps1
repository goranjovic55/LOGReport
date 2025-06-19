# Helper script to run application in development mode with proper Qt setup
$ErrorActionPreference = "Stop"

# Set paths to Qt directories
$pythonPath = "C:\Program Files\Python311"
$qtBinPath = "$PSScriptRoot\.venv\Lib\site-packages\PyQt6\Qt6\bin"
$qtPluginsPath = "$PSScriptRoot\.venv\Lib\site-packages\PyQt6\Qt6\plugins"

# Add paths to environment variables
$env:PATH = "$pythonPath;$qtBinPath;$env:PATH"
$env:QT_PLUGIN_PATH = $qtPluginsPath
$env:QT_QPA_PLATFORM_PLUGIN_PATH = "$qtPluginsPath\platforms"

# Verify paths exist
if (-not (Test-Path $qtPluginsPath)) {
    Write-Host "Qt plugins directory not found at: $qtPluginsPath"
    Exit 1
}

if (-not (Test-Path "$qtPluginsPath\platforms")) {
    Write-Host "Qt platforms plugins directory not found at: $qtPluginsPath\platforms"
    Exit 1
}

Write-Host "Environment setup:"
Write-Host "PATH = $env:PATH"
Write-Host "QT_PLUGIN_PATH = $env:QT_PLUGIN_PATH"
Write-Host "QT_QPA_PLATFORM_PLUGIN_PATH = $env:QT_QPA_PLATFORM_PLUGIN_PATH"

# Run the application
Write-Host "Starting application..."
python src\main.py
