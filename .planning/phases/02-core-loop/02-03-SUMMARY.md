---
phase: 02-core-loop
plan: 03
subsystem: ui
tags: [fastapi, htmx, alpine, jinja2, cart, llm, kroger, sqlmodel]

# Dependency graph
requires:
  - phase: 02-01
    provides: kroger_client.search_products + add_to_cart, CartSession/CartItem models, shopping schemas
  - phase: 02-02
    provides: llm_service.parse_shopping_list + match_products, MatchResult/ItemMatch schemas

provides:
  - CartService orchestrating full parse->search->match->add pipeline with in-memory dedup
  - Shopping router with 5 endpoints covering the entire list-to-cart HTMX flow
  - 7 Jinja2 templates implementing every UI screen from the UI-SPEC
  - Full end-to-end shopping flow wired: list input -> live preview -> LLM match -> review -> cart add -> success

affects:
  - phase-03-preference-system (CartService.process_list accepts preferences= hook)
  - phase-04-settings (shopping router uses get_settings() for LLM and Kroger credentials)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "HTMX + Alpine.js hybrid UI: HTMX handles server requests/swaps; Alpine manages client-side state (text binding, toggle mode, swap dropdowns)"
    - "In-memory search_cache per CartService instance deduplicates Kroger API calls within a session (TOS-safe)"
    - "Server-side session (Starlette) persists match_data + candidates across /match -> /swap -> /add-to-cart request chain"
    - "CartService instantiates Jinja2Templates locally (same as pages.py) to avoid circular imports from app.main"
    - "Sticky confirm bar uses fixed positioning offset from sidebar width (left-16 lg:left-60)"

key-files:
  created:
    - app/services/cart_service.py
    - app/routers/shopping.py
    - templates/partials/list_preview.html
    - templates/partials/review_screen.html
    - templates/partials/success_screen.html
    - templates/partials/loading_spinner.html
    - templates/partials/error_block.html
    - templates/partials/review_card.html
  modified:
    - templates/pages/shopping.html (replaced placeholder with full input UI)
    - app/main.py (added shopping router include)

key-decisions:
  - "CartService instantiates Jinja2Templates locally, not imported from app.main — avoids circular import (pages.py pattern)"
  - "ConfirmedItem uses .price field (not .price_regular) — schema defined in Plan 01 with price not price_regular"
  - "AppConfig.store_id used for location_id (not store_location_id — plan had incorrect field name)"
  - "review_card.html added as 7th template — needed by /shopping/swap endpoint to render swapped card"
  - "Pre-existing text-xs violations in setup/ templates are out of scope (Phase 1 artifacts, not Phase 2)"

patterns-established:
  - "Pattern A: Router-local Jinja2Templates — each router instantiates its own instance to avoid main.py circular import"
  - "Pattern B: Session-persisted match state — match_data + candidates stored in Starlette session for multi-step HTMX flow"
  - "Pattern C: Confidence-based partition — 0.8 threshold splits items into review cards vs auto-matched table"

requirements-completed: [SRCH-01, SRCH-04, SRCH-05, CART-01, CART-02, CART-03]

# Metrics
duration: 6min
completed: 2026-04-03
---

# Phase 02 Plan 03: Cart Service + Shopping UI Summary

**CartService orchestrates parse->search->match->add pipeline; 5-endpoint shopping router and 7 Jinja2 templates implement the complete list-to-cart HTMX flow per UI-SPEC.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-04-03T08:33:34Z
- **Completed:** 2026-04-03T08:38:58Z
- **Tasks:** 3 completed
- **Files modified:** 10 (8 created, 2 modified)

## Accomplishments

- CartService wires together kroger_client + llm_service into a clean orchestration layer with 0.8 confidence threshold partition, in-memory search dedup (TOS), and SQLite cart persistence
- Shopping router delivers all 5 endpoints: GET page, POST preview (fast regex), POST match (full LLM pipeline), POST swap (Alpine dropdown), POST add-to-cart (Kroger + SQLite)
- All 7 templates implement exact UI-SPEC classes, copy, and interaction patterns: hybrid review (cards + table), review mode toggle, sticky confirm bar, success screen with expandable detail

## Task Commits

1. **Task 1: CartService orchestration layer** - `6228d21` (feat)
2. **Task 2: Shopping router with all endpoints** - `0bfb014` (feat)
3. **Task 3: All Jinja2 templates for the shopping flow** - `b078d1e` (feat)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Circular import: shopping.py importing from app.main**
- **Found during:** Task 2
- **Issue:** `from app.main import templates` in shopping.py caused circular import because app.main imports app.routers.shopping
- **Fix:** Router instantiates its own `Jinja2Templates(directory="templates")` — same pattern used by pages.py
- **Files modified:** app/routers/shopping.py
- **Commit:** 0bfb014

**2. [Rule 1 - Bug] ConfirmedItem schema uses .price not .price_regular**
- **Found during:** Task 1 (reading actual schema)
- **Issue:** Plan specified `item.price_regular` but app/schemas/shopping.py defines the field as `price`
- **Fix:** Used `item.price` throughout CartService.add_confirmed_to_cart and success_screen.html
- **Files modified:** app/services/cart_service.py, templates/partials/success_screen.html
- **Commit:** 6228d21

**3. [Rule 1 - Bug] AppConfig has store_id not store_location_id**
- **Found during:** Task 2 (reading app/models/config_model.py)
- **Issue:** Plan referenced `cfg.store_location_id` but the actual model field is `store_id`
- **Fix:** Used `cfg.store_id` in shopping router
- **Files modified:** app/routers/shopping.py
- **Commit:** 0bfb014

**4. [Rule 2 - Missing] review_card.html template not listed in plan but required by /shopping/swap**
- **Found during:** Task 3
- **Issue:** Plan's /swap endpoint renders `partials/review_card.html` but plan task list only specified 6 templates
- **Fix:** Created review_card.html as 7th template for swap endpoint responses
- **Files modified:** templates/partials/review_card.html (created)
- **Commit:** b078d1e

## Files Created/Modified

- `app/services/cart_service.py` — CartService with process_list, partition_matches, add_confirmed_to_cart, get_session_items, _to_candidate
- `app/routers/shopping.py` — 5 shopping endpoints + _quick_parse helper
- `app/main.py` — Added shopping router try/except include
- `templates/pages/shopping.html` — Full list input UI replacing placeholder
- `templates/partials/list_preview.html` — HTMX live preview pills
- `templates/partials/review_screen.html` — Hybrid cards+table review with Alpine mode toggle and sticky confirm bar
- `templates/partials/success_screen.html` — Post-add success with expandable item detail
- `templates/partials/loading_spinner.html` — Reusable animate-spin spinner
- `templates/partials/error_block.html` — Reusable error container with HTMX retry
- `templates/partials/review_card.html` — Single product card for swap responses

## Known Stubs

None — all data flows are wired. The `preferences=None` parameter in CartService.process_list is an intentional Phase 3 hook (D-07), not a UI-visible stub.

## Self-Check: PASSED
