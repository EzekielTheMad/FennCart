# Phase 3: Preference System - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver receipt PDF upload and parsing, a living preference profile built from purchase history, preference-compensated product matching that feeds into the existing Phase 2 matching pipeline, and both natural language (chat-style) and manual preference editing. After this phase, the LLM's product matches visibly reflect the user's buying habits.

</domain>

<decisions>
## Implementation Decisions

### Receipt Upload & Parsing
- **D-01:** Upload approach is Claude's discretion — single or batch, Claude picks what fits the HTMX/SSR pattern best.
- **D-02:** Editable table after parsing — show parsed items (name, brand, size, qty, price) in an editable table. User can fix OCR errors, remove unwanted items, then confirm to save to preference history.
- **D-03:** Bad receipt handling is Claude's discretion — show partial results with warnings, reject, or hybrid approach.

### Preference Profile Structure
- **D-04:** Preference weighting approach is Claude's discretion — simple count-based, recency-weighted, or hybrid. Must support PREF-03 (distinguish recurring preferences from one-off substitutions).
- **D-05:** Flat list organization — each preference is a standalone entry (e.g., "prefers Tillamook cheddar"). No category-based grouping. Search/filter for browsing.
- **D-06:** Flag-and-ask on contradictions — when a new receipt contradicts existing preferences (e.g., different brand than usual), detect the brand switch and ask the user: "New preference or one-time substitution?" Do not silently auto-update.

### NL Preference Updates
- **D-07:** Chat-style interface — conversational back-and-forth for natural language preference updates. LLM can ask clarifying questions ("Which brand of oat milk?", "Replace completely or add as alternative?").
- **D-08:** Always confirm before applying — show the interpreted change ("Replace whole milk with oat milk") and require explicit user approval before saving to the profile.

### Preferences UI & Management
- **D-09:** Page layout is Claude's discretion — Claude picks the structure that fits the dark sidebar nav and HTMX partial pattern. Must accommodate three modes: receipt upload, NL chat, and manual preference list.
- **D-10:** Editing pattern is Claude's discretion — inline editing vs drawer/modal, Claude picks what works.
- **D-11:** Bulk delete with checkboxes — checkbox per preference entry, select multiple, bulk delete button. Useful for cleaning up after a bad receipt upload or starting fresh.

### Claude's Discretion
- Receipt upload UX approach (single vs batch, progress indicator style)
- Bad/partial receipt error handling pattern
- Preference weighting algorithm (must satisfy PREF-03: recurring vs one-off)
- Preferences page layout (must fit sidebar nav pattern from Phase 1)
- Individual preference editing pattern (inline vs modal/drawer)
- Chat interface implementation (HTMX polling vs WebSocket-like pattern for conversational flow)
- How preference data is serialized for the `preferences` parameter in `match_products()`

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Kroger API & Constraints
- `FennCartPitch.md` — Kroger API details, TOS constraints. Customer search data must not be persistently stored (TOS) but preference profiles derived from user-provided receipts are fine.
- `.planning/research/PITFALLS.md` — API pitfalls and prevention strategies

### Architecture & Stack
- `.planning/research/STACK.md` — Verified stack with versions
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow patterns
- `CLAUDE.md` — Technology stack constraints, version pins. pdfplumber 0.11.9 for PDF parsing, Instructor 1.14.5 for structured LLM output.

### Phase 2 Integration Points (established code to extend)
- `app/services/llm_service.py` — Has `match_products(list_items, kroger_results, preferences=None)` — the `preferences` parameter is the Phase 3 hook (D-07 from Phase 2). This is the integration point for preference-compensated matching.
- `app/services/cart_service.py` — CartService.process_list() orchestrates the pipeline. Must pass preference data through to match_products().
- `app/schemas/shopping.py` — Shared Pydantic schemas for the matching pipeline.
- `templates/pages/preferences.html` — Placeholder page to be replaced with actual preferences UI.
- `templates/base.html` — Base template with dark sidebar nav, HTMX/Alpine.js/Tailwind CDN.
- `app/models/__init__.py` — Import new models here for Alembic discovery.
- `tests/conftest.py` — Async test infrastructure with DI overrides.

### Phase 1 & 2 Context
- `.planning/phases/01-foundation-and-auth/01-CONTEXT.md` — D-05: non-secret config in SQLite, D-06: encryption patterns, D-08: nav shell with placeholder pages.
- `.planning/phases/02-core-loop/02-CONTEXT.md` — D-07: preference parameter hook, D-08: all-at-once results display.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/llm_service.py` — `match_products()` already accepts `preferences: Optional[dict]`. Phase 3 defines the dict structure and passes real data.
- `app/services/llm_service.py` — `parse_shopping_list()` uses Instructor structured output. Same pattern can be used for NL preference parsing.
- `pdfplumber` — Already in requirements.txt. Chosen for tabular receipt parsing (Fry's receipts are structured tabular data).
- `templates/base.html` — Dark sidebar with "Preferences" nav item already wired.

### Established Patterns
- HTMX partial responses for multi-step flows (setup wizard, shopping flow)
- SQLModel for database models with async sessions + Alembic migrations
- Pydantic for request/response validation
- Instructor for LLM structured output

### Integration Points
- `app/services/cart_service.py` — `process_list()` must load user preferences and pass to `match_products()`
- `app/main.py` — Pre-stubbed router includes for new preference router
- `app/routers/pages.py` — Serves the placeholder preferences page, to be replaced or extended
- Phase 4 may add provider switching — preference NL chat should work with any LLM provider

</code_context>

<specifics>
## Specific Ideas

- The `preferences` parameter in `match_products()` is already Optional[dict] — Phase 3 defines what goes in that dict and ensures CartService loads and passes it.
- Receipt PDFs are from Fry's (Kroger subsidiary) — pdfplumber should handle the tabular receipt format well. Test with real Fry's receipts.
- The flag-and-ask pattern for contradictions (D-06) means the receipt upload flow needs a second step after initial parsing where detected brand switches are surfaced for user decision.
- Chat-style NL interface (D-07) may need multiple LLM round-trips. Consider the cost/latency implications — keep it lightweight.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-preference-system*
*Context gathered: 2026-04-04*
