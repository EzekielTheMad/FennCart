---
phase: 07-llm-config-integration-fix
plan: "01"
subsystem: preferences
tags: [llm-config, preferences, tdd, db-authoritative]
dependency_graph:
  requires:
    - app/services/llm_config.py (get_active_llm_config)
  provides:
    - DB-authoritative LLM config in upload_receipt and preference_chat
  affects:
    - app/routers/preferences.py
    - tests/test_preferences_flow.py
tech_stack:
  added: []
  patterns:
    - DB-authoritative LLM config via get_active_llm_config(db) — matches shopping.py pattern
key_files:
  modified:
    - app/routers/preferences.py
    - tests/test_preferences_flow.py
decisions:
  - Kept `from app.config import get_settings` module-level import intact (other infrastructure depends on it)
  - Did NOT add ollama_base_url to parse_receipt_with_llm or parse_preference_nl signatures (neither accepts it)
metrics:
  duration: "~8min"
  completed: "2026-04-06"
  tasks_completed: 2
  files_modified: 2
---

# Phase 07 Plan 01: LLM Config Integration Fix Summary

**One-liner:** Wired receipt upload and NL chat to use DB-authoritative LLM config via get_active_llm_config(db), matching the shopping router pattern established in Phase 4.

## What Was Built

Two LLM call sites in `app/routers/preferences.py` that previously read `settings.llm_*` env vars directly now use `get_active_llm_config(db)`, which reads from AppConfig in the database with a fallback to env vars. This makes the user's LLM provider selection in Settings take effect across all three LLM-using features: shopping, receipt upload, and NL preference chat.

Two integration tests prove the DB config is authoritative — they seed AppConfig with `provider="openai"`, `model="gpt-4o"` (different from the env default `"anthropic"`/`"claude-3-haiku-20240307"`) and assert those DB values reach the LLM service functions.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add integration tests proving DB LLM config is used (TDD RED) | 88f1b74 | tests/test_preferences_flow.py |
| 2 | Wire preferences.py to use get_active_llm_config(db) (TDD GREEN) | 7956ddb | app/routers/preferences.py |

## Changes Made

### app/routers/preferences.py

- Added `from app.services.llm_config import get_active_llm_config` import
- In `upload_receipt()`: replaced `settings = get_settings()` + `settings.llm_*` with `llm_cfg = await get_active_llm_config(db)` + `llm_cfg["api_key/provider/model"]`
- In `preference_chat()`: same replacement as above

### tests/test_preferences_flow.py

- Added `_seed_app_config_custom(db, provider, model)` helper for seeding AppConfig with custom LLM values
- Added `test_upload_receipt_uses_db_llm_config`: patches extract + parse mocks, asserts provider/model positional args match DB values not env defaults
- Added `test_nl_chat_uses_db_llm_config`: patches parse_preference_nl mock, asserts provider/model args match DB values

## Verification

```
grep -n "get_active_llm_config" app/routers/preferences.py
# 14: import
# 211: upload_receipt call site
# 411: preference_chat call site

grep -n "settings.llm_" app/routers/preferences.py
# (no matches)

python -m pytest tests/test_preferences_flow.py -x -q
# 22 passed

python -m pytest tests/ -x -q
# 187 passed, 0 regressions
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Extracted receipt text too short for LLM guard**
- **Found during:** Task 1 (TDD RED verification)
- **Issue:** The plan's example receipt text "FRYS STORE #123\nItem1 $5.00\nTOTAL $5.00" is 38 chars — below the 50-char guard in upload_receipt, causing the endpoint to return early before calling parse_receipt_with_llm. Mock was called 0 times instead of asserting wrong provider.
- **Fix:** Expanded the mocked receipt text to a realistic multi-line receipt exceeding 50 chars
- **Files modified:** tests/test_preferences_flow.py
- **Commit:** 88f1b74 (same task commit)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Keep `from app.config import get_settings` module-level import | Other code paths and test infrastructure reference it; removing it would break SetupGuardMiddleware tests |
| No ollama_base_url in parse_receipt_with_llm/parse_preference_nl | Those functions don't accept the param; shopping.py pattern passes it to CartService which handles provider routing |

## Known Stubs

None — both call sites are fully wired to DB config.

## Self-Check: PASSED

- [x] `app/routers/preferences.py` exists and contains get_active_llm_config import + 2 call sites
- [x] `tests/test_preferences_flow.py` contains test_upload_receipt_uses_db_llm_config and test_nl_chat_uses_db_llm_config
- [x] Commit 88f1b74 exists (Task 1)
- [x] Commit 7956ddb exists (Task 2)
- [x] 187 tests pass, 0 regressions
