# Phase 7: LLM Config Integration Fix - Research

**Researched:** 2026-04-06
**Domain:** FastAPI router refactor — replacing direct env-var reads with DB-authoritative config calls
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Both receipt upload (`POST /preferences/upload-receipt`) and NL chat (`POST /preferences/chat`) must use `get_active_llm_config(db)` instead of `settings.llm_api_key`, `settings.llm_provider`, `settings.llm_model`. This matches the shopping router's existing pattern.
- **D-02:** The `AsyncSession` dependency (`db: AsyncSession = Depends(get_session)`) is already available in both endpoints — no new dependency injection needed.
- **D-03:** Fallback behavior matches existing `get_active_llm_config` logic: DB config first, env vars as fallback. No change to fallback semantics.

### Claude's Discretion

- Whether to pass `ollama_base_url` through to `parse_receipt_with_llm` and `parse_preference_nl`, or ignore it for now (shopping router ignores it too)
- Test structure — whether to add to existing `test_preferences_flow.py` or create a new test file
- Whether the `settings = get_settings()` line in each endpoint should be removed entirely or kept for non-LLM settings

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 7 is a mechanical two-site fix with zero new infrastructure. The project already has `get_active_llm_config(db)` fully implemented and tested in `app/services/llm_config.py`, and the shopping router already uses it as the reference pattern. The only work is applying that same pattern to two endpoints in `app/routers/preferences.py` that still call `settings.llm_*` directly.

The change is: add one import, call `get_active_llm_config(db)` before each LLM call, destructure the result dict, and pass `llm_cfg["api_key"]`, `llm_cfg["provider"]`, `llm_cfg["model"]` instead of `settings.llm_*`. The `settings = get_settings()` call in each endpoint can then be removed (neither endpoint uses `settings` for anything else in the LLM block). Tests need to verify that `get_active_llm_config` is what gets called, not `get_settings()`.

This phase closes the LLM config integration gap from the v1.0 milestone audit: user-configured LLM provider (set via the Settings page) now takes effect everywhere, not just in the shopping router.

**Primary recommendation:** Copy the `shopping_match()` pattern verbatim into both preferences endpoints — one `await get_active_llm_config(db)` call, destructure into `llm_cfg`, pass keys forward. No new patterns or infrastructure needed.

---

## Standard Stack

This phase introduces no new dependencies. All required tools are already in the project.

### Core (already installed)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| `app.services.llm_config` | project-local | DB-authoritative LLM config reader | Already implemented; tested |
| `get_active_llm_config` | project-local function | Returns `dict` with provider/model/api_key/ollama_base_url | Reference implementation in shopping router |
| FastAPI / SQLAlchemy AsyncSession | project stack | Async DI session | Already injected into both target endpoints |

**No new installs required.**

---

## Architecture Patterns

### The Fix Pattern (copy from shopping router)

The shopping router (`app/routers/shopping.py`, `shopping_match()`) is the reference implementation. Study lines 86-97:

```python
# Source: app/routers/shopping.py — shopping_match() lines 86-97
llm_cfg = await get_active_llm_config(session)

cart_service = CartService(
    ...
    llm_api_key=llm_cfg["api_key"],
    llm_provider=llm_cfg["provider"],
    llm_model=llm_cfg["model"],
    llm_ollama_base_url=llm_cfg["ollama_base_url"],
)
```

Applied to `upload_receipt()`:

```python
# BEFORE (lines ~210-218 in preferences.py):
settings = get_settings()
try:
    parsed = await parse_receipt_with_llm(
        raw_text,
        settings.llm_api_key,
        settings.llm_provider,
        settings.llm_model,
    )

# AFTER:
llm_cfg = await get_active_llm_config(db)
try:
    parsed = await parse_receipt_with_llm(
        raw_text,
        llm_cfg["api_key"],
        llm_cfg["provider"],
        llm_cfg["model"],
    )
```

Applied to `preference_chat()`:

```python
# BEFORE (lines ~410-418 in preferences.py):
settings = get_settings()
try:
    delta = await parse_preference_nl(
        llm_history,
        settings.llm_api_key,
        settings.llm_provider,
        settings.llm_model,
    )

# AFTER:
llm_cfg = await get_active_llm_config(db)
try:
    delta = await parse_preference_nl(
        llm_history,
        llm_cfg["api_key"],
        llm_cfg["provider"],
        llm_cfg["model"],
    )
```

