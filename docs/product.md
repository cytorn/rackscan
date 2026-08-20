# RackScan product brief

## Product statement

RackScan turns the messy evidence collected during a network site survey into accurate, reviewable network documentation.

## Primary user

Network technicians, MSP engineers, and IT contractors documenting small and medium client sites.

## V0.1 outcome

Given manual entries, CSV inventory files, technician notes, and supported device CLI text, a technician can produce:

- a reviewable device inventory;
- a connection list and simple topology;
- a clear queue of missing data and conflicts;
- an XLSX inventory export and a client-ready PDF site report.

## Core workflow

1. Create a client site.
2. Add evidence: manual device, CSV, notes, or CLI text.
3. Parse and normalize the evidence into proposed devices and connections.
4. Review unknown fields and conflicts; accept, edit, or reject proposals.
5. Inspect inventory and topology.
6. Export documentation.

## Trust rules

- A fact is never separated from its evidence source, confidence, and observed time.
- Unknown is a valid result. The product must not invent values.
- Contradictory evidence is visible and requires a human decision.
- Deterministic parsers produce product data. AI, if added later, may explain or assist but must not become the source of truth.

## Explicitly out of scope for V0.1

- Network discovery, SNMP polling, SSH login, monitoring, alerts, remediation, or device configuration changes.
- OCR/photo extraction and advanced rack-diagram recognition.
- Multi-vendor parsing beyond the first intentionally supported CLI format.
- Billing, teams, role-based access control, and live collaboration.

## Success measures for the first usable version

- A technician can turn a small sample site into an inventory and PDF in under 15 minutes.
- Every generated device field can be traced to evidence or marked manual.
- A reviewer can identify missing or conflicting data without reading raw uploads.
