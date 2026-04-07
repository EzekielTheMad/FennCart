---
phase: 06-wire-review-mode-and-cart-history
plan: "01"
subsystem: shopping-flow, history
tags: [review-mode, cart-history, htmx, alpine, sqlite, tests]
dependency_graph:
  requires: [02-core-loop/02-01, 02-core-loop/02-02]
  provides: [SRCH-05, CART-03]
  affects: [app/routers/shopping.py, app/routers/pages.py, templates/partials/review_screen.html, templates/pages/history.html]
tech_stack:
  added: []
  patterns:
    - Alpine x-data initialized from Jinja server variable for persistent UI state
    - Jinja2 dict key access via entry['key'] to avoid shadowing built-in dict methods
    - Starlette TemplateResponse new API (request as first positional param)
key_files:
  created:
    - tests/test_phase06.py
  modified:
    - app/routers/shopping.py
    - app/routers/pages.py
    - templates/partials/review_screen.html
    - templates/pages/history.html
decisions:
  - "Use entry['session'] / entry['items'] dict access in Jinja2 — entry.items resolves to the dict .items() method, causing TypeError"
  - "Patch app.main.get_settings in history/shopping tests to bypass SetupGuardMiddleware credential check"
metrics:
  duration: ~18min
  completed: 2026-04-06T20:11:20Z
  tasks_completed: 3
  files_modified: 5
---

# Phase 06 Plan 01: Wire Review Mode and Cart History Summary

**One-liner:** Review mode toggle reads `AppConfig.review_mode` from SQLite and history page renders real `CartSession`/`CartItem` data as expandable rows with empty state.

---

## What Was Built

### Task 1 — Review mode wired from AppConfig (SRCH-05)

`shopping_match()` now extracts `cfg.review_mode` (with `"exceptions"` fallback) from the AppConfig query it was already performing. The value is passed as `review_mode` in the `TemplateResponse` context.

`review_screen.html` Alpine `x-data` changed from hardcoded `mode: 'exceptions'` to `mode: '{{ review_mode | default("exceptions") }}'`. This means a user who saved `"full"` in Settings will land on the review screen in full-review mode without needing to click the toggle.

### Task 2 — History page with real data (CART-03)

`app/routers/pages.py` history endpoint upgraded from a static render to a database query:
- Imports `CartSession`, `CartItem`, `select`
- Queries all sessions ordered `created_at DESC` (newest first)
- Loads items per session in a second query
- Passes `sessions_with_items` list and `session_count` to template

`templates/pages/history.html` replaced entirely:
- Empty state: clock Heroicon, "No shopping history yet" heading, body text, "Start shopping" CTA link to `/shopping`
- Session cards: Alpine `x-data="{ open: false }"`, click-to-expand with chevron rotation
- Expanded panel: item table with description, brand, qty, price (promo > regular > em dash)

### Task 3 — Tests (TDD green)

`tests/test_phase06.py` — 4 tests (8 with asyncio+trio backends), all passing:

| Test | Requirement | Assertion |
|------|-------------|-----------|
| `test_history_empty_state` | CART-03 | Returns 200, contains "No shopping history yet" and "Start shopping" |
| `test_history_with_sessions` | CART-03 | Returns session count, item descriptions, and formatted totals |
| `test_review_mode_full_from_db` | SRCH-05 | Alpine x-data contains `mode: 'full'` when AppConfig.review_mode="full" |
| `test_review_mode_exceptions_default` | SRCH-05 | Alpine x-data contains `mode: 'exceptions'` with default config |

Full suite: **183 tests pass**, no regressions.

---

## Commits

| Task | Hash | Message |
|------|------|---------|
| 1 | 9c88e4a | feat(06-01): wire review_mode from AppConfig into review_screen template |
| 2 | 3dca82a | feat(06-01): wire history page with real CartSession/CartItem data |
| 3 | 802be85 | test(06-01): add Phase 6 tests for review mode persistence and cart history |

---

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Jinja2 dict key access conflict with built-in method**
- **Found during:** Task 3 (test failure)
- **Issue:** Template used `entry.session` and `entry.items` — Jinja2 resolved `entry.items` to the Python `dict.items()` method, causing `TypeError: 'builtin_function_or_method' object is not iterable`
- **Fix:** Changed to `entry['session']` and `entry['items']` (bracket syntax forces key lookup, not attribute resolution)
- **Files modified:** `templates/pages/history.html`
- **Commit:** 802be85 (included in Task 3 commit)

**2. [Rule 2 - Missing critical functionality] SetupGuardMiddleware bypasses DI get_settings override**
- **Found during:** Task 3 (first test run — all tests redirected to missing_config.html)
- **Issue:** Test fixture overrides `get_settings` via FastAPI DI, but `SetupGuardMiddleware.dispatch()` calls `get_settings()` directly at line 21 of `app/main.py`, bypassing DI. Tests got the real env (no Kroger creds) and received the missing-config page.
- **Fix:** Added `patch("app.main.get_settings", return_value=_mock_settings())` context manager in all 4 history/shopping tests — matching the exact pattern used in `test_shopping_flow.py`
- **Files modified:** `tests/test_phase06.py`
- **Commit:** 802be85

**3. [Rule 1 - Bug] Starlette TemplateResponse deprecated API in history endpoint**
- **Found during:** Task 3 (deprecation warning in test output)
- **Issue:** New history endpoint used old `TemplateResponse(name, {"request": request, ...})` signature; Starlette 0.49.1 requires `request` as first positional argument
- **Fix:** Updated to `TemplateResponse(request, "pages/history.html", {...})` and removed `"request"` from context dict — consistent with project convention documented in STATE.md
- **Files modified:** `app/routers/pages.py`
- **Commit:** 802be85

---

## Known Stubs

None. Both SRCH-05 and CART-03 are fully wired to live data.

---

## Self-Check: PASSED
