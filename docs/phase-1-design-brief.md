# Phase 1 design brief

## UX decision brief

- Job: help a network technician understand a site’s documentation health and act on its device inventory.
- User mode: occasional first-time setup and returning operator review.
- Frequency/risk: occasional, reversible edits; source and confidence must remain visible because documentation errors have operational cost.
- Pattern: operational dashboard plus master/detail inventory.
- Primary action: add a device.
- Secondary actions: inspect a device, filter inventory, inspect topology, clear a filter.
- Core path: open seeded site → scan attention items → add or inspect a device → see confirmation → continue reviewing.
- Recovery path: preserve form values after validation/API errors; give a clear retry route if the API is unavailable.
- Required states: seeded partial data, loading, no results, invalid form, saved, API unavailable.
- Handoff constraints: prioritise scan speed, evidence traceability, visible focus, and useful mobile replacement over decorative dashboard cards.

## Task ergonomics contract

- Core task: review and improve the documented inventory for one site.
- User mode: technician/operator.
- Frequency/risk: occasional; edits are reversible but wrong documentation has downstream cost.
- Success metric: find an attention item or add a complete device without losing context.
- Cognitive load: current health, unknown fields, evidence source, and device facts are always visible; users should not recall them from prior screens.
- Control model: add device, inspect device, clear filter; validation preserves data and save feedback keeps the user in place.
- Speed path: site-wide search/filter and direct device inspection.
- Error prevention: required device name; clear labels and sensible defaults for optional metadata.
- Recovery: inline field error for invalid input; visible retry banner for unavailable API.
- State matrix: seeded partial site, loading shell, filtered empty, invalid form, saved, unavailable API.
- Evidence plan: create a device, trigger/fix a validation error, filter to no results, inspect a device with incomplete evidence, and use the flow by keyboard.

## Web design handoff

- Surface: responsive operational web application using Next.js and TypeScript.
- Composition: a compact top context bar, stable left navigation on wide screens, a priority stack above a dense inventory workspace.
- Typography: system sans serif for fast, familiar scanning; tabular numerals for network facts.
- Palette/material: off-white field-paper background, navy ink, graphite lines, muted teal for verified facts, amber for review, and restrained red for conflicts.
- Motif: thin circuit/signal lines connecting metrics and topology nodes; never decorative glow or generic gradient cards.
- Responsive replacement: sidebar becomes a compact site/navigation header and table rows become labelled summaries.
- Motion: only short CSS state transitions; reduced motion has no animated layout changes.
- Acceptance evidence: desktop and narrow viewport render, keyboard-visible form workflow, and API smoke test.
