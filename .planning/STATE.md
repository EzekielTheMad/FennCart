# State: Fenn Cart

**Last updated:** 2026-04-02
**Updated by:** roadmapper (initial creation)

---

## Project Reference

**Core value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

**Current focus:** Phase 1 — Foundation and Auth

---

## Current Position

**Phase:** 1 — Foundation and Auth
**Plan:** None started
**Status:** Not started
**Blocker:** None

**Progress:**
```
[Phase 1] [ ] Foundation and Auth
[Phase 2] [ ] Core Loop
[Phase 3] [ ] Preference System
[Phase 4] [ ] Multi-Provider LLM and Settings
[Phase 5] [ ] Hardening and Distribution
```

---

## Performance Metrics

**Plans completed:** 0
**Plans total:** TBD (plans not yet created)
**Phases completed:** 0/5

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

**What was done last:** Roadmap created from requirements and research. 20/20 v1 requirements mapped across Phases 1-4. Phase 5 is non-functional hardening with no requirement mappings.

**What comes next:** Run `/gsd:plan-phase 1` to create the Phase 1 execution plan.

**Context to re-establish:** Read ROADMAP.md Phase 1 detail section and the research flags above before planning Phase 1.

---
*State initialized: 2026-04-02*
