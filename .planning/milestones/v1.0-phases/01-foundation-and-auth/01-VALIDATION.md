---
phase: 1
slug: foundation-and-auth
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-02
updated: 2026-04-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Backfilled to nyquist_compliant: true on 2026-04-08 (Phase 09 plan 01).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (project root) |
| **asyncio_mode** | auto (pytest.ini) |
| **SESSION_SECRET_KEY** | Set via `pytest-env` in pytest.ini |
| **Quick run command** | `python -m pytest tests/test_health.py tests/test_wizard.py tests/test_oauth.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_health.py tests/test_wizard.py tests/test_oauth.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | SETUP-01 | integration | `python -m pytest tests/test_health.py::test_health_endpoint -x` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | SETUP-01 | integration | `python -m pytest tests/test_wizard.py::test_wizard_setup_page_renders -x` | ✅ | ✅ green |
| 01-01-03 | 01 | 1 | SETUP-01 | integration | `python -m pytest tests/test_wizard.py::test_wizard_redirects_when_incomplete -x` | ✅ | ✅ green |
| 01-01-04 | 01 | 1 | SETUP-02, D-02 | integration | `python -m pytest tests/test_wizard.py::test_wizard_resumable -x` | ✅ | ✅ green |
| 01-01-05 | 01 | 1 | SETUP-02 | integration | `python -m pytest tests/test_wizard.py::test_validate_llm_success -x` | ✅ | ✅ green |
| 01-02-01 | 02 | 1 | SETUP-04, D-06 | unit | `python -m pytest tests/test_oauth.py::test_store_token_encrypts -x` | ✅ | ✅ green |
| 01-02-02 | 02 | 1 | SETUP-04 | unit | `python -m pytest tests/test_oauth.py::test_get_decrypted_token -x` | ✅ | ✅ green |
| 01-02-03 | 02 | 1 | SETUP-04 | unit | `python -m pytest tests/test_oauth.py::test_proactive_refresh_within_60s -x` | ✅ | ✅ green |
| 01-02-04 | 02 | 1 | SETUP-04 | unit | `python -m pytest tests/test_oauth.py::test_no_refresh_when_token_fresh -x` | ✅ | ✅ green |
| 01-02-05 | 02 | 1 | SETUP-03 | integration | `python -m pytest tests/test_oauth.py::test_auth_callback_marks_wizard_complete -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Test Function Reference

**tests/test_health.py** (1 test)
- `test_health_endpoint` — GET /health returns 200 `{"status": "ok"}`. Proxy for SETUP-01 (app is reachable).

**tests/test_wizard.py** (4 tests)
- `test_wizard_redirects_when_incomplete` — GET / redirects to /setup when wizard_complete=False (SETUP-01).
- `test_wizard_setup_page_renders` — GET /setup returns 200 with wizard content (SETUP-01).
- `test_validate_llm_success` — POST /setup/validate-llm advances wizard step on success (SETUP-02).
- `test_wizard_resumable` — Wizard resumes from last completed step when revisited (SETUP-02, D-02).

**tests/test_oauth.py** (5 tests)
- `test_store_token_encrypts` — Tokens stored with Fernet encryption; plaintext not in DB (D-06 / SETUP-04).
- `test_get_decrypted_token` — Decrypted token matches original plaintext (SETUP-04).
- `test_proactive_refresh_within_60s` — Token within 60s of expiry triggers proactive refresh (SETUP-04).
- `test_no_refresh_when_token_fresh` — Fresh token (600s remaining) does NOT call refresh (SETUP-04).
- `test_auth_callback_marks_wizard_complete` — OAuth callback sets wizard_complete=True and redirects to /tour (SETUP-03).

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. All test files (`tests/test_health.py`, `tests/test_wizard.py`, `tests/test_oauth.py`) existed and passed (10/10) at backfill time. `tests/conftest.py` provides the async DB session, DI overrides, and ASGI test client.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Kroger OAuth PKCE round-trip | SETUP-03 | Requires real Kroger redirect + browser interaction | Start container, click Authorize, complete Kroger login, verify redirect back to app |
| Docker compose wizard reachable | SETUP-01 | Requires Docker runtime | Run `docker compose up`, open browser to `http://localhost:8000`, verify wizard renders |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify entries
- [x] Sampling continuity: all 10 tests covered
- [x] Wave 0 requirements satisfied (all test files exist)
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (backfilled 2026-04-08, Phase 09 plan 01)
