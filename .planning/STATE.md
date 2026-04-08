---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
last_updated: "2026-04-08T17:19:11.492Z"
last_activity: 2026-04-08
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 5
  completed_plans: 5
  percent: 50
---

# State: Fenn Cart

**Last updated:** 2026-04-07
**Updated by:** roadmapper (v1.1 roadmap)

---

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-07)

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.
**Current focus:** Phase 09 — nyquist-validation-backfill

---

## Current Position

Phase: 09 (nyquist-validation-backfill) — EXECUTING
Plan: 3 of 3
Status: Phase complete — ready for verification
Last activity: 2026-04-08
**Blocker:** None

Progress: [█████░░░░░] 50% — 0/2 phases complete (1/2 plans done in phase 08)

---

## Performance Metrics

**Plans completed:** 0
**Plans total:** TBD
**Phases completed:** 0/2

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| 08-code-cleanup | P01 | 15min | 2 | 7 |
| Phase 08 P02 | 727 | 2 tasks | 4 files |
| Phase 09-nyquist-validation-backfill P02 | 5min | 2 tasks | 2 files |
| Phase 09 P03 | 7 | 2 tasks | 2 files |
| Phase 09-nyquist-validation-backfill P01 | 9min | 3 tasks | 3 files |

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
| SESSION_KEY_MISSING module-level flag (08-01) | Avoids re-calling lru_cached get_settings() which would raise ValidationError on each request when key is missing |
| Standalone session_error.html (08-01) | No base.html — consistent with missing_config.html pattern, works when session middleware initialized with placeholder |
| Alpine state-lift via $root.updateItem (08-02) | $root is a documented stable Alpine.js 3 API; replaces _x_dataStack internal API for product swap in review screen |
| confirmedItems from Jinja2 loops not confirmed_items_json (08-02) | confirmed_items_json context var was never passed by /match endpoint; initializing from review_items + auto_items loops is correct |

### Architecture Constraints (carry forward)

- Customer search data (raw list queries) must never be persisted — in-memory only
- Products API results must never be written to a durable SQLite table (TOS)
- Cart API is add-only; maintain a local session-scoped shadow in SQLite
- OAuth redirect URI must be built from a configurable `BASE_URL` env var, never hardcoded
- Kroger credentials must never have default values; app must refuse to start if absent
- `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000` required at DB init
- `--workers 1` for Uvicorn (SQLite cannot handle concurrent writers)

### Research Flags (carry into planning)

- **Phase 9 planning:** Audit all 7 v1.0 phase directories for existing VALIDATION.md files before writing new ones. Identify which phases have partial coverage vs. none, and which routers/services are missing test coverage entirely.

### Todos

- (none yet — awaiting plan-phase for Phase 8)

### Blockers

- (none)

---

## Session Continuity

**What was done last:** Executed 08-01-PLAN.md — SESSION_SECRET_KEY guard (ERR-01), MIT License + README URL (DOC-01), TemplateResponse API fix in pages.py + auth.py. 193 tests passing.

**What comes next:** 08-02-PLAN.md — Alpine._x_dataStack replacement, dead POST /shopping/swap removal, dead code audit.

**Context to re-establish:** entry['items'] bracket syntax required in Jinja2 when key name shadows dict built-in method. Patch app.main.get_settings (not just DI override) for any test hitting a non-/setup route. TemplateResponse new API: request as first positional arg throughout — now applied to all routes. SESSION_KEY_MISSING flag is module-level in app/main.py; patch at "app.main.SESSION_KEY_MISSING" in tests. get_active_llm_config(db) is the canonical LLM config reader across shopping, upload, and NL chat.

---
*State initialized: 2026-04-02*
*Updated: 2026-04-07 — v1.1 roadmap created, Phase 8 ready to plan*
