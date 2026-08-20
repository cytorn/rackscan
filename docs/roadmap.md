# RackScan delivery roadmap

## Phase 0 — foundation and decisions

Deliverables: product brief, UX direction, repository instructions, sample-data definition, and a thin architecture decision record.

Exit criteria: one supported input format and one demo site are defined; no framework or database is installed until the first implementation task is approved.

## Phase 1 — vertical-slice MVP

Build one end-to-end happy path with seeded sample data:

- create/view a site;
- manually add devices and connections;
- inventory table and device detail with evidence;
- simple logical topology;
- local persistence;
- polished loading, empty, and error states.

Exit criteria: a user can complete a demo site without file parsing or export.

Status: complete. The local workspace supports manual device and persisted manual-connection evidence, inventory inspection, evidence-backed topology, and local persistence.

## Phase 2 — evidence ingestion

- CSV inventory import;
- raw CLI text upload for one selected platform/command set;
- parser tests and fixtures;
- review queue for proposed facts, unknowns, and conflicts.

Exit criteria: sample CLI/CSV inputs reliably produce a reviewable change set.

Status: complete for the intentionally supported inputs: CSV inventory and ArubaOS-Switch `show system`. Both retain raw evidence and create a site-wide, reviewable field-observation queue.

## Phase 2.5 — evidence architecture hardening

Completed scope: persisted Site, field-level Observation history, explicit conflict resolution, persisted Connection topology, site-wide unresolved review queue, and ArubaOS-Switch parser fixtures. Existing Phase 2 device summaries are preserved and backfilled with `Legacy migration` provenance; their original per-field observed time was not available and remains explicitly unknown.

Remaining before Phase 3: proposed connection intake/review is not yet exposed because the supported CSV and CLI inputs do not extract connection evidence. Phase 3 reporting must consume only resolved Device state and accepted Connection records.

## Phase 3 — documentation output

- XLSX/CSV inventory export;
- client-ready PDF report;
- report generation tests using the demo site.

Exit criteria: demo evidence produces documentation that is useful without manual formatting.

## Phase 4 — validation with technicians

Test the workflow with 3–5 target users, record where time is lost, and prioritize only repeated pain. Avoid adding scanning, monitoring, OCR, or additional vendors until evidence supports it.

## Working budget guardrails

- One small, testable outcome per Codex task.
- Ask for an implementation plan before edits when a task affects more than a few files.
- Do not run parallel agents, large dependency upgrades, or broad rewrites by default.
- Commit at each completed phase; inspect the diff before the next task.
- Keep a small fixture-based demo site so tests and UI work do not need external devices, data, or paid APIs.
