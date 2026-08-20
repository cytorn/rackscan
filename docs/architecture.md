# RackScan architecture decisions

## Decision 1: begin as a local-first web application

The first vertical slice will run on the developer machine with local persistence and seeded fixtures. This keeps cost, deployment complexity, and sensitive site-data exposure low while the workflow is validated.

## Decision 2: split the frontend and domain/API layers

Planned shape:

```text
Next.js + TypeScript frontend
            |
            v
FastAPI application
  - site and inventory API
  - evidence ingestion
  - parsers
  - conflict / review service
  - report generation
            |
            v
SQLite in development -> PostgreSQL in production
```

The frontend owns interaction and presentation. The API owns validation, normalization, parsing, evidence, and export logic.

## Decision 3: evidence is first-class data

Phase 2.5 persists Site, Device, EvidenceImport, Observation, Connection, and ReviewDecision. `Device` is the resolved, current state used for fast reads. `Observation` is the field-level evidence history: it records the field, observed value, current accepted value at import, evidence import, source, confidence, observed time, and review status. A decision never deletes the observation.

When evidence matches an accepted field it is retained as accepted history. A new value for an unknown field enters the review queue. A disagreement creates a conflict and preserves both values; resolving it is an explicit review decision. Phase 2's coarse device summaries are backfilled as `Legacy migration` observations with an explicitly unknown observed time rather than fabricated provenance.

`Connection` is now a persisted, evidence-backed relationship between two device endpoints (or a documented external endpoint). The topology API derives links from accepted Connection rows; React only renders the returned topology.

`ProposedDevice` remains as a compatibility envelope for each parser row. It is not the evidence store: its fields mirror parser output while individual Observation rows carry field-level provenance.

## Decision 3.5: lightweight SQLite migration path

The Phase 2.5 startup migration uses ordered, additive SQLite changes and `SQLModel.metadata.create_all` for new tables. Existing device data is retained, then backfilled into legacy observations. This is intentionally local and dependency-free while the product validates its workflow; a versioned migration framework can replace it if schema changes become more frequent.

## Decision 4: use sample fixtures before real devices

The repository will contain a small fictional site and representative CLI/CSV inputs. They enable parser tests, UI demos, and export verification without connecting to network equipment or storing client data.

## Deferred decisions

- Authentication and multi-tenancy: after user validation.
- File/object storage: after actual uploads are introduced.
- PostgreSQL, hosting, and managed services: after the local workflow is proven.
- LLM or OCR integration: only after deterministic inputs reveal a specific gap.
- Replit deployment: Replit may run a repository-imported copy for preview or clean-environment checks, but it does not change the portable local-first architecture.
