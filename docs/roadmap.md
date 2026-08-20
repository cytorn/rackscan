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

## Phase 2 — evidence ingestion

- CSV inventory import;
- raw CLI text upload for one selected platform/command set;
- parser tests and fixtures;
- review queue for proposed facts, unknowns, and conflicts.

Exit criteria: sample CLI/CSV inputs reliably produce a reviewable change set.

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
