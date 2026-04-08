---
phase: 4
slug: multi-provider-llm-and-settings
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
updated: 2026-04-08
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (project root) |
| **Quick run command** | `python -m pytest tests/test_settings.py tests/test_llm_config.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_settings.py tests/test_llm_config.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

### test_settings.py — 13 tests covering LLM-02 settings UI and persistence

| Task | Test Function | Requirement | Test Type | Command | File Exists | Status |
|------|---------------|-------------|-----------|---------|-------------|--------|
| 04-01 | `test_settings_page_renders` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_settings_page_renders -x` | ✅ | ✅ green |
| 04-01 | `test_settings_section_llm` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_settings_section_llm -x` | ✅ | ✅ green |
| 04-01 | `test_settings_section_store` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_settings_section_store -x` | ✅ | ✅ green |
| 04-01 | `test_settings_section_account` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_settings_section_account -x` | ✅ | ✅ green |
| 04-01 | `test_settings_section_preferences` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_settings_section_preferences -x` | ✅ | ✅ green |
| 04-02 | `test_save_llm_settings` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_save_llm_settings -x` | ✅ | ✅ green |
| 04-02 | `test_save_llm_invalid_key` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_save_llm_invalid_key -x` | ✅ | ✅ green |
| 04-02 | `test_ollama_config` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_ollama_config -x` | ✅ | ✅ green |
| 04-02 | `test_save_llm_blank_key_keeps_existing` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_save_llm_blank_key_keeps_existing -x` | ✅ | ✅ green |
| 04-01 | `test_search_stores` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_search_stores -x` | ✅ | ✅ green |
| 04-01 | `test_select_store` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_select_store -x` | ✅ | ✅ green |
| 04-01 | `test_save_preferences` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_save_preferences -x` | ✅ | ✅ green |
| 04-02 | `test_llm_hotswap` | LLM-02 | integration | `python -m pytest tests/test_settings.py::test_llm_hotswap -x` | ✅ | ✅ green |

### test_llm_config.py — 4 tests covering LLM-02 service layer

| Task | Test Function | Requirement | Test Type | Command | File Exists | Status |
|------|---------------|-------------|-----------|---------|-------------|--------|
| 04-02 | `test_llm_config_env_fallback` | LLM-02 | unit | `python -m pytest tests/test_llm_config.py::test_llm_config_env_fallback -x` | ✅ | ✅ green |
| 04-02 | `test_llm_config_from_db` | LLM-02 | unit | `python -m pytest tests/test_llm_config.py::test_llm_config_from_db -x` | ✅ | ✅ green |
| 04-02 | `test_llm_config_encrypted_key` | LLM-02 | unit | `python -m pytest tests/test_llm_config.py::test_llm_config_encrypted_key -x` | ✅ | ✅ green |
| 04-02 | `test_llm_config_ollama` | LLM-02 | unit | `python -m pytest tests/test_llm_config.py::test_llm_config_ollama -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. All 17 tests across `test_settings.py` (13 tests) and `test_llm_config.py` (4 tests) exist and pass. No new test files are needed for Phase 4.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Settings sidebar navigation renders correctly | LLM-02 | Visual layout verification — sidebar section highlighting requires browser render | Navigate to /settings, verify sidebar sections (LLM, Store, Account, Preferences) render and switch content |
| Provider dropdown dynamically changes form fields | LLM-02 | HTMX dynamic interaction — field visibility toggling is Alpine.js/HTMX behavior | Select each provider in dropdown, verify correct fields appear (API key vs endpoint URL) |
| API key masked input with reveal toggle | LLM-02 | Browser password field behavior — visual masking cannot be asserted via HTTP response | Enter API key, verify masked display, click eye icon, verify revealed |

---

## Phase-Scoped Test Command

```bash
python -m pytest tests/test_settings.py tests/test_llm_config.py -x -q
```

**Expected:** 17 passed in < 5 seconds

---

## Validation Sign-Off

- [x] All tasks have automated verify entries in per-task map
- [x] Sampling continuity: no consecutive tasks without automated verify
- [x] Wave 0 covers all gaps (none — all tests exist)
- [x] No watch-mode flags
- [x] Feedback latency < 5s (confirmed 4.94s full suite)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved — 2026-04-08
