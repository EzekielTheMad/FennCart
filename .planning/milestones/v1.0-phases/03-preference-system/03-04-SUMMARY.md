---
phase: 03-preference-system
plan: "04"
subsystem: testing
tags: [tests, receipt-parser, preference-service, integration-tests, pref-system]
dependency_graph:
  requires: ["03-01", "03-02", "03-03"]
  provides: ["PREF-01", "PREF-02", "PREF-03", "PREF-04", "PREF-05", "PREF-06"]
  affects: []
tech_stack:
  added: []
  patterns:
    - "Mock pdfplumber at module boundary: patch('app.services.receipt_parser.pdfplumber')"
    - "Mock Instructor at module boundary: patch('app.services.receipt_parser.instructor')"
    - "Mock preference NL parse: patch('app.routers.preferences.parse_preference_nl')"
    - "Patch app.main.get_settings for middleware bypass (Kroger credential guard)"
    - "CartService preference wiring: assert match_products called with preferences kwarg not None"
key_files:
  created:
    - tests/test_receipt_parser.py
    - tests/test_preference_service.py
    - tests/test_preferences_flow.py
  modified:
    - templates/partials/pref_row.html
decisions:
  - "Mock pdfplumber at module boundary (not instance) — allows testing extract_receipt_text without a real PDF"
  - "Patch app.main.get_settings for all integration tests — SetupGuardMiddleware calls it directly, not via FastAPI DI"
  - "Use _seed_app_config helper in integration tests — wizard_complete=True required for middleware to pass"
  - "Fix pref_row.html %-d -> %d — Windows-incompatible strftime format caused ValueError in test environment"
metrics:
  duration: "~16 min"
  completed: "2026-04-06"
  tasks_completed: 2
  files_modified: 4
---

# Phase 3 Plan 4: Preference System Test Suite Summary

Complete test suite for Phase 3: unit tests for receipt parser and preference service, integration tests for all preferences HTTP endpoints, and CartService preference wiring verification.

## What Was Built

**Unit tests — receipt parser (4 tests):**
- `test_extract_receipt_text_valid_pdf` — pdfplumber returns text, empty warnings
- `test_extract_receipt_text_empty_pdf` — image-based PDF returns warning
- `test_extract_receipt_text_invalid_bytes` — non-PDF bytes returns error warning
- `test_parse_receipt_with_llm` — Instructor mock returns typed ParsedReceipt

**Unit tests — preference service (16 tests, 32 with asyncio+trio):**
- Upsert: new item creates entry, same item increments count, is_one_time skips increment
- Contradictions: count>=2 triggers, count==1 no trigger, empty brand ignored
- Preferences dict: only count>=2 returned, ordered by count DESC, capped at 50
- CRUD: create_preference (source=manual), update_preference, delete_preference, bulk_delete
- NL delta: add creates nl_chat entry, remove deletes entry, replace updates brand

**Integration tests — preferences HTTP endpoints (9 tests, 18 with asyncio+trio):**
- GET /preferences page loads with heading
- POST /preferences/upload with mock PDF returns review HTML
- POST /preferences/upload with invalid file returns error state
- Full CRUD lifecycle (create, list, update, delete)
- GET /preferences/list?q= search filtering
- POST /preferences/bulk-delete clears entries
- POST /preferences/chat clarify returns question
- POST /preferences/chat + /chat/apply saves preference to DB
- CartService.process_list auto-loads established preferences (PREF-06)

**Final test count:** 173 tests passing (116 prior + 57 new), 0 regressions.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Windows-incompatible strftime format in pref_row.html**
- **Found during:** Task 2 (test_preference_crud)
- **Issue:** `pref.last_seen_at.strftime('%b %-d, %Y')` raises ValueError on Windows — `%-d` (remove leading zero) is Linux-only strftime directive
- **Fix:** Changed `%-d` to `%d` (zero-padded day) in `templates/partials/pref_row.html`
- **Files modified:** `templates/partials/pref_row.html`
- **Commit:** b59b368

**2. [Rule 2 - Missing functionality] Added middleware patch pattern for all integration tests**
- **Found during:** Task 2 (all integration tests failing with 200 "Container needs configuration")
- **Issue:** `SetupGuardMiddleware` calls `get_settings()` directly (not via FastAPI DI), so the `client` fixture's DI override doesn't bypass credential checks
- **Fix:** Added `with patch("app.main.get_settings", return_value=_mock_settings()):` pattern to all integration test functions, following the existing pattern from `test_shopping_flow.py`
- **Files modified:** `tests/test_preferences_flow.py`
- **Commit:** b59b368

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Unit tests: receipt parser + preference service | 50d1fec | tests/test_receipt_parser.py, tests/test_preference_service.py |
| 2 | Integration tests: preferences endpoints + CartService | b59b368 | tests/test_preferences_flow.py, templates/partials/pref_row.html |

## Self-Check: PASSED
