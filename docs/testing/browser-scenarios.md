# RackScan browser scenarios

Run the applicable scenarios with available browser tooling after frontend or domain changes. These scenarios complement API and parser tests.

## RS-E2E-001 — Manually add a device

1. Open a site overview.
2. Add a device through the manual-evidence form.
3. Confirm its evidence source is visible in inventory and the evidence inspector.
4. Reload and confirm persistence.

## RS-E2E-002 — Import CSV and accept a proposed device

1. Open the Evidence workspace.
2. Import a valid CSV containing a new device.
3. Confirm the proposal shows source, confidence, raw row, and review state.
4. Accept the proposal.
5. Confirm the device appears in accepted inventory after reload.

## RS-E2E-003 — Import supported CLI text

1. Paste valid ArubaOS-Switch `show system` output.
2. Confirm the proposed values and provenance are displayed.
3. Confirm unsupported platform, command, or invalid text receives a clear error without changing inventory.

## RS-E2E-004 — Preserve a conflict

1. Import evidence for an existing device name.
2. Confirm it is identified as a conflict.
3. Confirm accepted inventory is unchanged.
4. Reject the conflicting proposal and confirm it remains traceable as rejected.

## RS-E2E-005 — Review queue states

1. Exercise loading, empty, and error states in the Evidence workspace.
2. Use keyboard navigation for intake and proposal actions.
3. Verify narrow layout preserves controls, source, confidence, and conflict visibility.

## RS-E2E-006 — Persisted topology

1. Open the site topology after a persisted inventory change.
2. Confirm only evidence-backed relationships are drawn.
3. Confirm unresolved/conflicting devices are not placed on inferred links.
