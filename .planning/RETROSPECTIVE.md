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

## Milestone: v1.1 Tech Debt Cleanup

**Shipped:** 2026-04-08
**Phases:** 2 | **Plans:** 5 | **Timeline:** 1 day

### What Was Built
- Helpful error page for missing SESSION_SECRET_KEY (was crash-looping containers)
- MIT License file and corrected GitHub URL in README
- Stable Alpine.js `$root.updateItem()` state-lift replacing fragile `_x_dataStack` internal API
- Dead code removal: `/shopping/swap` endpoint, `review_card.html`, unused imports, deprecated TemplateResponse calls
- Nyquist-compliant VALIDATION.md for all 7 v1.0 phases (197 tests mapped to requirements)

### What Worked
- **Parallel executor agents:** Phase 8 ran both plans simultaneously in worktree isolation — efficient use of time
- **Research-driven Alpine fix:** Researcher identified `$root` state-lift as the correct pattern, eliminating both QUAL-01 and QUAL-02 in one architectural change
- **Auto-advance chain:** discuss -> plan -> execute ran seamlessly for Phase 8
- **Documentation-only Phase 9:** 3 parallel agents rewrote 7 VALIDATION.md files without touching any code

### What Was Inefficient
- **Merge conflicts from parallel worktrees:** Both Phase 8 agents modified `review_screen.html` — required manual conflict resolution
- **Plan checker rate limit:** Phase 9 plan verification was skipped due to rate limit on subagent model
- **Background test tasks:** Several pytest processes hung or were orphaned during parallel execution

### Key Lessons
- **QUAL-01 and QUAL-02 were one fix:** The Alpine state-lift that fixed the fragile API also eliminated the need for the server-side swap endpoint
- **Worktree isolation prevents most conflicts:** Only one conflict across 5 parallel agent runs — and it was in a file both plans legitimately needed to modify
- **Stub VALIDATION.md files are tech debt:** All 6 existing files were stubs created during planning but never filled in post-execution — the backfill was necessary

---

## Cross-Milestone Trends

| Metric | v1.0 | v1.1 |
|--------|------|------|
| Phases | 7 | 2 |
| Plans | 19 | 5 |
| Days | 5 | 1 |
| Commits | 125 | 28 |
| Python LOC | ~6,400 | ~6,400 |
| HTML LOC | ~5,000 | ~5,000 |
| Tests | 187 | 197 |
| Requirements | 20/20 | 5/5 |
| Tech debt items | 5 | 0 |
