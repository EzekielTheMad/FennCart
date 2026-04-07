# Phase 7: LLM Config Integration Fix - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Ensure all LLM-using endpoints respect the user's configured provider from Settings (stored in AppConfig DB table), not just environment variables. Two endpoints in `app/routers/preferences.py` still read `settings.llm_*` directly instead of calling `get_active_llm_config(db)`.

This is a mechanical fix — applying Phase 4's established pattern to two missed call sites.

</domain>

<decisions>
## Implementation Decisions

### Integration Pattern
- **D-01:** Both receipt upload (`POST /preferences/upload-receipt`) and NL chat (`POST /preferences/chat`) must use `get_active_llm_config(db)` instead of `settings.llm_api_key`, `settings.llm_provider`, `settings.llm_model`. This matches the shopping router's existing pattern.
- **D-02:** The `AsyncSession` dependency (`db: AsyncSession = Depends(get_session)`) is already available in both endpoints — no new dependency injection needed.
- **D-03:** Fallback behavior matches existing `get_active_llm_config` logic: DB config first, env vars as fallback. No change to fallback semantics.

### Claude's Discretion
- Whether to pass `ollama_base_url` through to `parse_receipt_with_llm` and `parse_preference_nl`, or ignore it for now (shopping router ignores it too)
- Test structure — whether to add to existing `test_preferences_flow.py` or create a new test file
- Whether the `settings = get_settings()` line in each endpoint should be removed entirely or kept for non-LLM settings

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LLM Config Pattern (source of truth)
- `app/services/llm_config.py` — `get_active_llm_config(db)` function: DB-first with env var fallback
- `app/routers/shopping.py` — Reference implementation of the correct pattern (already uses `get_active_llm_config`)
- `app/models/config_model.py` — `AppConfig` model with `llm_provider`, `llm_model`, `llm_api_key_encrypted` fields

### Endpoints to Fix
- `app/routers/preferences.py` — Two call sites using `settings.llm_*` directly:
  - Line ~210-217: `parse_receipt_with_llm(raw_text, settings.llm_api_key, settings.llm_provider, settings.llm_model)`
  - Line ~410-417: `parse_preference_nl(llm_history, settings.llm_api_key, settings.llm_provider, settings.llm_model)`

### LLM Service Functions
- `app/services/receipt_parser.py` — `parse_receipt_with_llm()` signature
- `app/services/preference_nl.py` — `parse_preference_nl()` signature

### Tests
- `tests/test_preferences_flow.py` — Existing preference flow tests
- `tests/test_llm_config.py` — Existing LLM config tests

### Audit Source
- `.planning/v1.0-MILESTONE-AUDIT.md` — Gap definition and evidence

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_active_llm_config(db)` — Already exists in `app/services/llm_config.py`, returns `dict` with `provider`, `model`, `api_key`, `ollama_base_url`
- `get_session` — AsyncSession dependency already imported and used in preferences router
- Shopping router pattern — Exact template for how to call `get_active_llm_config` and destructure the result

### Established Patterns
- DB-authoritative config: `get_active_llm_config(db)` reads AppConfig row, falls back to env vars
- Fernet decryption for encrypted API keys handled inside `get_active_llm_config`
- Shopping router destructures as: `llm_cfg = await get_active_llm_config(db)` then passes `llm_cfg["api_key"]`, `llm_cfg["provider"]`, `llm_cfg["model"]`

### Integration Points
- `preferences.py` imports `get_settings` — needs additional import of `get_active_llm_config`
- Both endpoints already have `db: AsyncSession` parameter — no DI changes needed

</code_context>

<specifics>
## Specific Ideas

- This is a two-site mechanical fix: replace `settings.llm_*` with `llm_cfg[*]` from `get_active_llm_config(db)`
- Shopping router is the exact reference implementation to copy from

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-llm-config-integration-fix*
*Context gathered: 2026-04-06*
