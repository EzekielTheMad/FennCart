# Phase 9: Nyquist Validation Backfill - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Backfill VALIDATION.md files for all 7 v1.0 phases with passing test coverage. Each phase must have a non-stub VALIDATION.md documenting its observable behaviors with automated verification.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
- **Coverage strategy:** 6 of 7 phases already have VALIDATION.md files in `.planning/milestones/v1.0-phases/`. Phase 6 (Wire Review Mode and Cart History) is missing one entirely. Claude should audit existing files for completeness (stub vs real content), fill gaps, and create Phase 6's file from scratch.
- **Test writing scope:** Write new tests only for behaviors that have zero automated coverage. Don't rewrite or refactor existing passing tests — just map them to VALIDATION.md entries. If a behavior is already tested but not documented in VALIDATION.md, document it.
- **VALIDATION.md location:** Keep files in `.planning/milestones/v1.0-phases/{phase-dir}/` alongside existing ones for consistency. Do not move or reorganize existing files.
- **Completion criteria:** Full test suite must pass under `python -m pytest tests/ -q`. Every test referenced in VALIDATION.md files must be individually runnable and passing.
- **Approach:** Process phases in order (1-7). For each: read existing VALIDATION.md, audit what's covered vs missing, write tests for gaps, update VALIDATION.md to be non-stub and complete.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing VALIDATION.md Files (audit targets)
- `.planning/milestones/v1.0-phases/01-foundation-and-auth/01-VALIDATION.md` — Phase 1 validation
- `.planning/milestones/v1.0-phases/02-core-loop/02-VALIDATION.md` — Phase 2 validation
- `.planning/milestones/v1.0-phases/03-preference-system/03-VALIDATION.md` — Phase 3 validation
- `.planning/milestones/v1.0-phases/04-multi-provider-llm-and-settings/04-VALIDATION.md` — Phase 4 validation
- `.planning/milestones/v1.0-phases/05-hardening-and-distribution/05-VALIDATION.md` — Phase 5 validation
- `.planning/milestones/v1.0-phases/07-llm-config-integration-fix/07-VALIDATION.md` — Phase 7 validation
- (Phase 6 MISSING — must be created)

### Existing Test Files (coverage source)
- `tests/` directory — 18 test files covering various v1.0 features
- `pytest.ini` — test configuration

### Requirements
- `.planning/REQUIREMENTS.md` — VAL-01 is the single requirement for this phase

### Research Flag from STATE.md
- "Audit all 7 v1.0 phase directories for existing VALIDATION.md files before writing new ones. Identify which phases have partial coverage vs. none, and which routers/services are missing test coverage entirely."

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tests/conftest.py` — shared fixtures (async_session, DI override, get_settings patch)
- Established test patterns: `httpx.AsyncClient` + `ASGITransport` for integration tests
- `pytest.ini` — existing configuration with anyio_backends

### Established Patterns
- Patch `app.main.get_settings` at module level for any test hitting non-/setup routes
- `lru_cache` on `get_settings()` means env vars must be set before conftest imports
- `pytest-env` for SESSION_SECRET_KEY in test environment

### Integration Points
- Each v1.0 phase's VALIDATION.md maps to specific test files and routers/services
- VALIDATION.md template available at `$HOME/.claude/get-shit-done/templates/VALIDATION.md`

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-nyquist-validation-backfill*
*Context gathered: 2026-04-07*
