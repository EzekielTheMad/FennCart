---
phase: 6
slug: wire-review-mode-and-cart-history
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-07
updated: 2026-04-08
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Created from scratch on 2026-04-08 (Phase 09 plan 03). VERIFICATION.md was the authoritative source for delivered behaviors.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (project root) |
| **asyncio_mode** | auto (pytest.ini) |
| **SESSION_SECRET_KEY** | Set via `pytest-env` in pytest.ini |
| **Quick run command** | `python -m pytest tests/test_phase06.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_phase06.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | SRCH-05 | integration | `python -m pytest tests/test_phase06.py::test_review_mode_full_from_db -x` | ✅ | ✅ green |
| 06-01-02 | 01 | 1 | SRCH-05 | integration | `python -m pytest tests/test_phase06.py::test_review_mode_exceptions_default -x` | ✅ | ✅ green |
| 06-01-03 | 01 | 1 | CART-03 | integration | `python -m pytest tests/test_phase06.py::test_history_empty_state -x` | ✅ | ✅ green |
| 06-01-04 | 01 | 1 | CART-03 | integration | `python -m pytest tests/test_phase06.py::test_history_with_sessions -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Test Function Reference

**tests/test_phase06.py** (4 tests, 8 cases with asyncio+trio backends)
- `test_review_mode_full_from_db` — When AppConfig.review_mode="full", the review_screen Alpine x-data contains `mode: 'full'`. Verifies SRCH-05 (review_mode reads from DB, not hardcoded).
- `test_review_mode_exceptions_default` — When AppConfig.review_mode is default ("exceptions"), Alpine x-data contains `mode: 'exceptions'`. Verifies SRCH-05 fallback path.
- `test_history_empty_state` — GET /history with no CartSessions returns 200 with "No shopping history yet" heading and "Start shopping" CTA link. Verifies CART-03 empty state.
- `test_history_with_sessions` — GET /history with seeded CartSession+CartItem data returns 200 showing session count, item descriptions, and formatted totals newest-first. Verifies CART-03 data display.

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. `tests/test_phase06.py` existed and all 8 cases (4 tests × 2 async backends) passed at backfill time. `tests/conftest.py` provides the async DB session, DI overrides, and ASGI test client. The `patch("app.main.get_settings")` pattern handles SetupGuardMiddleware bypass.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Review mode toggle visual state | SRCH-05 | Alpine.js DOM binding requires browser rendering | In Settings, set Review Mode to "Full". Submit a shopping list. Verify review screen opens with "Full review" tab active (no click needed). |
| History expand/collapse animation | CART-03 | `x-transition` CSS animation requires browser rendering | Navigate to /history with at least one session. Click a session row. Verify item detail panel expands with animation and chevron rotates 180°. |
| Date formatting in Docker (Linux) | CART-03 | `strftime('%-d')` format differs Linux vs Windows | In production Docker container, navigate to /history. Verify dates display as "Apr 5, 2026" (no leading zero on day). |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify entries
- [x] Sampling continuity: all 4 test functions covered
- [x] Wave 0 requirements satisfied (test_phase06.py exists and passes)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (backfilled 2026-04-08, Phase 09 plan 03)
