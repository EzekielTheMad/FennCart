# Roadmap: Fenn Cart

**Project:** Fenn Cart
**Core Value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.
**Created:** 2026-04-02

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-7 (shipped 2026-04-07) — [archive](milestones/v1.0-ROADMAP.md)
- **v1.1 Tech Debt Cleanup** — Phases 8-9 (active)

---

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-7) — SHIPPED 2026-04-07</summary>

- [x] Phase 1: Foundation and Auth (4/4 plans) — completed 2026-04-03
- [x] Phase 2: Core Loop (4/4 plans) — completed 2026-04-03
- [x] Phase 3: Preference System (4/4 plans) — completed 2026-04-06
- [x] Phase 4: Multi-Provider LLM and Settings (3/3 plans) — completed 2026-04-06
- [x] Phase 5: Hardening and Distribution (2/2 plans) — completed 2026-04-06
- [x] Phase 6: Wire Review Mode and Cart History (1/1 plan) — completed 2026-04-06
- [x] Phase 7: LLM Config Integration Fix (1/1 plan) — completed 2026-04-06

</details>

**v1.1 Tech Debt Cleanup**

- [x] **Phase 8: Code Cleanup** - Fix fragile code, remove dead code, replace placeholder content (completed 2026-04-07)
- [ ] **Phase 9: Nyquist Validation Backfill** - Complete VALIDATION.md coverage across all v1.0 phases

---

## Phase Details

### Phase 8: Code Cleanup
**Goal**: The codebase is free of known fragility, dead code, and placeholder content
**Depends on**: Nothing (standalone cleanup)
**Requirements**: ERR-01, DOC-01, QUAL-01, QUAL-02
**Plans:** 2/2 plans complete

Plans:
- [x] 08-01-PLAN.md — Session key startup guard, README/LICENSE updates, TemplateResponse API fixes
- [x] 08-02-PLAN.md — Alpine.js state-lift for product swap, dead code removal

**Success Criteria** (what must be TRUE):
  1. A container started without SESSION_SECRET_KEY shows a helpful error page with setup instructions instead of crash-looping
  2. README displays "MIT License" and a real GitHub repository URL, not placeholder text
  3. Product swap in the review screen works correctly and no longer touches Alpine._x_dataStack
  4. POST /shopping/swap endpoint is absent from the codebase and no unused imports or stale routes remain in any router

### Phase 9: Nyquist Validation Backfill
**Goal**: Every v1.0 phase has a documented VALIDATION.md with passing test coverage
**Depends on**: Phase 8 (dead code removal may affect test surface)
**Requirements**: VAL-01
**Plans:** 3 plans

Plans:
- [ ] 09-01-PLAN.md — Rewrite VALIDATION.md for Phases 1, 2, 3 (Foundation, Core Loop, Preferences)
- [ ] 09-02-PLAN.md — Rewrite VALIDATION.md for Phases 4, 5 (LLM Settings, Hardening)
- [ ] 09-03-PLAN.md — Create Phase 6 VALIDATION.md, rewrite Phase 7, full suite confirmation

**Success Criteria** (what must be TRUE):
  1. Each of the 7 v1.0 phases has a non-stub VALIDATION.md file covering its observable behaviors
  2. All tests referenced or implied by VALIDATION.md files pass under `pytest`
  3. No phase is left with a missing or empty VALIDATION.md

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation and Auth | v1.0 | 4/4 | Complete | 2026-04-03 |
| 2. Core Loop | v1.0 | 4/4 | Complete | 2026-04-03 |
| 3. Preference System | v1.0 | 4/4 | Complete | 2026-04-06 |
| 4. Multi-Provider LLM and Settings | v1.0 | 3/3 | Complete | 2026-04-06 |
| 5. Hardening and Distribution | v1.0 | 2/2 | Complete | 2026-04-06 |
| 6. Wire Review Mode and Cart History | v1.0 | 1/1 | Complete | 2026-04-06 |
| 7. LLM Config Integration Fix | v1.0 | 1/1 | Complete | 2026-04-06 |
| 8. Code Cleanup | v1.1 | 2/2 | Complete   | 2026-04-07 |
| 9. Nyquist Validation Backfill | v1.1 | 0/3 | Not started | - |

---
*Created: 2026-04-02*
*Last updated: 2026-04-07 after Phase 9 planning*
