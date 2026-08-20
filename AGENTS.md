# RackScan engineering instructions

## Product boundary

RackScan creates network documentation from site-survey evidence. It is not a monitoring platform, scanner, remote controller, or configuration manager.

## Engineering principles

- Preserve evidence source, confidence, and observed timestamp with each discovered fact.
- Unknown remains unknown. Never infer or fabricate device information.
- Surface conflicts for review; do not silently overwrite evidence.
- Keep parsing and domain logic out of presentation components.
- Prefer deterministic parsing, typed domain models, and fixture-based tests.
- Add dependencies only when their concrete benefit is documented in the change summary.

## Delivery discipline

- Work in narrow, independently verifiable slices.
- Before changes spanning multiple areas, state affected files and a short plan.
- Do not change unrelated files or reformat broadly.
- Run the relevant tests, type checks, linting, and build for the changed area when available.
- Review the final diff and report limitations or deferred work.
- Do not create background agents or install plugins/dependencies unless the task explicitly benefits from them.

## UI and UX work

- Use the local Stark resource guide in `docs/stark-resources.md` before changing RackScan UI/UX.
- Keep the visual direction aligned with `docs/design-references.md` and preserve the product boundary.
- A UI change is not complete until its desktop and narrow layouts, keyboard path, and one relevant non-happy state have been checked.

## Tool and plugin usage

Installed plugins do not authorize architectural changes. Before implementation, inspect the repository and relevant architecture documentation, determine whether an available tool applies, and use only the tools relevant to the task.

### Stark

- Stark is required for RackScan UI/UX work.
- Use it for review-queue layout, provenance and conflict presentation, interaction quality, accessibility, visual hierarchy, and responsive state design.
- Do not use Stark to make backend, parser, persistence, or domain-model decisions.
- RackScan UI priorities: evidence before aesthetics; unknowns and conflicts must remain prominent; source and confidence stay near observations; dense technician workflows must remain fast and keyboard-usable.

### Supabase

- Supabase is installed but is not part of the current architecture.
- RackScan remains SQLite and local-first unless a task explicitly authorizes an architectural migration.
- Do not introduce Supabase, hosted PostgreSQL, Supabase Auth, Supabase Storage, or cloud persistence merely because the plugin is available.

### Context7 and current documentation

- If Context7 is available in the current session, use it for materially uncertain or version-sensitive library behavior.
- Prioritize it for SQLModel/SQLAlchemy, Alembic, FastAPI, Pydantic, Next.js, React, React Flow, Playwright, and third-party dependencies.
- Prefer repository code and pinned versions first, then current official documentation, then implementation.
- Do not query documentation for ordinary logic that can be established from the repository.

### Browser verification

- If Webwright, Playwright, or equivalent browser tooling is available, use it for completed frontend workflows.
- Browser verification complements rather than replaces unit tests, backend tests, type checks, linting, and builds.
- For relevant frontend/domain work, run applicable scenarios from `docs/testing/browser-scenarios.md` and check browser console errors, an important non-happy state, and responsive layout.

### Tool availability and reporting

- At task start, distinguish tools that are available from tools actually used.
- Never claim that a plugin was used unless it was available and invoked.
- When a task materially benefits from plugins, report Stark, Context7, Webwright/Playwright, and Supabase usage or non-usage in the completion summary.
