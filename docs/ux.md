# RackScan UX direction

## Product feeling

Calm, trustworthy field-work software: clean enough for a client-facing report, but dense enough for an engineer doing real documentation. The UI should make uncertainty explicit without making the user feel punished by warnings.

## Information hierarchy

The site workspace has six stable sections:

1. Overview — status, progress, recent evidence, and attention items.
2. Inventory — authoritative device table and device detail.
3. Connections — port-aware links and unresolved endpoints.
4. Evidence — raw inputs, parsing state, and traceability.
5. Topology — a readable, focused network map.
6. Reports — export configuration and past exports.

## Primary screen: site overview

Top bar: client name, site name, audit status, last updated, and a primary **Add evidence** action.

At a glance, show four compact metrics: devices, connections, missing fields, and conflicts. The next section is an actionable "Needs review" list; it must always say what needs attention and link directly to the relevant record. Recent evidence and a small topology preview follow.

## Key interaction rules

- One obvious primary action per view; use progressive disclosure for advanced options.
- Tables support search, filters, column visibility, and a readable empty state.
- Device detail uses a field/value/evidence layout, not a wall of metadata.
- Confidence uses both a label and colour; colour never carries meaning alone.
- Use neutral styling for unknown values, amber for review, red only for confirmed conflicts/errors, and green only for verified/completed states.
- Parsing results arrive as a reviewable change set: "3 devices found, 2 connections found, 5 fields need review".
- Topology defaults to a simplified logical view; port labels appear on selection or zoom, never as permanent clutter.
- Every destructive or data-replacing action explains what will change and is recoverable where possible.

## Visual system for implementation

- Responsive web app with a desktop-first workspace and usable tablet layout for field work.
- Modern but restrained: generous spacing, 12–16px text base, high contrast, rounded panels, subtle borders, no decorative gradients competing with data.
- Use an accessible component foundation (for example, shadcn/ui + Radix primitives) after the frontend is scaffolded; do not install a visual plugin merely for styling.
- Validate keyboard navigation, visible focus, contrast, loading states, errors, empty states, and narrow-width behaviour as part of each UI slice.

## Design deliverables before coding feature screens

1. Low-fidelity flow for create-site → add-evidence → review → export.
2. One high-fidelity overview screen.
3. Inventory table and device-detail states (known, unknown, conflict).
4. A topology interaction prototype using sample data.
