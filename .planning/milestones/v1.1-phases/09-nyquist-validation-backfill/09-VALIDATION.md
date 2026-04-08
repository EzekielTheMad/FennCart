---
phase: 9
slug: nyquist-validation-backfill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python -m pytest tests/ -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | VAL-01 | meta | `python -m pytest tests/ -q` + verify VALIDATION.md files | partial | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `.planning/milestones/v1.0-phases/06-wire-review-mode-and-cart-history/06-VALIDATION.md` — Phase 6 file must be created from scratch

*All other VALIDATION.md files exist but are stubs needing rewrite.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Each VALIDATION.md has nyquist_compliant: true | VAL-01 | Frontmatter check | `grep "nyquist_compliant: true" .planning/milestones/v1.0-phases/*/*.md` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
