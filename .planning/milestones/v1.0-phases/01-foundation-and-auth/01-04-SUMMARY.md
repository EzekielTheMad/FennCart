---
phase: 01-foundation-and-auth
plan: 04
subsystem: auth
tags: [authlib, oauth2, pkce, fernet, cryptography, kroger, token-refresh]

# Dependency graph
requires:
  - phase: 01-01
    provides: config, database, OAuthToken model, AppConfig model, app/main.py with pre-stubbed auth router include
  - phase: 01-02
    provides: pages router, base templates
  - phase: 01-03
    provides: setup wizard backend, AppConfig wizard_step/wizard_complete fields, test conftest with fixtures

provides:
  - Kroger OAuth PKCE flow (start + callback endpoints)
  - Fernet-encrypted token storage in SQLite (D-06)
  - Proactive silent token refresh within 60s of expiry (SETUP-04)
  - Wizard completion marking (wizard_complete=True, wizard_step="complete")
  - Quick tour page shown once after wizard completion (D-03)
  - get_valid_access_token() service for use by future API calls

affects: [02-core-loop, kroger-api-calls, cart-service, product-matching]

# Tech tracking
tech-stack:
  added: [authlib starlette integration, cryptography Fernet, httpx for refresh token exchange]
  patterns:
    - "OAuth PKCE via authlib.integrations.starlette_client.OAuth with authorize_redirect + authorize_access_token"
    - "Fernet key stored at /data/app.key (Docker volume), loaded at call time not startup"
    - "Proactive token refresh: check expiry within 60s, fall back to existing token on refresh failure"
    - "OAuth client registered at startup only when Kroger credentials are present"

key-files:
  created:
    - app/services/oauth_manager.py
    - app/routers/auth.py
    - templates/tour.html
    - tests/test_oauth.py
  modified:
    - app/main.py (lifespan calls register_kroger_oauth)
    - app/routers/pages.py (added /tour route)
    - templates/setup/step_oauth.html (updated to /auth/kroger/start, added error state)

key-decisions:
  - "Fernet key loaded at call time (not cached at module level) so tests can patch KEY_PATH without import-time side effects"
  - "register_kroger_oauth() guarded by credential check so app starts in unconfigured state without error"
  - "OAuth callback error renders step_oauth.html directly rather than redirecting — preserves PKCE session context"
  - "Tour page is standalone (no base.html) — users arrive here directly from OAuth redirect, nav shell not needed"

patterns-established:
  - "Service modules in app/services/ follow the pattern: pure async functions, no app-level state, injectable DB session"
  - "Template error rendering: TemplateResponse with error context variable, not redirect to error page"

requirements-completed: [SETUP-03, SETUP-04]

# Metrics
duration: 12min
completed: 2026-04-03
---

# Phase 1 Plan 04: Kroger OAuth PKCE Flow Summary

**Kroger OAuth PKCE authorization flow with Fernet-encrypted token storage, proactive 60-second refresh, and post-setup quick tour page**

## Performance

- **Duration:** 12 min
- **Started:** 2026-04-03T00:40:39Z
- **Completed:** 2026-04-03T00:52:49Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Full Kroger OAuth PKCE flow: /auth/kroger/start redirects with S256 challenge, /auth/kroger/callback exchanges code for tokens
- Tokens encrypted with Fernet before writing to SQLite; key persists on Docker volume at /data/app.key
- Proactive silent refresh triggers when token has fewer than 60 seconds remaining (SETUP-04)
- Wizard marked complete (wizard_complete=True, wizard_step="complete") after successful OAuth
- Tour page renders standalone (no sidebar) with 3 tips and "Start shopping" CTA

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OAuth manager with Fernet encryption and silent refresh** - `f665401` (feat)
2. **Task 2: Create OAuth routes, wizard step 4 template, tour page, and tests** - `125713d` (feat)

**Plan metadata:** _(docs commit follows)_

## Files Created/Modified
- `app/services/oauth_manager.py` - Authlib OAuth client, Fernet key management, encrypted token storage, proactive refresh
- `app/routers/auth.py` - GET /auth/kroger/start (PKCE redirect) and GET /auth/kroger/callback (token exchange + wizard completion)
- `templates/tour.html` - Standalone quick tour page with 3 tips and "Start shopping" link to /shopping
- `tests/test_oauth.py` - 5 tests: encryption, decryption, proactive refresh, no-refresh-when-fresh, wizard completion
- `app/main.py` - Updated lifespan to call register_kroger_oauth() when credentials present
- `app/routers/pages.py` - Added /tour route
- `templates/setup/step_oauth.html` - Updated href from /auth/kroger/login to /auth/kroger/start; added error "Try again" link

## Decisions Made
- Fernet key loaded at call time rather than module import — allows tests to patch KEY_PATH cleanly
- OAuth client registration guarded by credential presence — app boots in unconfigured state without throwing
- OAuth callback error path renders step_oauth.html template inline rather than redirecting — preserves PKCE session state

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Updated step_oauth.html href from /auth/kroger/login to /auth/kroger/start**
- **Found during:** Task 2 (reading existing template before creating auth router)
- **Issue:** The existing template stub linked to /auth/kroger/login, but the plan specifies /auth/kroger/start as the endpoint. Left uncorrected, the "Authorize with Kroger" button would 404.
- **Fix:** Updated href and also improved error state layout to match spec (added "Try again" link in error block)
- **Files modified:** templates/setup/step_oauth.html
- **Verification:** Template now matches the /auth/kroger/start endpoint created in auth.py
- **Committed in:** 125713d (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical — broken endpoint URL in existing stub)
**Impact on plan:** Necessary correction; without it the OAuth button would not work.

## Issues Encountered
None — tests passed on first run.

## Known Stubs
None — all endpoints are wired, all template content is real.

## User Setup Required
None — no external service configuration required beyond what Plan 01-03 established (Kroger developer credentials must be in environment variables).

## Next Phase Readiness
- Complete OAuth flow: wizard now goes start -> LLM -> Kroger credentials -> store selection -> OAuth -> tour -> shopping
- get_valid_access_token(db) is the entry point for Phase 2 (Core Loop) to make authenticated Kroger API calls
- AppConfig.wizard_complete=True gate in SetupGuardMiddleware now properly guards main app routes

## Self-Check: PASSED

- FOUND: app/services/oauth_manager.py
- FOUND: app/routers/auth.py
- FOUND: templates/tour.html
- FOUND: tests/test_oauth.py
- FOUND: .planning/phases/01-foundation-and-auth/01-04-SUMMARY.md
- FOUND commit f665401 (Task 1)
- FOUND commit 125713d (Task 2)
- All 26 tests pass (pytest tests/ -x -q)

---
*Phase: 01-foundation-and-auth*
*Completed: 2026-04-03*
