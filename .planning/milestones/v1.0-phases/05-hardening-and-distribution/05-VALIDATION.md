---
phase: 5
slug: hardening-and-distribution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-06
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` (exists) |
| **Quick run command** | `python -m pytest tests/test_migrations.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | SC-1 (README) | manual | N/A — human follow-along | N/A | ⬜ pending |
| 05-01-02 | 01 | 1 | SC-2 (Docker) | smoke | `docker build .` | ❌ manual | ⬜ pending |
| 05-02-01 | 02 | 1 | SC-4 (Migrations) | automated | `python -m pytest tests/test_migrations.py -x -q` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 2 | SC-3 (OAuth Docker) | manual | N/A — env var docs | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_migrations.py` — pytest-alembic sequential upgrade test (D-06)
- [ ] `pytest-alembic==0.12.1` must be added to `requirements-dev.txt`

*Existing test infrastructure covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| README walkthrough | SC-1 | Requires fresh machine, human judgment | Follow README on a machine without prior setup |
| OAuth redirect in Docker | SC-3 | Requires real Kroger credentials + browser | Run `docker compose up`, complete OAuth flow, verify no redirect errors |
| Docker build from cold pull | SC-2 | Requires clean Docker state | `docker system prune -a`, then `docker build .` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
