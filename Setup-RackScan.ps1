$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
$python = Join-Path $root "backend\.venv\Scripts\python.exe"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw "Python is required. Install Python 3.13+ from python.org, then run this script again." }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Node.js 20+ is required. Install it from nodejs.org, then run this script again." }
if (-not (Test-Path $python)) { & py -m venv (Join-Path $root "backend\.venv") }
& $python -m pip install --upgrade pip
& $python -m pip install -r (Join-Path $root "backend\requirements.txt")
Push-Location (Join-Path $root "frontend")
try { npm install } finally { Pop-Location }
Write-Host "RackScan is set up. Run .\Start-RackScan.ps1 to launch it." -ForegroundColor Green
