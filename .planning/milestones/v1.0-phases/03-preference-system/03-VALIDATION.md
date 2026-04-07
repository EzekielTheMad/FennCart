---
phase: 03
slug: preference-system
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-04
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio (confirmed in requirements-dev.txt and pytest.ini) |
| **Config file** | `pytest.ini` at project root |
| **Quick run command** | `pytest tests/test_preference_service.py tests/test_receipt_parser.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_preference_service.py tests/test_receipt_parser.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PREF-01, PREF-02 | unit | `pytest tests/test_receipt_parser.py -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | PREF-03 | unit | `pytest tests/test_preference_service.py -x` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | PREF-01 | integration | `pytest tests/test_preferences_flow.py::test_upload_receipt -x` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | PREF-05 | integration | `pytest tests/test_preferences_flow.py::test_preference_crud -x` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | PREF-04 | integration | `pytest tests/test_preferences_flow.py::test_nl_chat_confirm -x` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | PREF-06 | unit | `pytest tests/test_cart_service.py::test_process_list_with_preferences -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_preference_service.py` — unit tests for upsert, contradiction detection, preferences dict builder
- [ ] `tests/test_receipt_parser.py` — unit tests for pdfplumber extraction + Instructor parsing (mock LLM)
- [ ] `tests/test_preferences_flow.py` — integration tests for all preferences router endpoints

*Existing infrastructure (`tests/conftest.py`) covers async session and DI override fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Receipt PDF upload UI renders correctly | PREF-01 | HTMX partial rendering visual | Upload a PDF, verify editable table shows parsed items |
| Preference chat conversation flow is coherent | PREF-04 | Multi-turn LLM chat quality | Type "we switched to oat milk", verify clarification or confirmation appears |
| Tab switching between Upload/List/Chat modes | PREF-05 | Alpine.js tab UI interaction | Click each tab, verify correct panel shows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
