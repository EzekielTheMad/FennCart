---
phase: 5
slug: hardening-and-distribution
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-06
updated: 2026-04-08
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (project root) |
| **Quick run command** | `python -m pytest tests/test_migrations.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_migrations.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

### test_migrations.py — 2 tests covering SC-4 (Alembic migration chain)

| Task | Test Function | Requirement | Test Type | Command | File Exists | Status |
|------|---------------|-------------|-----------|---------|-------------|--------|
| 05-02 | `test_migrations_upgrade_to_head` | SC-4 | automated | `python -m pytest tests/test_migrations.py::test_migrations_upgrade_to_head -x` | ✅ | ✅ green |
| 05-02 | `test_model_definitions_match_ddl` | SC-4 | automated | `python -m pytest tests/test_migrations.py::test_model_definitions_match_ddl -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**SC-1, SC-2, SC-3:** These requirements are correctly manual-only. See Manual-Only Verifications section below.

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. `tests/test_migrations.py` exists and both tests pass. SC-1, SC-2, and SC-3 require Docker runtime and/or real Kroger credentials — they are manual-only by necessity, not a coverage gap.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README contains correct content | SC-1 | Static file content — correctness is a human judgment call verified at review time | Read README.md and verify setup instructions, quickstart, and credential documentation are accurate |
| Docker image builds and runs | SC-2 | Requires Docker daemon — cannot be run in standard test environment | `docker build -t fenncart . && docker run --rm fenncart python -c "import app"` |
| OAuth works in Docker container | SC-3 | Requires real Kroger credentials + browser — cannot be mocked in automated tests | Start container with real credentials via `docker compose up`, complete OAuth flow, verify no redirect errors |

---

## Phase-Scoped Test Command

```bash
python -m pytest tests/test_migrations.py -x -q
```

**Expected:** 2 passed in < 5 seconds

---

## Validation Sign-Off

- [x] All automated tasks have verify entries in per-task map
- [x] SC-1, SC-2, SC-3 correctly documented as manual-only (require Docker/credentials)
- [x] Wave 0 covers all gaps (none — test_migrations.py exists and passes)
- [x] No watch-mode flags
- [x] Feedback latency < 5s (confirmed 4.94s full suite)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved — 2026-04-08
