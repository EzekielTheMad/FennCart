---
phase: 4
slug: multi-provider-llm-and-settings
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `tests/conftest.py` |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=long` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=long`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | LLM-02 | unit | `python -m pytest tests/test_settings.py -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | LLM-02 | unit | `python -m pytest tests/test_llm_provider.py -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | LLM-02 | integration | `python -m pytest tests/test_settings_integration.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_settings.py` — stubs for settings CRUD and provider switching
- [ ] `tests/test_llm_provider.py` — stubs for multi-provider config and test_connection
- [ ] `tests/test_settings_integration.py` — stubs for end-to-end settings flow

*Existing pytest infrastructure covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Settings sidebar navigation renders correctly | LLM-02 | Visual layout verification | Navigate to /settings, verify sidebar sections (LLM, Store, Account, Preferences) render and switch content |
| Provider dropdown dynamically changes form fields | LLM-02 | HTMX dynamic interaction | Select each provider in dropdown, verify correct fields appear (API key vs endpoint URL) |
| API key masked input with reveal toggle | LLM-02 | Browser password field behavior | Enter API key, verify masked, click eye icon, verify revealed |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
