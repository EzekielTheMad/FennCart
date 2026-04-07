---
phase: 02-core-loop
plan: "01"
subsystem: api, database
tags: [pydantic, sqlmodel, kroger-api, httpx, alembic, sqlite]

# Dependency graph
requires:
  - phase: 01-foundation-and-auth
    provides: kroger_client.py with get_app_token(), OAuthToken model, AppConfig model, SQLModel setup, aiosqlite engine
provides:
  - Shared Pydantic schemas (ParsedListItem, ProductCandidate, ItemMatch, MatchResult, ConfirmedItem) in app/schemas/shopping.py
  - CartSession SQLModel table with cart_sessions DB table
  - CartItem SQLModel table with cart_items DB table and FK to cart_sessions
  - Alembic migration 0002 creating both cart tables
  - search_products() function querying Kroger Products API with csp filter
  - add_to_cart() function calling Kroger Cart API via user OAuth token, treating 204 as success
  - 6 unit tests for search_products and add_to_cart
affects: [02-02, 02-03, 02-04, 03-preference-system]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "app/schemas/ package for Pydantic-only models separate from SQLModel table models"
    - "search_products uses filter.fulfillment=csp (lowercase) for curbside-eligible products"
    - "add_to_cart treats HTTP 204 as success — no body parsing on cart add"
    - "product search results never persisted (TOS constraint)"

key-files:
  created:
    - app/schemas/__init__.py
    - app/schemas/shopping.py
    - app/models/cart_session.py
    - app/models/cart_item.py
    - alembic/versions/0002_cart_tables.py
    - tests/test_kroger_products.py
  modified:
    - app/models/__init__.py
    - app/services/kroger_client.py

key-decisions:
  - "app/schemas/ package for shared Pydantic models separate from SQLModel table models — avoids circular imports and keeps type contracts clearly distinct from persistence layer"
  - "search_products raises RuntimeError on failure (not tuple return) — simpler caller code for a function that must succeed to proceed"
  - "add_to_cart returns (bool, str) tuple — matches existing kroger_client pattern and allows graceful 401 handling without exception propagation"

patterns-established:
  - "Pattern: schemas/shopping.py holds the full Pydantic type contract for the shopping pipeline"
  - "Pattern: test mocks patch httpx.AsyncClient at module level using unittest.mock.patch"
  - "Pattern: Alembic migrations use short hex revision IDs (0001, 0002abcd1234)"

requirements-completed: [SRCH-03, CART-02]

# Metrics
duration: ~8min
completed: 2026-04-03
---

# Phase 02 Plan 01: Data Layer and Kroger API Extensions Summary

**Shared Pydantic pipeline schemas, CartSession/CartItem SQLModel tables, and Kroger product search + cart add functions with csp filter and 204 success handling**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-03T08:20:00Z
- **Completed:** 2026-04-03T08:28:28Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Created app/schemas/shopping.py with 5 shared Pydantic models (ParsedListItem, ProductCandidate, ItemMatch, MatchResult, ConfirmedItem) that all downstream pipeline tasks depend on
- Created CartSession and CartItem SQLModel table models with correct FK relationship, added to models/__init__.py, and Alembic migration 0002 to create both tables
- Extended kroger_client.py with search_products() (filter.fulfillment=csp for curbside-only) and add_to_cart() (PUT to cart/add, 204 success, 401 expiry handling), with 6 passing unit tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Shared Pydantic schemas and SQLModel cart tables** - `8878662` (feat)
2. **Task 2: Extend kroger_client.py with search_products() and add_to_cart()** - `eb65bd4` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified

- `app/schemas/__init__.py` - Package marker for schemas module
- `app/schemas/shopping.py` - 5 Pydantic schemas for the full shopping pipeline type contract
- `app/models/cart_session.py` - CartSession SQLModel table (cart_sessions)
- `app/models/cart_item.py` - CartItem SQLModel table (cart_items) with FK to cart_sessions.id
- `app/models/__init__.py` - Updated to export CartSession and CartItem
- `alembic/versions/0002_cart_tables.py` - Migration creating cart_sessions and cart_items with downgrade
- `app/services/kroger_client.py` - Added search_products() and add_to_cart(); existing functions untouched
- `tests/test_kroger_products.py` - 6 unit tests: csp filter, data return, error handling, 204 success, 401 expiry, PUT method

## Decisions Made

- Created `app/schemas/` as a separate package from `app/models/` — keeps Pydantic-only type contracts separate from SQLModel table models to avoid circular imports as the pipeline grows
- `search_products()` raises RuntimeError on failure rather than returning a tuple — callers in the pipeline must have a valid result to proceed, so an exception is the correct failure mode
- `add_to_cart()` returns `(bool, str)` tuple matching existing kroger_client convention — allows callers to handle 401 gracefully without exception propagation

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All 5 Pydantic schemas available from `app.schemas.shopping` for LLM matching (02-02) and cart service (02-03)
- CartSession and CartItem tables ready for the cart session tracking service
- search_products() and add_to_cart() are the complete Kroger API surface needed by the core loop
- Migration 0002 links correctly to 0001 via down_revision

---
*Phase: 02-core-loop*
*Completed: 2026-04-03*
