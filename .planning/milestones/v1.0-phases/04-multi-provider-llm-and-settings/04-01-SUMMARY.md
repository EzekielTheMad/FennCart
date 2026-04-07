---
phase: 04-multi-provider-llm-and-settings
plan: 01
subsystem: api
tags: [litellm, instructor, sqlite, alembic, fernet, ollama, llm]

# Dependency graph
requires:
  - phase: 02-core-loop
    provides: CartService, llm_service (parse_shopping_list, match_products, test_connection)
  - phase: 01-foundation-and-auth
    provides: AppConfig model, Alembic migrations, Fernet encryption via oauth_manager

provides:
  - AppConfig with llm_api_key_encrypted, llm_ollama_base_url, review_mode columns
  - Alembic migration 0003 adding LLM settings columns to app_config table
  - get_active_llm_config() service reading DB-authoritative LLM config with Fernet decrypt
  - test_connection(), parse_shopping_list(), match_products() all support Ollama via base_url param
  - CartService accepts llm_ollama_base_url and threads it through process_list()
  - shopping_match and shopping_add_to_cart read LLM config from DB (no more lru_cache for LLM fields)

affects:
  - 04-02 (settings page writes llm_api_key_encrypted, llm_provider, llm_model, llm_ollama_base_url to AppConfig)
  - 04-03 (wizard LLM setup step reads/writes same columns)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - DB-authoritative config read: get_active_llm_config() reads from AppConfig at request time, bypasses lru_cache
    - Fernet reuse: same get_or_create_fernet() from oauth_manager used for LLM API key encryption
    - base_url threading: Ollama endpoint URL threaded from router -> CartService -> llm_service as api_base kwarg

key-files:
  created:
    - app/services/llm_config.py
    - alembic/versions/0003_add_llm_settings_columns.py
  modified:
    - app/models/config_model.py
    - app/services/llm_service.py
    - app/services/cart_service.py
    - app/routers/shopping.py

key-decisions:
  - "get_active_llm_config() always queries DB first; falls back to env Settings when no DB row or llm_provider not set"
  - "CartService gets llm_ollama_base_url param to thread Ollama base URL through to llm_service — not just the router"
  - "api_key omitted from litellm/instructor calls when base_url present (Ollama has no API key requirement)"

patterns-established:
  - "DB-authoritative hot-swap: write to AppConfig -> next request picks up new LLM config without restart"
  - "Fernet decrypt pattern for stored secrets: cfg.llm_api_key_encrypted -> f.decrypt().decode(), fallback to env on exception"

requirements-completed:
  - LLM-02

# Metrics
duration: 8min
completed: 2026-04-05
---

# Phase 4 Plan 1: LLM Backend Foundation Summary

**DB-authoritative LLM hot-swap foundation: extended AppConfig with encrypted API key storage, Alembic migration 0003, get_active_llm_config() service with Fernet decrypt, and Ollama base_url threading through the full shopping pipeline**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-05T23:40:05Z
- **Completed:** 2026-04-05T23:48:00Z
- **Tasks:** 2
- **Files modified:** 5 (plus 2 created)

## Accomplishments

- Extended AppConfig model with `llm_api_key_encrypted`, `llm_ollama_base_url`, and `review_mode` columns
- Created Alembic migration 0003 to add the three new columns to the existing `app_config` table
- Built `get_active_llm_config()` service: reads from AppConfig at request time (bypassing lru_cache), Fernet-decrypts stored API key, falls back to env Settings
- Added `base_url: Optional[str] = None` to `test_connection()`, `parse_shopping_list()`, and `match_products()` for Ollama support
- Threaded `llm_ollama_base_url` through `CartService.__init__` and `process_list()` so Ollama works end-to-end
- Updated both `shopping_match` and `shopping_add_to_cart` to read LLM config from DB via `get_active_llm_config()`
- All 82 existing tests remain green

## Task Commits

1. **Task 1: Extend AppConfig model, Alembic migration, get_active_llm_config()** - `66147c5` (feat)
2. **Task 2: Ollama base_url support in LLM service + shopping router DB reads** - `d6466c0` (feat)

## Files Created/Modified

- `app/models/config_model.py` - Added llm_api_key_encrypted, llm_ollama_base_url, review_mode fields
- `alembic/versions/0003_add_llm_settings_columns.py` - Migration adding 3 columns to app_config
- `app/services/llm_config.py` - New: DB-authoritative LLM config reader with Fernet decrypt and env fallback
- `app/services/llm_service.py` - Added base_url param to test_connection, parse_shopping_list, match_products
- `app/services/cart_service.py` - Added llm_ollama_base_url param, threads through process_list()
- `app/routers/shopping.py` - Replaced settings.llm_* reads with get_active_llm_config() in both handlers

## Decisions Made

- `get_active_llm_config()` always DB-first: reads AppConfig row, falls back to env only when no row exists or llm_provider is falsy
- `CartService` gets `llm_ollama_base_url` param rather than only the router knowing about it — ensures the full pipeline (parse + match) works with Ollama, not just the router layer
- When `base_url` is provided, `api_key` is omitted from litellm/instructor kwargs (Ollama has no API key requirement)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Threaded ollama_base_url through CartService**
- **Found during:** Task 2 (Ollama base_url support)
- **Issue:** Plan instructed adding base_url to shopping router, but CartService calls parse_shopping_list() and match_products() internally. Without threading base_url through CartService, Ollama would not work end-to-end — only the router knows the base_url.
- **Fix:** Added `llm_ollama_base_url: Optional[str] = None` to CartService.__init__ and passed `base_url=self.llm_ollama_base_url` to both LLM service calls in process_list()
- **Files modified:** app/services/cart_service.py
- **Verification:** Import check passes; test suite (82 tests) all green
- **Committed in:** d6466c0 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Essential for Ollama end-to-end correctness. No scope creep — CartService is already the LLM call site.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- Plan 02 (settings hub UI) can now write `llm_provider`, `llm_model`, `llm_api_key_encrypted`, and `llm_ollama_base_url` to AppConfig; changes take effect on the next shopping request without restart
- `test_connection()` now accepts `base_url` for the Ollama connection test that the settings page will call
- Alembic migration 0003 must run before the settings page writes new columns — handled automatically by app startup migration runner

---
*Phase: 04-multi-provider-llm-and-settings*
*Completed: 2026-04-05*
