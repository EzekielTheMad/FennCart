# Phase 2: Core Loop - Context

**Gathered:** 2026-04-03
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the end-to-end list-to-cart flow: user pastes a natural language grocery list, the app uses an LLM (via LiteLLM + Instructor) to interpret items and match them against Kroger Products API results, presents matched products for review with confidence-based filtering, and adds confirmed items to the user's Kroger cart via the Cart API. A local session record of what was added is maintained in SQLite since the Cart API is add-only (no view endpoint).

</domain>

<decisions>
## Implementation Decisions

### Shopping List Input
- **D-01:** Smart textarea with live preview — user types or pastes free-form text in a textarea. As they type, a live preview below the textarea parses lines into structured items (name, quantity, notes) using HTMX partial updates.
- **D-02:** No list persistence — the textarea starts fresh every visit. No session storage, no database persistence of the raw list text.

### Match Review UX
- **D-03:** Hybrid cards/table layout — items needing review (low confidence) display as product cards with image, name, size, price. Auto-matched high-confidence items display as compact table rows. This gives visual attention to items that need it while keeping the rest scannable.
- **D-04:** Confidence hidden unless low — don't show confidence scores on high-confidence matches. Only flag uncertain ones with a warning indicator. Keeps the UI clean.
- **D-05:** Dropdown swap for alternatives — when an item has multiple possible matches, clicking the matched product shows a dropdown of 3-5 alternatives. User picks one to swap it in. HTMX partial swap on selection.

### Cart Confirmation
- **D-06:** Success screen shows summary by default (item count, estimated total) with a direct link to Fry's curbside pickup. Expandable to full item list with product name, quantity, and price for users who want detail.

### LLM Matching Behavior
- **D-07:** Ambiguous items use preference profile if available (Phase 3 delivers this), otherwise LLM best-guesses the most common option and flags as low confidence for review. The matching interface is designed to accept preference context from the start, even though Phase 2 won't have preferences yet.
- **D-08:** Results displayed all at once after the full list is processed. User waits for complete results rather than seeing streaming per-item updates.

### Claude's Discretion
- Quantity/unit parsing approach — LLM-only vs regex pre-parse. Claude picks what works best with Instructor structured output.
- Empty/short list handling — Claude picks the UX pattern (inline error vs helpful empty state).
- Cart confirmation flow details — one-click vs checkbox select, progress indicator style.
- Error handling for failed cart additions — retry vs report pattern.
- Exceptions-only vs full review toggle UX — switch vs tabs vs other.
- Number of Kroger product results per search (5 vs 10 vs dynamic).
- LLM call strategy — single batch vs per-item. Claude picks based on cost, resilience, and the all-at-once display decision.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Kroger API
- `FennCartPitch.md` — Full Kroger API details, auth flow, rate limits, TOS constraints, acceptable use policy. Critical for Products API search parameters and Cart API add endpoint.
- `.planning/research/PITFALLS.md` — 14 specific pitfalls with prevention strategies, especially product search pagination and cart add-only limitation.

### Architecture & Stack
- `.planning/research/STACK.md` — Verified stack with versions (LiteLLM 1.83.0, Instructor 1.14.5, HTTPX 0.28.1)
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow patterns
- `CLAUDE.md` — Technology stack constraints, all version pins

### Phase 1 Patterns (established code to follow)
- `app/services/kroger_client.py` — Existing Kroger API client (credentials grant, store search). Extend for product search.
- `app/services/llm_service.py` — Existing LLM service (connection test). Extend for product matching.
- `app/services/oauth_manager.py` — Token management for authenticated Kroger API calls.
- `app/main.py` — App factory pattern with pre-stubbed router includes.
- `templates/base.html` — Base template with HTMX/Alpine.js/Tailwind CDN. All new templates extend this.
- `tests/conftest.py` — Test infrastructure with async fixtures and middleware patching.

### Phase 1 Context
- `.planning/phases/01-foundation-and-auth/01-CONTEXT.md` — Prior decisions (D-01 through D-10), especially D-08 (nav shell with placeholder pages already built).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/services/kroger_client.py` — Has `_get_client_token()` for credentials grant. Extend with `search_products(term, location_id, limit)` and `add_to_cart(items, access_token)`.
- `app/services/llm_service.py` — Has `test_connection()`. Extend with `match_products(list_items, kroger_results, preferences=None)` returning Pydantic models via Instructor.
- `app/services/oauth_manager.py` — Has `get_valid_access_token()` for user-authenticated Kroger calls (Cart API requires user auth, Products API uses client credentials).
- `templates/base.html` — Dark sidebar nav with HTMX 1.9.x, Alpine.js 3.x, Tailwind CDN. All new pages extend this.
- `tests/conftest.py` — Async test client with DI overrides and middleware session patching.

### Established Patterns
- HTMX partial responses for multi-step flows (established in setup wizard)
- SQLModel for database models with async sessions
- Pydantic Settings for configuration from env vars
- Alembic for schema migrations (new models need migration files)

### Integration Points
- `templates/pages/shopping.html` — Placeholder page to be replaced with the actual shopping list + review UI
- `app/main.py` has pre-stubbed router includes — new routers auto-register
- `app/models/__init__.py` — Import new models here for Alembic discovery
- Phase 3 will add preference context to the matching pipeline — design the matching function signature to accept optional preferences

</code_context>

<specifics>
## Specific Ideas

- User wants ambiguity resolution to be preference-driven (Phase 3), so the matching interface must accept optional preference context even though Phase 2 won't use it yet. Design for the future.
- The Kroger Cart API is add-only — cannot view or remove items. Local SQLite cart state is the only record of what was added. This is a hard constraint from the TOS.
- Product search results are non-personalized (Kroger API constraint). The LLM compensates by re-ranking based on common sense and (eventually) preferences.
- Curbside pickup filtering is done via the `fulfillment.type` field in Kroger Products API — filter for `ais` (Available In Store) for pickup eligibility.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-loop*
*Context gathered: 2026-04-03*
