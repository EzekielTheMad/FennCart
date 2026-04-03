---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: planning
last_updated: "2026-04-03T01:09:03.480Z"
progress:
  total_phases: 5
  completed_phases: 1
  total_plans: 4
  completed_plans: 4
  percent: 100
---

# State: Fenn Cart

**Last updated:** 2026-04-02
**Updated by:** roadmapper (initial creation)

---

## Project Reference

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

**Current focus:** Phase 01 — foundation-and-auth

---

## Current Position

Phase: 01 (foundation-and-auth) — COMPLETE
Plan: 4 of 4 (all plans complete)
**Phase:** 2
**Plan:** Not started
**Status:** Ready to plan
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

**What was done last:** Completed Plan 04 — Kroger OAuth PKCE flow with Fernet token encryption, proactive silent refresh, and quick tour page. Phase 01 complete.

**What comes next:** Phase 02 — Core Loop (product matching, shopping list input, cart building). Use get_valid_access_token(db) from app/services/oauth_manager.py for authenticated Kroger API calls.

**Context to re-establish:** Read 01-01-SUMMARY.md, 01-03-SUMMARY.md, 01-04-SUMMARY.md. OAuth tokens encrypted in SQLite. AppConfig.wizard_complete=True guards main app routes.

---
*State initialized: 2026-04-02*
