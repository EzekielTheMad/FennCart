---
phase: 02-core-loop
plan: 04
subsystem: testing
tags: [pytest, anyio, unittest.mock, cart_service, shopping_flow, htmx, sqlite]

# Dependency graph
requires:
  - phase: 02-core-loop plan 03
    provides: CartService, shopping router, review/success templates

provides:
  - Unit tests for CartService (confidence partitioning, pipeline, persistence)
  - Integration tests for all /shopping/* HTTP endpoints
  - Full requirement coverage: SRCH-01 through CART-03 and LLM-01

affects: [03-preference-system, future phases requiring test patterns]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "CartService unit tests mock at module level (app.services.cart_service.*)"
    - "Shopping router integration tests seed AppConfig + mock external services"
    - "get_valid_access_token patched at app.routers.shopping to control token state"
    - "Both asyncio and trio backends run automatically via anyio pytest config"

key-files:
  created:
    - tests/test_cart_service.py
    - tests/test_shopping_flow.py
  modified: []

key-decisions:
  - "Mock at module boundary (app.services.cart_service.search_products) not at import path"
  - "Seed AppConfig with wizard_complete=True before shopping endpoint tests (middleware guard)"
  - "patch app.routers.shopping.get_valid_access_token to test expired-token path cleanly"

patterns-established:
  - "CartService unit tests: all 7 async tests use @pytest.mark.anyio + test_db fixture"
  - "Integration tests: seed DB via _seed_app_config helper, patch settings via app.main.get_settings"
  - "ConfirmedItem JSON serialized as string for form submission (confirmed_items_json field)"

requirements-completed: [SRCH-01, SRCH-02, SRCH-03, SRCH-04, SRCH-05, CART-01, CART-02, CART-03, LLM-01]

# Metrics
duration: 15min
completed: 2026-04-03
---

# Phase 2 Plan 04: Test Suite Summary

**82 passing tests covering all 9 Phase 2 requirements — CartService unit tests with mocked externals and shopping flow HTTP integration tests**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-03T00:00:00Z
- **Completed:** 2026-04-03T00:15:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- 8 CartService unit tests: confidence partitioning at 0.8 threshold (SRCH-04), pipeline orchestration (SRCH-02), search deduplication, cart persistence with local shadow (CART-02, CART-03)
- 9 shopping flow integration tests covering all 5 endpoints: GET /shopping (SRCH-01), POST /preview (SRCH-01), POST /match (SRCH-02, SRCH-04, SRCH-05), POST /add-to-cart (CART-01, CART-03), expired token path
- Full test suite green: 82 tests passing including all Phase 1 tests (no regressions)
- All 9 Phase 2 requirement IDs (SRCH-01 through CART-03, LLM-01) have at least one passing test

## Task Commits

Each task was committed atomically:

1. **Task 1: CartService unit tests** - `8569d3a` (test)
2. **Task 2: Shopping flow integration tests** - `85a799c` (test)

## Files Created/Modified
- `tests/test_cart_service.py` - 8 unit tests for CartService: confidence partitioning, pipeline calls, dedup, persistence, failure handling, session retrieval, candidate extraction
- `tests/test_shopping_flow.py` - 9 integration tests for /shopping/* endpoints with mocked externals

## Decisions Made
- Patched `app.services.cart_service.*` at the module level (search_products, parse_shopping_list, match_products, add_to_cart) so unit tests isolate CartService logic without hitting real Kroger or LLM APIs
- Patched `app.routers.shopping.get_valid_access_token` directly (not at oauth_manager) to control the token path independently per test
- `_seed_app_config` helper seeds AppConfig with wizard_complete=True so setup guard middleware passes and /shopping endpoints respond normally

## Deviations from Plan

None - plan executed exactly as written. Added one extra test (`test_to_candidate_handles_missing_fields`) beyond the 7 planned to cover the defensive `_to_candidate` code path; this is additive and does not conflict with any requirement.

## Issues Encountered
None. All tests passed on first run.

## Known Stubs
None — this plan creates tests only (no UI or service stubs).

## Next Phase Readiness
- Phase 2 core loop is fully tested and green
- CartService.process_list accepts `preferences=None` hook ready for Phase 3 preference system
- Phase 3 (Preference System) can build on the same test patterns established here

---
*Phase: 02-core-loop*
*Completed: 2026-04-03*
