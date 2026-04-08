# Phase 9: Nyquist Validation Backfill - Research

**Researched:** 2026-04-07
**Domain:** pytest test coverage, Nyquist VALIDATION.md authoring, v1.0 phase audit
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

*(None — no locked decisions specified in CONTEXT.md. Implementation approach is entirely Claude's discretion.)*

### Claude's Discretion

- **Coverage strategy:** 6 of 7 phases already have VALIDATION.md files in `.planning/milestones/v1.0-phases/`. Phase 6 (Wire Review Mode and Cart History) is missing one entirely. Claude should audit existing files for completeness (stub vs real content), fill gaps, and create Phase 6's file from scratch.
- **Test writing scope:** Write new tests only for behaviors that have zero automated coverage. Don't rewrite or refactor existing passing tests — just map them to VALIDATION.md entries. If a behavior is already tested but not documented in VALIDATION.md, document it.
- **VALIDATION.md location:** Keep files in `.planning/milestones/v1.0-phases/{phase-dir}/` alongside existing ones for consistency. Do not move or reorganize existing files.
- **Completion criteria:** Full test suite must pass under `python -m pytest tests/ -q`. Every test referenced in VALIDATION.md files must be individually runnable and passing.
- **Approach:** Process phases in order (1-7). For each: read existing VALIDATION.md, audit what's covered vs missing, write tests for gaps, update VALIDATION.md to be non-stub and complete.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | All v1.0 phases have Nyquist-compliant VALIDATION.md with passing test coverage | Full audit completed — see Phase Coverage Matrix below. All 7 phases have existing test coverage; task is to write VALIDATION.md files that document and reference those tests, then fill any true coverage gaps. |
</phase_requirements>

---

## Summary

The validation backfill for Phase 9 is primarily a documentation task with targeted test-writing. All 197 existing tests pass in under 5 seconds. The 18 test files clearly map to the 7 v1.0 phases. The gap is not test coverage per se — it is that all 6 existing VALIDATION.md files are stubs with `nyquist_compliant: false` and empty per-task maps, and Phase 6 has no VALIDATION.md at all (only a VERIFICATION.md, which serves a different purpose).

The work pattern for each phase is: (1) read the existing VALIDATION.md stub, (2) identify the phase requirements from CONTEXT.md/VERIFICATION.md, (3) map existing passing tests to those requirements, (4) identify any requirement with zero test coverage and write a targeted test, (5) rewrite the VALIDATION.md with a complete per-task map and set `nyquist_compliant: true`.

For Phase 6, the file must be created from scratch. The VERIFICATION.md for Phase 6 is the authoritative source for what behaviors were delivered (SRCH-05 and CART-03), and `tests/test_phase06.py` (8 test cases) already provides full coverage.

**Primary recommendation:** Process phases 1-7 in order. Each phase requires a VALIDATION.md rewrite (not just edits) because the per-task maps are completely empty. Expect 1-2 new test functions total — the existing 197 tests already cover the observable behaviors of all phases.

---

## Phase Coverage Matrix (Audit)

This is the core finding. Every phase's existing test files, coverage status, and VALIDATION.md condition:

### Phase 1 — Foundation and Auth

**Requirements from CONTEXT.md:** SETUP-01 (wizard reachable from Docker), SETUP-02 (wizard config persisted), SETUP-03 (Kroger OAuth PKCE), SETUP-04 (silent token refresh), D-07 (missing config page)

**Existing test files:**
- `tests/test_health.py` — 1 test: `test_health_endpoint` (app startup / SETUP-01 proxy)
- `tests/test_wizard.py` — 4 tests: wizard redirect when incomplete, setup page renders, LLM validate success, wizard resumable (SETUP-01, SETUP-02, D-02)
- `tests/test_oauth.py` — 5 tests: store_token encrypts, get_decrypted_token, proactive refresh within 60s, no refresh when fresh, auth callback marks wizard complete (SETUP-04, D-06, SETUP-03)

**Coverage assessment:** 10 tests. All Phase 1 core behaviors covered. Missing config page (D-07 / ERR-01) is covered by `test_session_key_guard.py` which is more accurately a Phase 8 test. No new tests needed for Phase 1.

**VALIDATION.md status:** EXISTS, stub — per-task map empty, `nyquist_compliant: false`

---

### Phase 2 — Core Loop

**Requirements from CONTEXT.md:** SRCH-01 (shopping page renders), SRCH-02 (product search + LLM match), SRCH-04 (confidence partitioning), LLM-01 (structured output), CART-01 (add to cart), CART-02 (local persistence on API failure)

**Existing test files:**
- `tests/test_shopping_flow.py` — 11 tests: shopping page renders, list preview, empty preview, match returns review screen, review toggle, empty list error, add-to-cart success, success screen items, expired token, swap endpoint removed, no _x_dataStack (SRCH-01, SRCH-02, SRCH-04, SRCH-05, CART-01)
- `tests/test_cart_service.py` — 9 tests: confidence partitioning, process_list pipeline, dedup, cart persistence on success, cart persistence on failure, get_session_items, _to_candidate field extraction, missing fields (SRCH-04, SRCH-02, CART-02, CART-03)
- `tests/test_llm_matching.py` — 7 tests: parse_shopping_list, match_products, preferences=None, preferences dict, provider strings, prompt format, error handling (LLM-01)
- `tests/test_kroger_client.py` — Kroger API client tests (infrastructure for SRCH-02)
- `tests/test_kroger_products.py` — Product search tests

**Coverage assessment:** Comprehensive. No new tests needed for Phase 2.

**VALIDATION.md status:** EXISTS, stub — per-task map says "Populated after planning" placeholder, `nyquist_compliant: false`

---

### Phase 3 — Preference System

**Requirements from CONTEXT.md:** PREF-01 (receipt PDF upload + parse), PREF-02 (parsed items editable), PREF-03 (preference upsert), PREF-04 (NL chat apply), PREF-05 (preference CRUD), PREF-06 (preferences injected into matching)

**Existing test files:**
- `tests/test_receipt_parser.py` — 4 tests: valid PDF extraction, empty PDF warning, invalid bytes, LLM parse (PREF-01, PREF-02)
- `tests/test_preference_service.py` — 16 tests: upsert new, upsert increment, one-time no increment, contradiction triggers, contradiction low count no trigger, empty brand ignored, get_preferences_for_matching, cap at 50, empty, list with query, create manual, update, delete, bulk delete, apply_nl_delta add/remove/replace (PREF-03, PREF-05, PREF-06 service layer)
- `tests/test_preferences_flow.py` — 11 tests (Tests 1-11): preferences page loads, upload receipt, invalid file, preference CRUD lifecycle, search, bulk delete, NL chat clarify, NL chat confirm+apply, process_list with preferences, upload uses DB LLM config, chat uses DB LLM config (PREF-01, PREF-04, PREF-05, PREF-06)

**Coverage assessment:** Strong. PREF-02 (editable table UI) has no automated test — it is inherently a visual/HTMX behavior that cannot be verified without browser rendering. Correctly marked as manual-only. No new tests needed.

**VALIDATION.md status:** EXISTS, stub — per-task map has task IDs listed but all marked `❌ W0` (Wave 0 pending) even though tests now exist, `nyquist_compliant: false`

---

### Phase 4 — Multi-Provider LLM and Settings

**Requirements from CONTEXT.md:** LLM-02 (multi-provider config, settings UI, save/load/hot-swap)

**Existing test files:**
- `tests/test_settings.py` — 13 tests: settings page renders, LLM section, store section, account section, preferences section, save LLM success, save LLM invalid key, Ollama config, blank key keeps existing, search stores, select store, save preferences, hot-swap (LLM-02 thoroughly)
- `tests/test_llm_config.py` — 4 tests: env fallback, DB row reads, encrypted key decryption, Ollama path (LLM-02 service layer)

**Coverage assessment:** 17 tests. All LLM-02 behaviors covered. No new tests needed.

**VALIDATION.md status:** EXISTS, stub — per-task map lists 3 tasks with `❌ W0` even though tests now exist, `nyquist_compliant: false`

---

### Phase 5 — Hardening and Distribution

**Requirements from CONTEXT.md/VERIFICATION.md:** SC-1 (README), SC-2 (Docker build), SC-3 (OAuth in Docker), SC-4 (Alembic migrations)

**Existing test files:**
- `tests/test_migrations.py` — 2 tests: `test_migrations_upgrade_to_head`, `test_model_definitions_match_ddl` (SC-4)

**Coverage assessment:** SC-4 is covered. SC-1, SC-2, SC-3 are correctly manual-only (require Docker runtime and real credentials). This is the minimal but correct coverage for this phase.

**VALIDATION.md status:** EXISTS, stub — per-task map accurate (05-02-01 migration test listed as W0), `nyquist_compliant: false`. The W0 gaps are now filled — test file exists.

---

### Phase 6 — Wire Review Mode and Cart History

**Requirements delivered (from VERIFICATION.md):** SRCH-05 (review mode persistence from DB), CART-03 (history page with real CartSession/CartItem data)

**Existing test files:**
- `tests/test_phase06.py` — 4 tests (8 cases with asyncio+trio backends): `test_history_empty_state`, `test_history_with_sessions`, `test_review_mode_full_from_db`, `test_review_mode_exceptions_default` (SRCH-05, CART-03)

**Coverage assessment:** Full coverage of delivered behaviors. Note: `test_shopping_flow.py::test_success_screen_shows_items` also covers CART-03 surface from Phase 2's add-to-cart perspective (the success screen). No new tests needed.

**VALIDATION.md status:** MISSING — file does not exist. Must be created from scratch. VERIFICATION.md exists at `.planning/milestones/v1.0-phases/06-wire-review-mode-and-cart-history/06-VERIFICATION.md` and is the authoritative source for what behaviors were delivered.

---

### Phase 7 — LLM Config Integration Fix

**Requirements delivered:** Integration fix ensuring shopping/preferences routes read LLM config from DB (AppConfig) rather than env-var defaults. Post-Phase-7, `get_active_llm_config(db)` is the canonical reader.

**Existing test files:**
- `tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config` — verifies receipt upload uses DB provider/model (LLM-CONFIG)
- `tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config` — verifies NL chat uses DB provider/model (LLM-CONFIG)
- `tests/test_llm_config.py` — 4 tests covering the `get_active_llm_config` function itself

**Coverage assessment:** The two LLM-CONFIG tests in `test_preferences_flow.py` are exactly the tests the stub VALIDATION.md pointed to. They exist and pass. Shopping route LLM config also reads from DB (wired in Phase 7) — `test_shopping_flow.py::test_match_returns_review_screen` implicitly tests this via the `get_active_llm_config` mock pattern.

**VALIDATION.md status:** EXISTS, stub — per-task map lists `test_preferences_flow.py` tests as `✅` (file exists noted) but status marked pending. `nyquist_compliant: false`

---

## Test Infrastructure (Confirmed)

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `pytest.ini` (project root) |
| asyncio_mode | auto (in pytest.ini) |
| anyio_backends | asyncio (in pytest.ini, produces 1 benign warning) |
| SESSION_SECRET_KEY | Set via `pytest-env` in pytest.ini |
| Quick run | `python -m pytest tests/ -q` |
| Full suite | `python -m pytest tests/ -v` |
| Runtime | 4.94 seconds (verified 2026-04-07) |
| Total passing | 197 tests |

---

## Standard Stack

### Core (Already Installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.4.2 | Test runner | Confirmed in use across all 18 test files |
| pytest-asyncio | (in requirements-dev.txt) | async test support | `asyncio_mode = auto` in pytest.ini |
| pytest-env | (in requirements-dev.txt) | SESSION_SECRET_KEY in test env | Documented in CONTEXT.md established patterns |
| pytest-alembic | 0.12.1 | Migration chain testing | Already used in `test_migrations.py` |
| httpx | 0.28.1 | AsyncClient for integration tests | `ASGITransport(app=app)` pattern used in conftest.py |
| anyio | (pytest-asyncio dep) | async backends | `anyio_backends = asyncio` in pytest.ini |

**No new dependencies required.** The existing test infrastructure fully supports all testing needs for this backfill phase.

---

## Architecture Patterns

### Existing conftest.py Fixtures

```python
# C:\Projects\FennCart\tests\conftest.py
# Source: verified by direct read

# test_settings  — Settings with test Kroger/LLM credentials (bypasses SetupGuardMiddleware)
# test_db        — Function-scoped in-memory SQLite session
# client         — AsyncClient with:
#                  - DI override: get_session -> test_db
#                  - DI override: get_settings -> test_settings
#                  - Patch: app.database.async_session -> TestSessionLocal
#                  - Uses ASGITransport(app=app)
```

### Critical Test Pattern: get_settings Middleware Patch

Any test hitting a non-`/setup` route must patch `app.main.get_settings` at module level because `SetupGuardMiddleware` calls it directly, bypassing FastAPI DI:

```python
with patch("app.main.get_settings", return_value=_mock_settings()):
    response = await client.get("/some-route")
```

### Integration Test Skeleton (reference pattern from test_shopping_flow.py)

```python
@pytest.mark.anyio
async def test_behavior_name(client, test_db):
    """Describe what behavior is verified and which requirement it satisfies."""
    # Seed AppConfig so wizard_complete=True (required for most routes)
    test_db.add(AppConfig(id=1, wizard_complete=True, ...))
    await test_db.commit()

    with patch("app.main.get_settings", return_value=_mock_settings()):
        # Mock external services as needed
        response = await client.get("/route")

    assert response.status_code == 200
    assert "expected text" in response.text
```

### Unit Test Skeleton (reference pattern from test_preference_service.py)

```python
@pytest.mark.anyio
async def test_service_behavior(test_db):
    """Describe the unit behavior and its requirement."""
    svc = SomeService(test_db)
    result = await svc.some_method(args)
    assert result.field == expected_value
```

### Nyquist-Compliant VALIDATION.md Structure

A non-stub VALIDATION.md must have:
1. `nyquist_compliant: true` in frontmatter
2. `wave_0_complete: true` in frontmatter (all W0 gaps filled)
3. Per-Task Verification Map with real task IDs, requirement mappings, and `✅` File Exists status
4. Wave 0 Requirements section listing "None — existing infrastructure covers all phase requirements" (or specific gaps)
5. Approval status updated

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async HTTP testing | Custom test client setup | `conftest.py` `client` fixture | Already handles DI overrides, session patches, and ASGITransport |
| DB isolation per test | Manual teardown | `test_db` fixture (function-scoped) | Creates fresh in-memory SQLite per test, drops all tables after |
| Settings override | Per-test env var mutation | `test_settings` fixture + `patch("app.main.get_settings")` | lru_cache means env vars set after import have no effect |
| OAuth token setup | Real Authlib flow | `patch("app.services.oauth_manager.KEY_PATH", tmp_path)` | Fernet key loaded at call time, patchable via KEY_PATH |
| LLM calls | Real API | `patch("app.services.{module}.instructor.from_provider")` | Instructor wraps LiteLLM; mock at instructor boundary |

---

## Common Pitfalls

### Pitfall 1: Leaving Wave 0 gaps as open checkboxes

**What goes wrong:** VALIDATION.md says `- [ ] tests/test_file.py — stubs for PREF-01` but `tests/test_preference_service.py` already exists and passes. The planner marks it as needing creation.
**Why it happens:** The VALIDATION.md files were written as planning artifacts before execution. They were never updated post-execution.
**How to avoid:** When writing the updated VALIDATION.md, verify the test file actually exists before listing it as a gap. Use `ls tests/` as the authoritative list.
**Warning signs:** Any `❌ W0` entry in the per-task map for tests that have file names matching existing test files.

### Pitfall 2: Missing get_settings middleware patch

**What goes wrong:** Test hits a non-`/setup` route and gets 503 or redirect to `/missing_config` instead of the expected response.
**Why it happens:** `SetupGuardMiddleware` calls `get_settings()` directly — FastAPI DI override alone is insufficient.
**How to avoid:** Always include `with patch("app.main.get_settings", return_value=_mock_settings()):` for any route test that isn't `/setup`, `/health`, or static files.
**Warning signs:** Unexpected 302/503 in tests, `"Container needs configuration"` in response text.

### Pitfall 3: Confusing VALIDATION.md with VERIFICATION.md

**What goes wrong:** Phase 6 has a VERIFICATION.md. The planner might treat this as sufficient and skip creating a VALIDATION.md.
**Why it happens:** Both files document what was built, but they serve different purposes in the GSD workflow.
**How to avoid:** VERIFICATION.md is the post-execution verification report (what was built and confirmed working). VALIDATION.md is the forward-looking test contract (the sampling plan that guided execution). Phase 6 needs a VALIDATION.md created that documents what tests exist and marks the phase nyquist_compliant.
**Warning signs:** `ls .planning/milestones/v1.0-phases/06-wire-review-mode-and-cart-history/` shows no `06-VALIDATION.md`.

### Pitfall 4: lru_cache on get_settings

**What goes wrong:** Test sets environment variables but `get_settings()` still returns cached values from a previous call.
**Why it happens:** `app/config.py` uses `@lru_cache` on `get_settings()`. Any call made during module import caches the Settings object.
**How to avoid:** The `test_settings` fixture and `patch("app.main.get_settings")` pattern are the correct solution. Don't try to set env vars directly in tests.
**Warning signs:** Tests pass in isolation but fail when run together; settings values from a different test bleed in.

### Pitfall 5: anyio_backends warning is benign

**What goes wrong:** pytest outputs `PytestConfigWarning: Unknown config option: anyio_backends`. A researcher might treat this as a test infrastructure problem needing fixing.
**Why it happens:** The `anyio_backends` key in `pytest.ini` is read by the anyio plugin in a way that newer pytest versions consider unrecognized. It's cosmetic.
**How to avoid:** Do not modify pytest.ini to fix this warning. It does not affect test execution (197 tests pass with it present).

### Pitfall 6: Phase 3 VALIDATION.md per-task map uses pre-execution task IDs

**What goes wrong:** The Phase 3 VALIDATION.md lists task IDs `03-01-01` through `03-03-02` that map to plan tasks during execution. These IDs were planning artifacts.
**How to avoid:** When rewriting the map for the backfill VALIDATION.md, the task IDs should reflect the actual execution units (plans) that delivered each requirement, cross-referenced against the SUMMARY files.

---

## Code Examples

### Creating the Phase 6 VALIDATION.md from VERIFICATION.md

The Phase 6 VERIFICATION.md documents 4 behavioral truths with their test evidence. The VALIDATION.md must reference these:

```
# Source: .planning/milestones/v1.0-phases/06-wire-review-mode-and-cart-history/06-VERIFICATION.md
# Behaviors delivered:
# - SRCH-05: review_mode from AppConfig.review_mode propagates to Alpine x-data
#   Tests: test_review_mode_full_from_db, test_review_mode_exceptions_default
# - CART-03: /history shows CartSession+CartItem data, newest-first, with empty state
#   Tests: test_history_empty_state, test_history_with_sessions
```

### Running Phase-Scoped Tests

Each VALIDATION.md should document phase-scoped commands for the per-task entries:

```bash
# Phase 1 scoped
python -m pytest tests/test_health.py tests/test_wizard.py tests/test_oauth.py -x -q

# Phase 2 scoped
python -m pytest tests/test_shopping_flow.py tests/test_cart_service.py tests/test_llm_matching.py -x -q

# Phase 3 scoped
python -m pytest tests/test_receipt_parser.py tests/test_preference_service.py tests/test_preferences_flow.py -x -q

# Phase 4 scoped
python -m pytest tests/test_settings.py tests/test_llm_config.py -x -q

# Phase 5 scoped
python -m pytest tests/test_migrations.py -x -q

# Phase 6 scoped
python -m pytest tests/test_phase06.py -x -q

# Phase 7 scoped
python -m pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config tests/test_llm_config.py -x -q
```

---

## Environment Availability

Step 2.6: No new external dependencies. The test environment is fully operational. 197 tests pass at 2026-04-07 with pytest 8.4.2, Python 3.11 (Windows dev), Python 3.12 (Docker target).

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All tests | Yes | 8.4.2 | — |
| pytest-asyncio | Async tests | Yes | confirmed in use | — |
| pytest-env | SESSION_SECRET_KEY | Yes | confirmed in use | — |
| pytest-alembic | test_migrations.py | Yes | 0.12.1 (from Phase 5) | — |
| aiosqlite | In-memory DB | Yes | 0.22.1 | — |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `pytest.ini` (project root) |
| Quick run command | `python -m pytest tests/ -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | All 7 v1.0 phases have nyquist_compliant VALIDATION.md | meta/manual | `python -m pytest tests/ -q` (full suite green) | ✅ (197 passing) |
| VAL-01 (Phase 6 file) | Phase 6 VALIDATION.md created from scratch | meta | verify file exists + `nyquist_compliant: true` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/ -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `.planning/milestones/v1.0-phases/06-wire-review-mode-and-cart-history/06-VALIDATION.md` — Phase 6 VALIDATION.md must be created (currently missing)
- Any new test files written for behaviors with zero automated coverage (expected: 0-1 total, only if a genuine coverage gap is found during execution)

---

## Open Questions

1. **Phase 7 task ID mapping**
   - What we know: Phase 7 VALIDATION.md references tasks `07-01-01` and `07-01-02` pointing to `test_preferences_flow.py`, and these tests exist and pass.
   - What's unclear: Whether the planner should use the original task IDs from the 07-01-PLAN.md or create fresh task IDs for the backfill work.
   - Recommendation: Use a single backfill task ID per phase (e.g., `09-01-01` for "Phase 1 VALIDATION.md rewrite") rather than retroactively mapping to the original plan task IDs. The VALIDATION.md content should reference original requirement IDs (SRCH-01, etc.) not original task IDs.

2. **PREF-02 automation gap**
   - What we know: PREF-02 (parsed receipt items shown in editable table) has no automated test. The HTMX partial rendering is visual.
   - What's unclear: Whether an integration test asserting the HTML partial contains the right elements (brand names, editable inputs) counts as automated coverage.
   - Recommendation: Add a narrow integration test that asserts the upload response contains `<input` elements or editable fields. The Phase 3 VALIDATION.md should document this as manually verified for the UI behavior but automated for the HTTP response shape.

---

## Sources

### Primary (HIGH confidence)

- Direct file read: all 6 existing VALIDATION.md stubs (confirmed stub status)
- Direct file read: 18 test files in `tests/` (confirmed test functions and assertion patterns)
- Direct execution: `python -m pytest tests/ -q` output (197 passed, 4.94s, 2026-04-07)
- Direct file read: `tests/conftest.py` (confirmed fixture API)
- Direct file read: `pytest.ini` (confirmed asyncio_mode, anyio_backends, SESSION_SECRET_KEY)
- Direct file read: `06-VERIFICATION.md` (authoritative source for Phase 6 behaviors)
- Direct file read: CONTEXT.md (confirmed all implementation constraints)

### Secondary (MEDIUM confidence)

- Inferred from CONTEXT.md established patterns section (patch locations, lru_cache behavior)
- Inferred from SUMMARY files pattern (task ID structures used in plans 01-07)

---

## Metadata

**Confidence breakdown:**
- Phase audit: HIGH — all files directly read and test suite directly executed
- Test-to-phase mapping: HIGH — test file names and docstrings match phase behaviors
- Coverage gaps: HIGH — 197 tests verified passing; only Phase 6 VALIDATION.md is missing
- Wave 0 gaps: HIGH — one file definitively missing, 0-1 new test functions needed

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (stable domain, no external dependencies)
