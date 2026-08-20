# RackScan design reference contract

These references influence design principles only. RackScan must not copy their branding, copywriting, assets, layouts, or interaction choreography.

## Auros: editorial confidence for technical information

Borrow:

- strong typography, deliberate whitespace, and a clear point of view;
- a restrained palette with one meaningful accent rather than generic SaaS gradients;
- large, meaningful metrics that orient the user before detail;
- calm, high-trust composition.

Apply to RackScan:

- site health is the opening story: device count, connection count, unknown fields, and conflicts;
- use an evidence/signal-line motif and clean, utility-led materials;
- keep the dashboard quiet enough for dense operational work.

Do not apply:

- marketing-page scale, cinematic image treatments, crypto visual language, or speculative performance claims.

## Oryzo: distinctive technical storytelling

Borrow:

- small, purposeful details that make technical information memorable;
- one intentional visual motif carried through the experience;
- product-specific labels and explanatory microcopy;
- progressive disclosure that rewards inspection.

Apply to RackScan:

- topology and evidence can use subtle signal paths, concise provenance labels, and a tactile field-notebook feel;
- unknown, review, and conflict states should feel informative—not like generic error banners;
- motion, if added, must show a relationship or state change, with a reduced-motion fallback.

Do not apply:

- parody, fake AI claims, scroll-driven spectacle, or animations that slow a technician’s work.

## Auvik: task patterns, not product scope

Borrow:

- map/inventory/detail as linked ways to inspect the same network;
- fast search and filters for finding a device;
- device-level facts and relationship context;
- documentation as an operational artifact, not merely a table export.

RackScan V0.1 remains limited to:

- manually entered evidence, CSV, notes, and supported CLI text;
- device inventory, connections, provenance/confidence, unknowns, conflicts, topology, and exports;
- human review before documentation is accepted.

Explicitly excluded:

- SNMP or SSH discovery, network scanning, continuous monitoring, alerting, traffic analysis, remote device access, configuration backup, remediation, or live topology updates.

## Acceptance criteria for future UI work

- The first viewport explains documentation health and the next human action.
- Every visual state has a functional meaning; no decorative metric, button, or topology link.
- Inventory, topology, and device detail preserve the same evidence and confidence context.
- Desktop supports scan speed; mobile preserves priority and tap targets rather than squeezing the desktop table.
- Visual novelty is subordinate to usability, accessibility, evidence traceability, and performance.
