---
phase: 8
slug: code-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + anyio + httpx |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/test_shopping_flow.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_shopping_flow.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | ERR-01 | integration | `python -m pytest tests/test_session_key_guard.py -x` | Wave 0 gap | pending |
| 08-01-02 | 01 | 1 | DOC-01 | manual/smoke | `grep -c "EzekielTheMad/FennCart" README.md && grep -c "MIT License" README.md` | manual | pending |
| 08-01-03 | 01 | 1 | QUAL-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_review_screen_no_x_datastack -x` | Wave 0 gap | pending |
| 08-01-04 | 01 | 1 | QUAL-02 | integration | `python -m pytest tests/test_shopping_flow.py::test_swap_endpoint_removed -x` | Wave 0 gap | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_session_key_guard.py` — covers ERR-01: tests that a missing/default SESSION_SECRET_KEY causes session_error.html to render instead of crashing
- [ ] `tests/test_shopping_flow.py::test_review_screen_no_x_datastack` — covers QUAL-01: confirms template renders without _x_dataStack references
- [ ] `tests/test_shopping_flow.py::test_swap_endpoint_removed` — covers QUAL-02: 404/405 check that POST /shopping/swap is gone

*Existing `test_shopping_flow.py` tests (1-9) cover the shopping flow end-to-end. New tests should be added to that file or a new dedicated file.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README contains correct GitHub URL and "MIT License" | DOC-01 | Simple grep check — not worth a test file | `grep -c "EzekielTheMad/FennCart" README.md && grep -c "MIT License" README.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
