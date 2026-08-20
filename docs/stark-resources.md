# Stark design resources

Stark is stored locally in [`tools/stark`](../tools/stark) as the project’s UI/UX design resource. It is a design-guidance plugin, not a dependency of the RackScan application.

## Required route for RackScan UI work

For dashboard, inventory, topology, responsive layout, and visual QA work:

1. Read `tools/stark/skills/ux-design/SKILL.md`.
2. Read `tools/stark/skills/web-design/SKILL.md`.
3. Read only these core references unless a specific risk demands another one:
   - `tools/stark/references/ux-patterns/task-ergonomics.md`
   - `tools/stark/references/ui-patterns/interaction-state-matrix.md`
4. Produce a short decision brief before changing UI code.
5. Validate the rendered desktop and narrow layout, keyboard path, non-happy state, and console/runtime health.

## Project constraints Stark must preserve

- RackScan is a field-audit documentation workspace, not monitoring software.
- Evidence source, confidence, observed time, unknown data, and conflicts are first-class UI information.
- Use product-specific, operational language instead of generic SaaS copy.
- Add no animation or UI library unless it has a documented job, fallback, and test plan.
- Borrow principles from the reference contract in `docs/design-references.md`; never copy trade dress or assets.

## Local package

The Stark source includes `.codex-plugin/plugin.json`. The project keeps its source as a durable, reviewable resource. If the Codex desktop plugin UI exposes a local archive import option, use the packaged archive at `tools/stark/dist/stark.zip` after it is generated; otherwise the resource routing above remains the supported project-local integration.
