---
phase: 08-code-cleanup
plan: 02
subsystem: frontend/shopping-router
tags: [alpine-js, dead-code, tech-debt, refactor]
dependency_graph:
  requires: []
  provides: [stable-alpine-swap-pattern, clean-shopping-router]
  affects: [templates/partials/review_screen.html, app/routers/shopping.py]
tech_stack:
  added: []
  patterns: [alpine-state-lift, $root.updateItem]
key_files:
  created: []
  modified:
    - templates/partials/review_screen.html
    - app/routers/shopping.py
    - tests/test_shopping_flow.py
  deleted:
    - templates/partials/review_card.html
decisions:
  - Alpine state-lift via $root.updateItem is the stable replacement for _x_dataStack internal API
  - confirmedItems initialized from Jinja2 server data (review_items + auto_items loops) not from never-passed confirmed_items_json context var
  - test_swap_endpoint_removed requires app.main.get_settings patch so SetupGuardMiddleware passes through to FastAPI routing layer
metrics:
  duration_seconds: 727
  completed_date: "2026-04-07"
  tasks_completed: 2
  files_modified: 3
  files_deleted: 1
requirements: [QUAL-01, QUAL-02]
---

# Phase 08 Plan 02: Alpine State-Lift and Dead Code Removal Summary

**One-liner:** Replaced Alpine._x_dataStack internal API with $root.updateItem state-lift pattern and removed dead POST /shopping/swap endpoint with its associated template and unused imports.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite review_screen.html with Alpine state-lift pattern | 9905774 | templates/partials/review_screen.html |
| 2 | Remove /swap endpoint, delete review_card.html, clean dead imports, add tests | e4ed5a3 | app/routers/shopping.py, templates/partials/review_card.html (deleted), tests/test_shopping_flow.py |

## What Was Built

### Task 1 — Alpine State-Lift Pattern (QUAL-01)

Three changes to `templates/partials/review_screen.html`:

1. **Outer x-data rewritten**: `confirmedItems` now initialized from Jinja2 `review_items` + `auto_items` server loops. The old code used `confirmed_items_json | default('[]')` which was never passed by the `/match` endpoint, leaving confirmedItems always empty.

2. **`updateItem` signature changed**: Old signature `updateItem(upc, description, brand, size, price, quantity)` replaced with `updateItem(listItem, newUpc)` — uses `list_item` as the stable lookup key (not description, which can have special characters), updates only the `upc` field.

3. **Hidden input simplified**: The old `_x_dataStack`-based approach traversed the DOM with `document.querySelectorAll('#card-N')` and read Alpine's internal `el._x_dataStack[0].selectedUpc`. Replaced with `:value="JSON.stringify(confirmedItems)"` — reads directly from the reactive confirmedItems array kept up-to-date by `$root.updateItem()`.

4. **Card @click updated**: Each swap candidate's `@click` handler now calls `$root.updateItem('{{ item.list_item | e }}', '{{ candidate.upc }}')` to propagate the selection up to the outer scope. `$root` is a documented, stable Alpine.js 3 API (the nearest ancestor with `x-data`).

### Task 2 — Dead Code Removal (QUAL-02)

1. **`POST /shopping/swap` endpoint deleted** (lines 136-184 of shopping.py): The entire `shopping_swap` function and its decorator removed. This endpoint was superseded by the client-side Alpine state-lift pattern.

2. **`from typing import Optional` import removed**: `Optional` was only used for `matched_candidate: Optional[ProductCandidate]` inside the swap body — dies with the endpoint.

3. **`templates/partials/review_card.html` deleted**: This template was exclusively rendered by the `/swap` endpoint. Zero callers remain.

4. **Two new tests added**:
   - `test_swap_endpoint_removed`: Verifies POST /shopping/swap returns 404/405. Requires patching `app.main.get_settings` so SetupGuardMiddleware passes through to FastAPI routing.
   - `test_review_screen_no_x_datastack`: Static file check verifying `_x_dataStack` is absent and `$root.updateItem` is present.

## Verification

- `grep -r "_x_dataStack" templates/` — 0 results
- `grep -r "shopping/swap" app/ templates/` — 0 results
- `grep "from typing import Optional" app/routers/shopping.py` — no match
- `ls templates/partials/review_card.html` — not found
- `grep -c "$root.updateItem" templates/partials/review_screen.html` — 1
- `grep -c "JSON.stringify(confirmedItems)" templates/partials/review_screen.html` — 1
- `python -m pytest tests/test_shopping_flow.py -x -q` — 22 passed
- `python -m pytest tests/ -q` — 86 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] test_swap_endpoint_removed needed app.main.get_settings patch**
- **Found during:** Task 2 test run
- **Issue:** The test called `POST /shopping/swap` with only the `client` fixture. `SetupGuardMiddleware.dispatch()` calls `get_settings()` directly (bypassing FastAPI DI), and without a `get_settings` patch the middleware returned `missing_config.html` with 200 before FastAPI routing could determine the endpoint doesn't exist.
- **Fix:** Added `test_db` fixture to seed AppConfig and patched `app.main.get_settings` in the test body (same pattern as all other tests in the file), allowing the guard to pass through to FastAPI routing which then returns 404.
- **Files modified:** tests/test_shopping_flow.py
- **Commit:** e4ed5a3

## Known Stubs

None — all changes are concrete rewrites of existing functionality with no placeholder values.

## Self-Check: PASSED

- `templates/partials/review_screen.html` — file exists, contains `$root.updateItem`, `JSON.stringify(confirmedItems)`, zero `_x_dataStack`
- `app/routers/shopping.py` — syntax valid, no `shopping_swap`, no `Optional` import
- `templates/partials/review_card.html` — correctly absent
- `tests/test_shopping_flow.py` — contains `test_swap_endpoint_removed` and `test_review_screen_no_x_datastack`
- Commit 9905774 — Task 1
- Commit e4ed5a3 — Task 2
- 86 tests passing
