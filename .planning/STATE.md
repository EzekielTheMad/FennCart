---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
last_updated: "2026-04-03T08:40:13.244Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 8
  completed_plans: 7
  percent: 88
---

# State: Fenn Cart

**Last updated:** 2026-04-02
**Updated by:** roadmapper (initial creation)

---

## Project Reference

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

**Current focus:** Phase 02 — core-loop

---

## Current Position

Phase: 02 (core-loop) — Plan 3 of 3 complete
**Phase:** 2
**Plan:** 3 of 3 — COMPLETE
**Status:** Phase 02 complete — ready for Phase 03
**Blocker:** None

**Progress:**

[█████████░] 88%
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

**What was done last:** Completed Plan 02-03 — CartService, shopping router (5 endpoints), and 7 Jinja2 templates for the complete list-to-cart HTMX flow. Phase 02 complete.

**What comes next:** Phase 03 — Preference System (receipt PDF parsing, brand preference learning, pass preferences dict to CartService.process_list).

**Context to re-establish:** Read 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md. CartService.process_list accepts preferences=None hook. AppConfig.store_id holds the Kroger location. Starlette session stores match_data + candidates between requests.

---
*State initialized: 2026-04-02*
