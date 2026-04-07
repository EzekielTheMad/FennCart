---
phase: "01"
plan: "02"
subsystem: "frontend-shell"
tags: [templates, jinja2, htmx, tailwind, sidebar, test-infrastructure, pytest]
dependency_graph:
  requires: [01-01]
  provides: [app-shell, test-scaffold]
  affects: [01-03, 01-04]
tech_stack:
  added: []
  patterns:
    - "Jinja2 template inheritance: base.html -> pages/*.html"
    - "FastAPI APIRouter for page routes"
    - "pytest-anyio with AsyncClient + ASGITransport for async integration tests"
    - "Dependency overrides pattern: get_session, get_settings"
key_files:
  created:
    - templates/base.html
    - templates/missing_config.html
    - templates/pages/shopping.html
    - templates/pages/preferences.html
    - templates/pages/history.html
    - templates/pages/settings.html
    - app/routers/pages.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_health.py
    - pytest.ini
  modified:
    - templates/missing_config.html
decisions:
  - "SRI integrity hashes added to HTMX and Alpine.js CDN script tags (required by UI spec)"
  - "Tailwind CDN play build used without SRI (CDN play does not support SRI per spec)"
  - "pytest-anyio runs tests against both asyncio and trio backends — 2 passes per test is expected"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-02"
  tasks_completed: 2
  tasks_total: 2
  files_created: 11
---

# Phase 01 Plan 02: App Shell Templates and Test Infrastructure Summary

**One-liner:** Dark sidebar nav shell with Jinja2 template inheritance, 4 placeholder pages, missing-config error page, and pytest async test scaffold with dependency-override fixtures.

---

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create base template with nav sidebar and placeholder pages | be930ab | templates/base.html, templates/missing_config.html, templates/pages/*.html, app/routers/pages.py |
| 2 | Create test infrastructure scaffold (Wave 0) | fbad22f | tests/__init__.py, tests/conftest.py, tests/test_health.py, pytest.ini |

---

## What Was Built

### App Shell (Task 1)

`templates/base.html` provides the nav shell all pages extend:
- Left sidebar: 240px expanded on `lg:` screens, 64px icon-only on smaller viewports
- Dark theme: `bg-slate-950` page, `bg-slate-900` sidebar, `border-slate-700` divider
- 4 nav items with Heroicons inline SVGs (Shopping, Preferences, History, Settings)
- Active item: `bg-slate-800 border-l-2 border-green-500 text-slate-100`
- Inactive item: `text-slate-400 hover:bg-slate-800 hover:text-slate-100`
- WCAG touch targets: `min-h-[44px]` on all nav links
- CDN scripts: HTMX 1.9.12 with SRI, Alpine.js 3.14.8 with SRI, Tailwind play CDN

`templates/missing_config.html` — standalone full-page error (does not extend base.html):
- Page title: "FennCart -- Setup Required"
- Heading: "Container needs configuration"
- Body copy matches UI spec exactly
- `missing_vars` rendered in `bg-slate-800` code block
- Help link: "View setup instructions"

Placeholder pages follow identical pattern: extend base.html, centered content, `text-xl font-semibold` heading, `text-slate-400` body.

`app/routers/pages.py` — 5 route handlers: `/`, `/shopping`, `/preferences`, `/history`, `/settings`. Auto-registered by pre-stubbed `include_router` in `app/main.py`.

### Test Infrastructure (Task 2)

`tests/conftest.py` provides:
- `test_settings` fixture: Settings with all required fields populated (Kroger credentials, LLM key, in-memory DB URL)
- `test_db` fixture: async in-memory SQLite with SQLModel schema creation
- `client` fixture: AsyncClient with `get_session` and `get_settings` dependency overrides

`tests/test_health.py` confirms app starts and `/health` returns `{"status": "ok"}`.

---

## Verification Results

```
pytest tests/test_health.py -x -q
..
2 passed in 0.04s
```

Note: 2 passes = 1 test × 2 anyio backends (asyncio + trio). This is expected behavior with `pytest-anyio`.

---

## Deviations from Plan

None — plan executed exactly as written.

The existing `templates/missing_config.html` from Plan 01-01 used a light theme and different copy. It was updated to match the UI spec (dark theme, correct heading copy, `missing_vars` code block). This was the intended behavior (the plan listed it under `files_modified`).

---

## Known Stubs

The placeholder pages contain "coming soon" messages per the UI spec — these are intentional stubs for Phase 2:

| File | Stub | Reason |
|------|------|--------|
| templates/pages/shopping.html | "Shopping list input is coming in the next phase." | Phase 2 will replace this with the cart-building UI |
| templates/pages/preferences.html | "Preference learning is coming in a future update." | Phase 3 feature |
| templates/pages/history.html | "Your cart history will appear here after your first shopping run." | Phase 2 feature |
| templates/pages/settings.html | "Settings will be available in a future update." | Phase 4 feature |

These stubs are intentional per CONTEXT.md D-08 (full nav shell with placeholder pages). They do not prevent this plan's goals from being achieved.

---

## Self-Check: PASSED

Files exist:
- FOUND: templates/base.html
- FOUND: templates/missing_config.html
- FOUND: templates/pages/shopping.html
- FOUND: templates/pages/preferences.html
- FOUND: templates/pages/history.html
- FOUND: templates/pages/settings.html
- FOUND: app/routers/pages.py
- FOUND: tests/conftest.py
- FOUND: tests/test_health.py
- FOUND: pytest.ini

Commits exist:
- be930ab: feat(01-02): add app shell templates and pages router
- fbad22f: feat(01-02): add test infrastructure scaffold
