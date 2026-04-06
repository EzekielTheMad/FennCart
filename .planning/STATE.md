---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-04-06T23:00:40.098Z"
progress:
  total_phases: 7
  completed_phases: 7
  total_plans: 19
  completed_plans: 19
  percent: 100
---

# State: Fenn Cart

**Last updated:** 2026-04-02
**Updated by:** roadmapper (initial creation)

---

## Project Reference

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

**Current focus:** Phase 07 — llm-config-integration-fix — COMPLETE

---

## Current Position

Phase: 07 (llm-config-integration-fix) — COMPLETE
Plan: 1 of 1
**Phase:** 07
**Plan:** 1 of 1 — COMPLETE
**Status:** All phases and plans complete — milestone v1.0 ready
**Blocker:** None

**Progress:**

[██████████] 100%
[Phase 1] [ ] Foundation and Auth
[Phase 2] [ ] Core Loop
[Phase 3] [ ] Preference System
[Phase 4] [ ] Multi-Provider LLM and Settings
[Phase 5] [ ] Hardening and Distribution

```

---

## Performance Metrics

**Plans completed:** 4
**Plans total:** 4
**Phases completed:** 1/5

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 01-foundation-and-auth | 01 | ~4min | 2 | 21 |
| 01-foundation-and-auth | 02 | — | — | — |
| 01-foundation-and-auth | 03 | 17min | 2 | 15 |
| 01-foundation-and-auth | 04 | 12min | 2 | 7 |
| Phase 02-core-loop P01 | 8min | 2 tasks | 8 files |
| Phase 02-core-loop P03 | 6min | 3 tasks | 10 files |
| Phase 02-core-loop P04 | 15min | 2 tasks | 2 files |
| Phase 05-hardening-and-distribution P01 | 15min | 2 tasks | 6 files |
| Phase 06-wire-review-mode-and-cart-history P01 | 18min | 3 tasks | 5 files |
| Phase 07-llm-config-integration-fix P01 | 8min | 2 tasks | 2 files |

## Accumulated Context

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Python 3.12 + FastAPI + HTMX/Jinja2 | SSR eliminates Node.js build pipeline from Docker image; HTMX sufficient for dynamic review flow |
| LiteLLM + Instructor | Provider-agnostic LLM abstraction returning typed Pydantic objects; provider is config, not code branch |
| Authlib for OAuth PKCE | Handles Kroger's OAuth 2.0 PKCE flow; async-compatible |
| pdfplumber for receipt parsing | Superior table extraction for machine-generated PDFs; MIT licensed |
| SQLite via SQLModel + aiosqlite | Zero-ops persistence; single container; WAL mode required for async safety |
| LLM-01 placed in Phase 2 | LLM Service is required infrastructure for the core loop, not a standalone feature |
| Wizard templates standalone (no base.html) | Wizard runs pre-auth before nav shell is available; CDN scripts loaded directly |
| Test conftest patches async_session + DI | Middleware bypasses FastAPI DI; both layers must be patched for full test isolation |
| Starlette 0.49.1 TemplateResponse new API | request is first param, no longer in context dict — applied throughout to avoid deprecation |
| Fernet key loaded at call time | Loaded from /data/app.key at call time not module import — allows tests to patch KEY_PATH without import-time side effects |
| OAuth client registration guarded by credentials | register_kroger_oauth() only called when both Kroger credentials present — app starts cleanly in unconfigured state |
| Tour page is standalone | No base.html extension — users arrive via OAuth redirect, nav shell not available/needed |
| Router-local Jinja2Templates | Each router instantiates Jinja2Templates locally to avoid circular import from app.main |
| Server-side session for match state | Starlette session persists match_data + candidates across multi-step HTMX shopping flow |
| 0.8 confidence threshold | CartService.partition_matches splits items into review cards vs auto-matched compact table |
| Mock at module boundary (app.services.cart_service.*) | Patch at module level so CartService unit tests isolate service logic without touching Kroger or LLM |
| Patch app.routers.shopping.get_valid_access_token | Router-level patch avoids OAuth storage for testing expired-token path independently |
| pytest-env for SESSION_SECRET_KEY in test environment | env var must be set before conftest imports app.main; lru_cache on get_settings() makes this critical |
| anthropic and openai explicit in requirements.txt | LiteLLM does not bundle provider SDKs; Claude provider raises ImportError without explicit anthropic dep |
| Jinja2 dict bracket access for shadowed keys | entry['items'] not entry.items — Jinja2 resolves .items as Python dict method, not the 'items' key |
| Patch app.main.get_settings in history/shopping tests | SetupGuardMiddleware calls get_settings() directly, bypassing DI; must patch at module level in history/preferences tests too |

### Architecture Constraints (carry forward)

- Customer search data (raw list queries) must never be persisted — in-memory only
- Products API results must never be written to a durable SQLite table (TOS)
- Cart API is add-only; maintain a local session-scoped shadow in SQLite
- OAuth redirect URI must be built from a configurable `BASE_URL` env var, never hardcoded
- Kroger credentials must never have default values; app must refuse to start if absent
- `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000` required at DB init
- `--workers 1` for Uvicorn (SQLite cannot handle concurrent writers)

### Research Flags (carry into planning)

- **Phase 2 planning:** Spike on LLM prompt strategy before building Cart Service — 48% baseline success rate means prompt engineering is non-trivial. Validate Kroger Products API response shape with a real API call before designing matching logic.
- **Phase 3 planning:** Test at least three real Fry's receipt PDF formats (emailed, app-downloaded, older) with pdfplumber before committing to parser design.
- **Phase 1 planning:** Validate full Kroger OAuth PKCE round-trip inside Docker early — redirect URI mismatch is the known failure mode.

### Todos

- (none yet — awaiting plan-phase for Phase 1)

### Blockers

- (none)

---

## Session Continuity

**What was done last:** Completed Plan 07-01 — wired preferences.py receipt upload and NL chat endpoints to use get_active_llm_config(db) instead of settings.llm_*. Two new integration tests prove DB-configured provider/model values reach the LLM service functions. 187 tests passing total (up from 183).

**What comes next:** Milestone v1.0 complete — all 7 phases, 19 plans executed.

**Context to re-establish:** entry['items'] bracket syntax required in Jinja2 when key name shadows dict built-in method. Patch app.main.get_settings (not just DI override) for any test hitting a non-/setup route. TemplateResponse new API: request as first positional arg throughout. get_active_llm_config(db) is the canonical LLM config reader across shopping, upload, and NL chat.

---
*State initialized: 2026-04-02*
