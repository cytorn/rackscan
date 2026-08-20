# RackScan

RackScan turns network site-survey evidence into reviewable network documentation. It preserves evidence and uncertainty instead of inventing missing facts.

## Phase 1: local vertical slice

The current slice provides a seeded Petaling Jaya office workspace with:

- site-health overview and attention queue;
- searchable, filterable device inventory;
- evidence/confidence-aware device inspector;
- simple logical topology preview;
- manual device creation stored in local SQLite;
- FastAPI tests and a responsive Next.js interface.

## Phase 2: evidence ingestion

The first ingestion slice accepts CSV inventory evidence through `POST /api/sites/pj-office/evidence/csv`. It stores the raw CSV and each source row as a proposal; it never overwrites the accepted inventory. Supported columns are `name` (required), `device_type`, `brand`, `model`, `ip_address`, and `serial_number`.

Existing device names are flagged as `conflict`; new or duplicate-in-file names are marked for `review`. The Evidence workspace supports accepting a non-conflicting proposal into inventory or rejecting it; accepted devices retain the import source and confidence. Conflicts cannot overwrite accepted facts.

The one supported CLI input is ArubaOS-Switch `show system`. It deterministically reads `System Name`, `System Description`, `Serial Number`, and `IP Address` into a reviewable proposal. Other platforms and commands remain unsupported.

Automatic topology extraction, exports, authentication, and external services remain deferred.

## Run locally

Open two terminals from the repository root after restarting Codex/your terminal once:

```powershell
cd backend
.\.venv\Scripts\python -m uvicorn app.main:app --reload
```

```powershell
cd frontend
npm run dev
```

Open [http://127.0.0.1:3000](http://127.0.0.1:3000). The API docs are at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

## Secondary preview environments

The repository remains the portable source of truth; Replit may be used to run or preview an imported Git branch. SQLite stays local to the runtime. If the frontend and API use different origins, set `NEXT_PUBLIC_API_URL` to the API origin when building the frontend and set `RACKSCAN_CORS_ORIGINS` to a comma-separated allow-list including the frontend origin. No Replit-specific dependency or domain logic is required.

## Verify

```powershell
cd backend
.\.venv\Scripts\python -m pytest

cd ..\frontend
npm run lint
npm run build
```

## Dependencies

- Next.js/React: responsive web interface and local development tooling.
- FastAPI/SQLModel: typed local API and SQLite persistence, kept separate from presentation logic.
- pytest/httpx: API behaviour checks.

No LLM, paid API, cloud service, plugin runtime, scanner, or network-device connection is used in Phase 1.
