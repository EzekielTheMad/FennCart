# Retrospective: Fenn Cart

## Milestone: v1.0 MVP

**Shipped:** 2026-04-07
**Phases:** 7 | **Plans:** 19 | **Commits:** 125 | **Timeline:** 5 days

### What Was Built
- Docker-containerized FastAPI app with guided 4-step setup wizard and Kroger OAuth PKCE
- End-to-end NL shopping list to Kroger cart flow with LLM product matching and review screen
- Receipt PDF parsing (pdfplumber) to bootstrap a frequency-weighted preference profile
- Multi-provider LLM support (Claude/OpenAI/Ollama) with DB-authoritative hot-swap settings hub
- NL preference chat, manual preference CRUD, preference-influenced product ranking
- Cart history tracking, review mode persistence, Docker hardening, Alembic migration safety

### What Worked
- **SSR stack (HTMX + Jinja2 + Alpine.js):** No JS build pipeline, fast iteration, Docker image stays lean
- **Instructor + LiteLLM for structured output:** Provider-agnostic typed Pydantic models for product matching worked reliably
- **GSD workflow:** 7 phases planned and executed in 5 days with minimal rework
- **Gap closure phases (6, 7):** Milestone audit surfaced real integration issues; targeted phases fixed them cleanly
- **TDD on critical paths:** Test-first approach for Phase 7 caught wiring issues before implementation

### What Was Inefficient
- **Phase 5 (hardening) scope:** Too broad initially, some items (live OAuth Docker round-trip) deferred as human UAT
- **Nyquist validation:** VALIDATION.md files created but never completed across any phase — overhead without payoff
- **Summary extraction:** CLI one-liner extraction from SUMMARY.md files was noisy, needed manual cleanup
- **Phase 3 missing VERIFICATION.md:** Integration checker confirmed wiring but formal verification step was skipped

### Patterns Established
- `get_active_llm_config(db)` as the canonical LLM config reader (DB-first, env fallback)
- Router-local `Jinja2Templates` to avoid circular imports (works but adds boilerplate)
- `entry['key']` bracket syntax in Jinja2 when key name shadows dict built-in methods
- Patch `app.main.get_settings` at module level for tests hitting SetupGuardMiddleware
- `pytest-env` for SESSION_SECRET_KEY (must be set before conftest imports app.main)
- Fernet key loaded at call time from /data/app.key (not module import) for test patchability

### Key Lessons
- **Milestone audit before completion is valuable:** Found 2 partial requirements and 1 integration gap that were invisible from phase-level summaries
- **Cart API is truly add-only:** Local shadow state in SQLite is essential; no way to verify cart contents via API
- **Kroger API results are non-personalized:** Preference system compensates but users may see different results than on frysfood.com
- **Alpine._x_dataStack is fragile:** Internal API used for product swap capture needs replacement in future

---

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 7 |
| Plans | 19 |
| Days | 5 |
| Commits | 125 |
| Python LOC | ~6,400 |
| HTML LOC | ~5,000 |
| Tests | 187 |
| Requirements | 20/20 |
| Tech debt items | 5 |
