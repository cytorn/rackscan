$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSCommandPath
$python = Join-Path $root "backend\.venv\Scripts\python.exe"
$frontend = Join-Path $root "frontend"

if (-not (Test-Path $python) -or -not (Test-Path (Join-Path $frontend "node_modules"))) { throw "RackScan is not set up yet. Run .\Setup-RackScan.ps1 once, then try again." }
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; & '$python' -m uvicorn app.main:app --reload"
Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "Set-Location '$frontend'; npm run dev"
Write-Host "RackScan is starting. Open http://127.0.0.1:3000 when the frontend says Ready." -ForegroundColor Green
