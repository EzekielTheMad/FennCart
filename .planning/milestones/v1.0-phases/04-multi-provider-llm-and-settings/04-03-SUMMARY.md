---
phase: 04-multi-provider-llm-and-settings
plan: 03
subsystem: tests
tags: [pytest, unit-tests, integration-tests, llm, settings, fernet, ollama, htmx]

# Dependency graph
requires:
  - phase: 04-multi-provider-llm-and-settings
    plan: 01
    provides: get_active_llm_config(), AppConfig with llm_api_key_encrypted/llm_ollama_base_url/review_mode, Fernet encryption
  - phase: 04-multi-provider-llm-and-settings
    plan: 02
    provides: settings router (6 endpoints), settings templates

provides:
  - Unit tests for get_active_llm_config() (env fallback, DB read, Fernet decrypt, Ollama)
  - Integration tests for all settings endpoints (page render, section switching, LLM save/error, Ollama config, blank-key preservation, store search/select, preferences save, hot-swap proof)
  - Full test suite green at 116 tests

affects:
  - Phase 05 (hardening): test patterns established for regression-proofing settings

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "patch(app.main.get_settings): bypasses SetupGuardMiddleware in integration tests (same pattern as test_shopping_flow.py)"
    - "Fernet test isolation: generate test key at module level, patch get_or_create_fernet in all three module paths (oauth_manager, routers.settings, services.llm_config)"
    - "DB seeding helper: _seed_config(db, **overrides) creates AppConfig id=1 with wizard_complete=True for integration test isolation"

key-files:
  created:
    - tests/test_llm_config.py
    - tests/test_settings.py
  modified: []

key-decisions:
  - "patch app.main.get_settings (not app.config.get_settings) to bypass SetupGuardMiddleware — middleware calls get_settings() directly, not via DI"
  - "Fernet patched in three separate module namespaces: oauth_manager, routers.settings, services.llm_config — each imports get_or_create_fernet independently"
  - "anyio dual-backend (asyncio + trio) auto-runs all @pytest.mark.anyio tests twice — 17 logical tests become 34 collected items"

patterns-established:
  - "Settings integration test pattern: seed DB -> patch app.main.get_settings -> patch external services -> assert response + DB state"

requirements-completed:
  - LLM-02

# Metrics
duration: 14min
completed: 2026-04-06
---

# Phase 4 Plan 3: Settings Test Suite Summary

**34 tests (4 unit + 13 integration x 2 backends) proving get_active_llm_config() DB-first hot-swap, Fernet decrypt, and all 6 settings endpoints — full suite green at 116 tests**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-04-06T00:06:48Z
- **Completed:** 2026-04-06T00:21:00Z
- **Tasks:** 1
- **Files modified:** 0 (2 created)

## Accomplishments

- Created `tests/test_llm_config.py` with 4 unit tests for `get_active_llm_config()`: env fallback (no DB row), DB read with no encrypted key (env key fallback), Fernet-encrypted key decryption, and Ollama base_url threading
- Created `tests/test_settings.py` with 13 integration tests: settings page render, all 4 section partial GET requests, LLM save success, LLM save failure (key preserved), Ollama config, blank api_key key preservation, store search, store select (wizard_step invariant), preferences save, and hot-swap proof
- Identified and applied correct mock pattern: `patch("app.main.get_settings")` bypasses `SetupGuardMiddleware` (middleware calls `get_settings()` directly, bypassing FastAPI DI overrides)
- All 116 tests pass (82 pre-existing + 34 new; anyio runs each test on both asyncio and trio backends)

## Task Commits

1. **Task 1: Unit tests for get_active_llm_config() and integration tests for all settings endpoints** - `38dc42e` (test)

## Files Created/Modified

- `tests/test_llm_config.py` - New: 4 unit tests for get_active_llm_config() with Fernet and env fallback coverage
- `tests/test_settings.py` - New: 13 integration tests for all /settings/* endpoints

## Decisions Made

- `patch("app.main.get_settings", ...)` is the correct bypass for `SetupGuardMiddleware` — the middleware reads `get_settings()` at the module level, not via FastAPI DI. The `app.dependency_overrides[get_settings]` pattern in conftest only applies to router handlers, not middleware.
- Fernet must be patched in three separate module namespaces: `app.services.oauth_manager.get_or_create_fernet`, `app.routers.settings.get_or_create_fernet`, and `app.services.llm_config.get_or_create_fernet` — each module imports the function independently, so a single patch at the source doesn't propagate.
- anyio dual-backend mode (asyncio + trio) doubles test collection: 17 logical tests become 34 collected items. This is expected pytest-anyio behavior.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added patch("app.main.get_settings") to bypass SetupGuardMiddleware**
- **Found during:** Task 1 (first test run)
- **Issue:** All settings integration tests returned 200 with the "Container needs configuration" HTML instead of the expected settings page. The SetupGuardMiddleware reads `get_settings()` directly (not via FastAPI DI), so `app.dependency_overrides[get_settings]` in conftest doesn't affect it. The shopping flow tests (test_shopping_flow.py) already use `patch("app.main.get_settings")` for this reason — this pattern needed to be applied to settings tests too.
- **Fix:** Added `with patch("app.main.get_settings", return_value=_mock_settings())` wrapping all HTTP client calls in integration tests
- **Files modified:** tests/test_settings.py
- **Verification:** All 34 new tests pass; full 116-test suite green
- **Committed in:** 38dc42e (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug — wrong patch target for middleware bypass)
**Impact on plan:** No scope change — discovered the correct mock target from test_shopping_flow.py precedent.

## Issues Encountered

None beyond the middleware patch target issue documented above.

## User Setup Required

None.

## Known Stubs

None — test files contain no stubs. All assertions are concrete.

## Next Phase Readiness

- LLM-02 now has comprehensive test coverage: unit tests prove the DB-first hot-swap path, integration tests prove the full settings UI round-trip
- Phase 05 (hardening) can extend these test files with additional edge cases or regression tests
- The `_seed_config()` helper and `_mock_settings()` pattern are reusable for any future settings-adjacent tests

## Self-Check: PASSED

- tests/test_llm_config.py: FOUND
- tests/test_settings.py: FOUND
- 04-03-SUMMARY.md: FOUND
- Commit 38dc42e: FOUND

---
*Phase: 04-multi-provider-llm-and-settings*
*Completed: 2026-04-06*
