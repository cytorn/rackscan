# RackScan

RackScan turns site-survey evidence into reviewable network documentation. It keeps source, confidence, time observed, unknown values, and conflicts visible instead of guessing.

## Start here

### First time only

1. Install [Python 3.13+](https://www.python.org/downloads/) and [Node.js 20+](https://nodejs.org/).
2. Open PowerShell in this project folder.
3. Run:

```powershell
.\Setup-RackScan.ps1
```

### Every time you want to use RackScan

```powershell
.\Start-RackScan.ps1
```

Two PowerShell windows open: one for the API and one for the web app. Keep them open while using RackScan, then open [http://127.0.0.1:3000](http://127.0.0.1:3000).

## What you can do

- Review a seeded site workspace and evidence-backed topology.
- Add devices and manually record observed network connections.
- Import CSV inventory evidence with `name`, `device_type`, `brand`, `model`, `ip_address`, and `serial_number` columns.
- Paste ArubaOS-Switch `show system` output.
- Review, accept, reject, or explicitly resolve field-level conflicts.

RackScan is local-first. It does not scan networks, connect to devices, monitor traffic, change configurations, or use a cloud database.

## Troubleshooting

- **“Not set up yet”** — run `./Setup-RackScan.ps1` once.
- **Port already in use** — close older RackScan PowerShell windows, then launch again.
- **Cannot reach the API** — wait for the API window to show that Uvicorn is running, then refresh the browser.

## Developer checks

```powershell
cd backend
.\.venv\Scripts\python -m pytest

cd ..\frontend
npm run lint
npm run build
```

## Secondary preview environments

Git remains the source of truth. Replit can run an imported branch as a secondary preview environment, but it does not change RackScan’s local-first architecture. If the frontend and API use different origins, set `NEXT_PUBLIC_API_URL` and `RACKSCAN_CORS_ORIGINS` for those origins.