### Import Addition

`preferences.py` currently imports `get_settings` but not `get_active_llm_config`. Add:

```python
from app.services.llm_config import get_active_llm_config
```

### `settings = get_settings()` Removal Decision

Verified by reading `preferences.py` fully: in both `upload_receipt()` and `preference_chat()`, the `settings` object is ONLY used for `settings.llm_api_key`, `settings.llm_provider`, and `settings.llm_model`. After the fix, `settings = get_settings()` in each endpoint is unused and should be removed to avoid confusion. The module-level `from app.config import get_settings` import can be retained (other endpoints use it indirectly via `get_settings` being wired through DI).

### ollama_base_url Decision

The `parse_receipt_with_llm` and `parse_preference_nl` function signatures accept only `api_key`, `provider`, `model` — no `ollama_base_url` parameter. The shopping router passes `ollama_base_url` to `CartService`, which may use it internally. Since neither LLM service function accepts `ollama_base_url`, there is nothing to pass through. The planner should note this explicitly so the implementer does not add a parameter that does not exist in the function signatures.

### Anti-Patterns to Avoid

- **Keeping `settings = get_settings()` after removing the only uses:** Dead code creates confusion about which config source is authoritative.
- **Introducing a new DI dependency for `llm_cfg`:** The `db` session is already available; `get_active_llm_config(db)` is a service function call, not a FastAPI dependency. No `Depends()` wrapping needed.
- **Duplicating logic from `get_active_llm_config`:** Do not inline DB reads or env var lookups; the service function handles all of that including Fernet decryption.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB-first LLM config with env fallback | Custom DB query + env var fallback in each endpoint | `get_active_llm_config(db)` | Already implements Fernet decrypt, fallback logic, and is unit-tested |
| LLM credential decryption | `get_or_create_fernet().decrypt(...)` inline | `get_active_llm_config(db)` | Decryption is encapsulated; duplicating it would create two sources of truth |

**Key insight:** The entire point of `get_active_llm_config` is to be the single, correct place where LLM config is assembled. Adding call sites to it is the right answer, not re-implementing any part of it.

---

## Common Pitfalls

### Pitfall 1: Leaving `settings = get_settings()` in place
**What goes wrong:** The line becomes dead code. Future developers may assume `settings` is still used and not notice the endpoint is now using DB config.
**Why it happens:** Cautious removal hesitancy.
**How to avoid:** After the fix, search for remaining `settings.` usages in the endpoint; if none, remove the `settings = get_settings()` line.
**Warning signs:** `settings` assigned but never read (linter will flag this with `F841` if ruff is enabled).

