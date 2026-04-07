# Requirements: Fenn Cart v1.1

**Defined:** 2026-04-07
**Milestone:** v1.1 Tech Debt Cleanup
**Core Value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

## v1.1 Requirements

Requirements for tech debt cleanup. Each maps to roadmap phases.

### Error Handling

- [x] **ERR-01**: App shows a helpful error page when SESSION_SECRET_KEY is missing instead of crash-looping the container

### Documentation

- [x] **DOC-01**: README contains actual license (MIT) and correct GitHub repository URL

### Code Quality

- [x] **QUAL-01**: Product swap in review screen uses stable Alpine.js API instead of Alpine._x_dataStack internal
- [x] **QUAL-02**: Dead code removed (POST /shopping/swap endpoint, unused imports, stale routes across all routers)

### Validation

- [ ] **VAL-01**: All v1.0 phases have Nyquist-compliant VALIDATION.md with passing test coverage

## Future Requirements

Deferred to future milestones.

- **HIST-01**: User can view past shopping sessions with items, prices, and dates
- **HIST-02**: User can reorder items from a previous shopping session
- **HIST-03**: Shopping history feeds into preference profile updates over time
- **ADV-01**: User can import shopping lists from external sources (Apple Notes, Google Keep)
- **ADV-02**: App suggests items based on purchase frequency patterns

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| New user-facing features | This is a cleanup milestone only |
| UI redesign or polish | Defer to a UX milestone |
| Performance optimization | No measured bottleneck yet |
| Additional LLM providers | Current 3 (Claude, OpenAI, Ollama) sufficient |
| Router-local Jinja2Templates refactor | Marked as revisit but functional, defer to avoid churn |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ERR-01 | Phase 8 | Complete |
| DOC-01 | Phase 8 | Complete |
| QUAL-01 | Phase 8 | Complete |
| QUAL-02 | Phase 8 | Complete |
| VAL-01 | Phase 9 | Pending |

**Coverage:**
- v1.1 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0

---
*Requirements defined: 2026-04-07*
*Traceability updated: 2026-04-07 (roadmap creation)*
