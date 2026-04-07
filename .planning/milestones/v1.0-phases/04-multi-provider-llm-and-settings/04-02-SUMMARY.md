---
phase: 04-multi-provider-llm-and-settings
plan: 02
subsystem: ui
tags: [htmx, alpine, jinja2, tailwind, fastapi, settings, llm, oauth]

# Dependency graph
requires:
  - phase: 04-multi-provider-llm-and-settings
    plan: 01
    provides: AppConfig with llm_api_key_encrypted/llm_ollama_base_url/review_mode, get_active_llm_config(), test_connection() with base_url
  - phase: 01-foundation-and-auth
    provides: OAuth flow, AppConfig model, Fernet encryption

provides:
  - Settings hub at /settings with sidebar sub-navigation (4 sections)
  - /settings/section/{section} HTMX partials for section switching
  - LLM provider form with test-connection-before-save, Fernet encryption, eye-icon API key reveal
  - Store search/select endpoints (settings-specific, no wizard mutation)
  - Kroger account auth status badge and re-authorize flow
  - Review mode toggle (exceptions/full) with persistence
  - Auth callback smart redirect: first-time goes to /tour, re-auth goes to /settings?section=account

affects:
  - 04-03 (wizard LLM step can reference same settings UX patterns)
  - 05 (hardening phase will test settings round-trip)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Settings hub shell: two-column flex layout with HTMX sub-nav partial swapping into #settings-content
    - Alpine.js provider-reactive form: x-model="provider" drives x-show conditionals for API key / endpoint / model fields
    - Eye-icon API key reveal: nested x-data="{ show: false }" with :type="show ? 'text' : 'password'" on input
    - Test-before-save: HTMX POST to /settings/save-llm, server runs test_connection(), returns error partial on failure or saves+returns success partial

key-files:
  created:
    - app/routers/settings.py
    - templates/partials/settings/llm.html
    - templates/partials/settings/store.html
    - templates/partials/settings/account.html
    - templates/partials/settings/preferences.html
  modified:
    - templates/pages/settings.html
    - app/routers/pages.py
    - app/routers/auth.py
    - app/main.py

key-decisions:
  - "was_already_complete flag captured before marking wizard done in auth callback — distinguishes first-time OAuth (→ /tour) from re-auth (→ /settings?section=account)"
  - "Settings store search uses kroger_client.get_app_token() + search_stores_by_zip() directly — does not mutate wizard_step or wizard_complete"
  - "save-llm leaves llm_api_key_encrypted unchanged when api_key field submitted empty — allows provider/model update without re-entering key"

patterns-established:
  - "Settings section partial swap: hx-get='/settings/section/{section}' → hx-target='#settings-content' hx-swap='innerHTML'"
  - "Alpine provider reactive: x-model='provider' drives x-show conditionals; no server round-trip for field visibility"

requirements-completed:
  - LLM-02

# Metrics
duration: 18min
completed: 2026-04-05
---

# Phase 4 Plan 2: Settings Hub UI Summary

**Full settings hub with HTMX sub-nav, Alpine.js provider-reactive LLM form (eye-icon key reveal, test-before-save), store search reuse, Kroger auth status badge, and review mode toggle**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-04-05T23:48:55Z
- **Completed:** 2026-04-05T00:10:00Z
- **Tasks:** 2
- **Files modified:** 9 (5 created, 4 modified)

## Accomplishments

- Built `app/routers/settings.py` with 6 endpoints: GET /settings, GET /settings/section/{section}, POST /settings/save-llm (test-before-save), POST /settings/search-stores, POST /settings/select-store, POST /settings/save-preferences
- Replaced placeholder `templates/pages/settings.html` with two-column shell: 52-wide sub-nav sidebar (4 items, 44px touch targets, Heroicons, HTMX section switching) + `#settings-content` partial target
- `partials/settings/llm.html`: Alpine.js provider dropdown drives x-show conditionals for API key field / Ollama endpoint field / model dropdown; eye-icon reveal toggle; "Test connection and save" CTA with spinner loading state
- `partials/settings/store.html`: current store display, zip search, store list with settings-specific endpoints (no wizard_step mutation)
- `partials/settings/account.html`: green/amber auth status chip, Re-authorize with Kroger full-redirect button with Alpine loading state
- `partials/settings/preferences.html`: exceptions/full radio cards, Save preferences button
- Fixed auth callback redirect logic: `was_already_complete` captured before wizard completion to correctly route first-time auth to /tour and re-auth to /settings?section=account
- All 82 existing tests remain green

## Task Commits

1. **Task 1: Create settings router with all endpoints and wire into app** - `d0b1d1e` (feat)
2. **Task 2: Create settings shell template and all 4 section partial templates** - `4189091` (feat)

## Files Created/Modified

- `app/routers/settings.py` - New: 6 settings endpoints, _get_or_create_config helper, Fernet encrypt on save
- `templates/pages/settings.html` - Replaced placeholder with full two-column settings shell
- `templates/partials/settings/llm.html` - New: provider-reactive LLM form with test-before-save
- `templates/partials/settings/store.html` - New: zip search + store selection (settings endpoints)
- `templates/partials/settings/account.html` - New: Kroger auth status chip + re-auth button
- `templates/partials/settings/preferences.html` - New: review mode radio toggle + save
- `app/routers/pages.py` - Removed /settings handler (settings router now owns it)
- `app/routers/auth.py` - Fixed redirect logic: was_already_complete captures pre-auth state
- `app/main.py` - Registered settings router

## Decisions Made

- `was_already_complete` is captured before setting `wizard_complete = True` in the auth callback. This correctly distinguishes first-time wizard completion (→ /tour) from re-auth initiated from settings (→ /settings?section=account). Without this, first-time auth would incorrectly redirect to settings.
- Store search in settings reuses `kroger_client.get_app_token()` + `search_stores_by_zip()` directly rather than calling wizard endpoints — avoids any risk of mutating `wizard_step` or `wizard_complete` (Pitfall 4 from RESEARCH).
- Empty `api_key` submission leaves `llm_api_key_encrypted` unchanged — allows users to change provider/model without re-entering their API key.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed auth callback redirect for first-time vs re-auth**
- **Found during:** Task 2 (template creation) — discovered when running full test suite
- **Issue:** Plan specified `if cfg and cfg.wizard_complete: redirect to /settings` but the callback sets `wizard_complete = True` before the check, meaning first-time OAuth also redirected to settings instead of /tour. Test `test_auth_callback_marks_wizard_complete` caught this.
- **Fix:** Added `was_already_complete = cfg.wizard_complete if cfg else False` before updating wizard fields; redirect condition uses `was_already_complete` instead of post-update `cfg.wizard_complete`
- **Files modified:** app/routers/auth.py
- **Verification:** All 10 OAuth tests pass; full 82-test suite green
- **Committed in:** 4189091 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 logic bug)
**Impact on plan:** Essential correctness fix — without it, first-time wizard OAuth would bypass the tour page. No scope creep.

## Issues Encountered

None beyond the auth callback logic bug documented above.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

- Settings hub is fully functional: users can switch LLM providers, update store, re-authorize Kroger, and toggle review mode
- Plan 04-03 (wizard LLM step) can reference the same `partials/settings/llm.html` patterns or reuse the LLM config form
- `llm_api_key_encrypted`, `llm_provider`, `llm_model`, `llm_ollama_base_url` and `review_mode` are all writable from settings; changes take effect on next shopping request (no restart needed)

---
*Phase: 04-multi-provider-llm-and-settings*
*Completed: 2026-04-05*
