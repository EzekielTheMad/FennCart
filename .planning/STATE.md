---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: tech-debt-cleanup
status: ready_to_plan
last_updated: "2026-04-07T16:30:00.000Z"
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# State: Fenn Cart

**Last updated:** 2026-04-07
**Updated by:** roadmapper (v1.1 roadmap)

---

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-07)

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.
**Current focus:** v1.1 Tech Debt Cleanup — Phase 8 (Code Cleanup) ready to plan

---

## Current Position

Phase: 8 - Code Cleanup (not started)
Plan: —
Status: Ready to plan
Last activity: 2026-04-07 — v1.1 roadmap created
**Blocker:** None

Progress: [░░░░░░░░░░] 0% — 0/2 phases complete

---

## Performance Metrics

**Plans completed:** 0
**Plans total:** TBD
**Phases completed:** 0/2

| Phase | Plan | Duration | Tasks | Files |
|-------|------|----------|-------|-------|
| (v1.1 phases not yet planned) | — | — | — | — |

---

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

- **Phase 9 planning:** Audit all 7 v1.0 phase directories for existing VALIDATION.md files before writing new ones. Identify which phases have partial coverage vs. none, and which routers/services are missing test coverage entirely.

### Todos

- (none yet — awaiting plan-phase for Phase 8)

### Blockers

- (none)

---

## Session Continuity

**What was done last:** Created v1.1 roadmap — 2 phases (8: Code Cleanup, 9: Nyquist Validation Backfill).

**What comes next:** Plan Phase 8 — fix SESSION_SECRET_KEY crash, update README, replace Alpine._x_dataStack usage, remove dead code.

**Context to re-establish:** entry['items'] bracket syntax required in Jinja2 when key name shadows dict built-in method. Patch app.main.get_settings (not just DI override) for any test hitting a non-/setup route. TemplateResponse new API: request as first positional arg throughout. get_active_llm_config(db) is the canonical LLM config reader across shopping, upload, and NL chat.

---
*State initialized: 2026-04-02*
*Updated: 2026-04-07 — v1.1 roadmap created, Phase 8 ready to plan*