### Pitfall 2: Patching the wrong module in tests
**What goes wrong:** Test patches `app.config.get_active_llm_config` instead of `app.routers.preferences.get_active_llm_config`.
**Why it happens:** Incorrect patch target (standard Python mock pitfall — patch where the name is looked up, not where it's defined).
**How to avoid:** Patch `app.routers.preferences.get_active_llm_config` to intercept the call at the router's import boundary. Existing tests in `test_preferences_flow.py` already demonstrate the correct pattern with `app.routers.preferences.parse_receipt_with_llm` and `app.routers.preferences.parse_preference_nl`.

### Pitfall 3: `get_active_llm_config` not imported in test assertions
**What goes wrong:** Test patches `parse_receipt_with_llm` (as existing tests already do) and doesn't separately verify that `get_active_llm_config` was called.
**Why it happens:** The existing tests mock the downstream LLM service functions; testing the integration fix means also verifying the call chain changed.
**How to avoid:** Add a new test case (or extend existing) that seeds an `AppConfig` with a specific LLM provider and asserts that `parse_receipt_with_llm` / `parse_preference_nl` receive the DB-configured values, not the env-var values.

### Pitfall 4: Running the existing test suite without re-verifying behavior
**What goes wrong:** Existing `test_upload_receipt` and `test_nl_chat_*` tests pass but don't assert the config source — they mock the entire LLM function, so the fix is invisible to them.
**Why it happens:** Tests are written to verify behavior, not implementation detail.
**How to avoid:** Add at least one new test that seeds a DB AppConfig row with different LLM credentials than the env vars, and verifies the DB values are used. This is the integration gap test the phase is closing.

---

## Code Examples

### Verified: `get_active_llm_config` return shape
```python
# Source: app/services/llm_config.py — get_active_llm_config()
# Returns dict with exactly these keys:
{
    "provider": str,          # e.g. "anthropic", "openai", "ollama"
    "model": str,             # e.g. "claude-3-haiku-20240307"
    "api_key": str,           # decrypted if stored encrypted; env var if not in DB
    "ollama_base_url": str | None,  # set for ollama, None otherwise
}
```

### Verified: `parse_receipt_with_llm` signature
```python
# Source: app/services/receipt_parser.py — lines 46-50
async def parse_receipt_with_llm(
    raw_text: str,
    api_key: str,
    provider: str,
    model: str,
) -> ParsedReceipt:
```

### Verified: `parse_preference_nl` signature (defined in preferences.py)
```python
# Source: app/routers/preferences.py — lines 362-367
async def parse_preference_nl(
    conversation_history: list[dict],
    api_key: str,
    provider: str,
    model: str,
) -> PreferenceDelta:
```

### Correct test pattern (add to test_preferences_flow.py)
```python
# Test that DB-configured LLM provider is used, not env vars
@pytest.mark.anyio
async def test_upload_receipt_uses_db_llm_config(client, test_db):
    """POST /preferences/upload uses DB AppConfig LLM settings, not env vars."""
    # Seed AppConfig with a provider that differs from env default
    config = AppConfig(
        wizard_complete=True,
        store_id="70100153",
        store_name="Fry's Marketplace",
        llm_provider="openai",          # Different from env default "anthropic"
        llm_model="gpt-4o",             # Different from env default
    )
    test_db.add(config)
    await test_db.commit()

    mock_receipt = ParsedReceipt(items=[], parse_warnings=[])

    captured_provider = {}

    async def capture_parse(raw_text, api_key, provider, model):
        captured_provider["provider"] = provider
        captured_provider["model"] = model
        return mock_receipt

    with patch("app.main.get_settings", return_value=_mock_settings()):
        with patch("app.routers.preferences.extract_receipt_text",
                   return_value=("FRYS STORE #123\nItem1 $5.00\nItem2 $3.00\nTOTAL $8.00", [])):
            with patch("app.routers.preferences.parse_receipt_with_llm",
                       new=AsyncMock(side_effect=capture_parse)):
                await client.post(
                    "/preferences/upload",
                    files={"receipt_pdf": ("receipt.pdf", b"fake pdf", "application/pdf")},
                )

    assert captured_provider["provider"] == "openai"   # DB value, not env "anthropic"
    assert captured_provider["model"] == "gpt-4o"
```

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + anyio + httpx AsyncClient |
| Config file | `pytest.ini` (or `pyproject.toml [tool.pytest]`) |
| Quick run command | `pytest tests/test_preferences_flow.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

This phase has no formal requirement IDs (it is an integration fix). The success criteria map to tests as follows:

| Success Criterion | Behavior | Test Type | Automated Command | File Exists? |
|-------------------|----------|-----------|-------------------|--------------|
| Receipt upload uses DB LLM config | `parse_receipt_with_llm` receives DB provider/model | integration | `pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config -x` | Wave 0 (new) |
| NL chat uses DB LLM config | `parse_preference_nl` receives DB provider/model | integration | `pytest tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config -x` | Wave 0 (new) |
| Changing provider takes effect without restart | Same as above — DB read at request time | covered by above | (same) | Wave 0 (new) |
| Existing preference tests still pass | No regression in upload/chat happy paths | regression | `pytest tests/test_preferences_flow.py -x -q` | Yes |

### Sampling Rate
- **Per task commit:** `pytest tests/test_preferences_flow.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config` — verify DB LLM config used for receipt parsing
- [ ] `tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config` — verify DB LLM config used for NL chat

*(Existing test infrastructure is fully in place; only the two new test functions need to be added.)*

---

## Environment Availability

Step 2.6: SKIPPED — this phase is a pure code edit within the existing codebase. No external tools, services, or CLIs beyond the project's standard Python environment are required.

---

## Runtime State Inventory

Step 2.5: SKIPPED — this phase is a code fix, not a rename or migration. No runtime state, stored data, or OS-registered entries are involved.

---

## State of the Art

No new libraries or patterns. This phase applies patterns already proven in the same codebase.

| Old Approach (what the endpoints do now) | Correct Approach (what this fix implements) | Impact |
|------------------------------------------|---------------------------------------------|--------|
| `settings = get_settings(); settings.llm_provider` | `llm_cfg = await get_active_llm_config(db); llm_cfg["provider"]` | Provider changes in Settings page take effect without app restart |
| Env var only | DB-first with env var fallback | Consistent with shopping router |

---

## Open Questions

1. **Should `ollama_base_url` be threaded through to `parse_receipt_with_llm` and `parse_preference_nl`?**
   - What we know: Neither function currently accepts `ollama_base_url`; the shopping router passes it to `CartService` which may use it internally; the CONTEXT.md marks this as Claude's Discretion.
   - What's unclear: Whether Ollama users would need `ollama_base_url` forwarded to make receipt parsing / NL chat work with local models.
   - Recommendation: Do NOT add the parameter to `parse_receipt_with_llm` or `parse_preference_nl` in this phase. The LiteLLM/Instructor calls inside those functions use `instructor.from_provider(f"litellm/{model_str}", ...)` — the base URL for Ollama would need to be set as an environment variable (`OLLAMA_API_BASE`) at the LiteLLM level, not passed per-call. This is a separate concern and out of scope for this mechanical fix phase.

2. **Should `from app.config import get_settings` be removed from preferences.py entirely?**
   - What we know: After the fix, `get_settings` is no longer called inside `upload_receipt` or `preference_chat`. The module-level import still exists.
   - Recommendation: Keep the import. Removing it risks breaking the FastAPI DI override `app.dependency_overrides[get_settings]` pattern used in tests, and it costs nothing to leave. Do remove the two `settings = get_settings()` local variable assignments.

---

## Sources

### Primary (HIGH confidence)
- `app/services/llm_config.py` — `get_active_llm_config` source of truth (read directly)
- `app/routers/shopping.py` — Reference implementation of the correct pattern (read directly)
- `app/routers/preferences.py` — Confirmed locations of both `settings.llm_*` call sites at lines 210-218 and 410-418 (read directly)
- `app/services/receipt_parser.py` — Verified `parse_receipt_with_llm` signature (read directly)
- `tests/test_preferences_flow.py` — Existing test structure and patching patterns confirmed (read directly)
- `tests/conftest.py` — Test fixture infrastructure confirmed (read directly)

### Secondary (MEDIUM confidence)
- Python mock patching convention: patch at the import site (`app.routers.preferences.get_active_llm_config`), verified from existing test patterns in the same file.

---

## Project Constraints (from CLAUDE.md)

Directives the planner must verify:

| Directive | Impact on This Phase |
|-----------|---------------------|
| FastAPI + async SQLAlchemy | `get_active_llm_config(db)` is async; `await` is required |
| SQLModel / aiosqlite | `db: AsyncSession` — already present in both endpoints; no change |
| LiteLLM + Instructor | Both LLM service functions already use Instructor; no change to LLM call internals |
| No env var default values baked in | Fix ensures DB config is authoritative; env vars remain fallback only |
| `--workers 1` Uvicorn | No impact on this fix |
| GSD workflow enforcement | CLAUDE.md requires all edits go through a GSD command — this phase plan will satisfy that |

---

## Metadata

**Confidence breakdown:**
- What needs to change: HIGH — read the source files directly; both call sites confirmed
- How to change it: HIGH — shopping router is the verified reference; pattern is identical
- Test strategy: HIGH — existing test patterns in test_preferences_flow.py are the model; new tests follow same structure
- Side effects / risk: HIGH (none) — mechanical substitution with no new infrastructure

**Research date:** 2026-04-06
**Valid until:** N/A — this is a codebase-internal fix; no external library versions to expire
