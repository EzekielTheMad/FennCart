---
phase: 7
slug: llm-config-integration-fix
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-06
updated: 2026-04-08
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Rewritten from stub to nyquist_compliant: true on 2026-04-08 (Phase 09 plan 03).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (project root) |
| **asyncio_mode** | auto (pytest.ini) |
| **SESSION_SECRET_KEY** | Set via `pytest-env` in pytest.ini |
| **Quick run command** | `python -m pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config tests/test_llm_config.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config tests/test_llm_config.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | LLM-CONFIG | integration | `python -m pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config -x` | ✅ | ✅ green |
| 07-01-02 | 01 | 1 | LLM-CONFIG | integration | `python -m pytest tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config -x` | ✅ | ✅ green |
| 07-01-03 | 01 | 1 | LLM-CONFIG | unit | `python -m pytest tests/test_llm_config.py -x -q` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Test Function Reference

**tests/test_preferences_flow.py** (2 tests directly exercising LLM-CONFIG)
- `test_upload_receipt_uses_db_llm_config` — POST /preferences/upload reads provider and model from AppConfig (DB) via `get_active_llm_config(db)`, not env-var defaults. Verifies LLM-CONFIG for the receipt upload route.
- `test_nl_chat_uses_db_llm_config` — POST /preferences/nl-chat reads provider and model from AppConfig (DB) via `get_active_llm_config(db)`. Verifies LLM-CONFIG for the NL chat route.

**tests/test_llm_config.py** (4 tests covering the service layer)
- `test_env_fallback` — When no AppConfig row exists, `get_active_llm_config(db)` returns env-var defaults (LITELLM_PROVIDER, LITELLM_MODEL).
- `test_db_row_reads` — When AppConfig row exists, `get_active_llm_config(db)` returns the DB-stored provider and model.
- `test_encrypted_key_decryption` — API key stored encrypted in AppConfig is correctly decrypted when returned from `get_active_llm_config(db)`.
- `test_ollama_path` — Ollama provider returns base_url from AppConfig.ollama_base_url with no API key required.

*Note: `test_shopping_flow.py::test_match_returns_review_screen` also implicitly validates LLM-CONFIG for the shopping route via `get_active_llm_config` mock pattern, but the primary Phase 7 tests are the two explicit DB LLM config tests above.*

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. `tests/test_preferences_flow.py` and `tests/test_llm_config.py` existed and all 6 directly relevant tests passed at backfill time. `tests/conftest.py` provides the async DB session, DI overrides, and ASGI test client.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM provider hot-swap without restart | LLM-CONFIG | Requires running app and live provider change mid-session | 1. Start app 2. Configure LLM provider in Settings 3. Upload a receipt 4. Change provider in Settings 5. Upload another receipt 6. Verify second upload uses the new provider |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify entries
- [x] Sampling continuity: all 6 tests covered across 3 task entries
- [x] Wave 0 requirements satisfied (all test files exist and pass)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (backfilled 2026-04-08, Phase 09 plan 03)
