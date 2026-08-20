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

A future data model should support Site, Device, Connection, EvidenceItem, Observation, and ReviewDecision. An observation links a value to its source, confidence, observed time, and review status. Current display values are derived from accepted observations rather than overwriting history.

## Decision 4: use sample fixtures before real devices

The repository will contain a small fictional site and representative CLI/CSV inputs. They enable parser tests, UI demos, and export verification without connecting to network equipment or storing client data.

## Deferred decisions

- Authentication and multi-tenancy: after user validation.
- File/object storage: after actual uploads are introduced.
- PostgreSQL, hosting, and managed services: after the local workflow is proven.
- LLM or OCR integration: only after deterministic inputs reveal a specific gap.
