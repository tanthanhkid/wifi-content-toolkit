$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "=== WiFi Marketing Content Toolkit — Install ==="

if (-Not (Test-Path "$ScriptDir\.venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv "$ScriptDir\.venv"
}

& "$ScriptDir\.venv\Scripts\Activate.ps1"

Write-Host "Installing shared..."
pip install -e "$ScriptDir\shared"

foreach ($module in @("imggen", "poster", "tts", "talkhead", "vidmake")) {
    Write-Host "Installing $module..."
    pip install -e "$ScriptDir\$module"
}

Write-Host "Installing Playwright Chromium..."
playwright install chromium

Write-Host ""
Write-Host "=== Done! ==="
Write-Host "Activate venv: $ScriptDir\.venv\Scripts\Activate.ps1"
Write-Host "Run setup:     wfm-setup"
