# Phase 6: Wire Review Mode and Cart History - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Close two partial requirement gaps identified in the v1.0 milestone audit:
1. **SRCH-05**: Review mode toggle state must persist across page loads by reading `AppConfig.review_mode` from the database instead of hardcoding `'exceptions'` in the template.
2. **CART-03**: The `/history` page must query `CartSession`/`CartItem` models and render actual cart history data instead of a static placeholder.

Also closes:
- Integration gap: `review_screen.html` hardcodes `mode: 'exceptions'` instead of reading `AppConfig.review_mode`
- Flow gap: "Session cart history view" broken at history page

</domain>

<decisions>
## Implementation Decisions

### Cart History Layout
- **D-01:** Expandable session rows — each cart session is a compact row showing date, item count, and estimated total. Click/tap to expand and see individual items. Keeps the page scannable.
- **D-02:** Collapsed row shows: date + item count + estimated total (e.g., "Apr 6, 2026 — 12 items — $47.82").
- **D-03:** Expanded item detail shows: product name, brand, quantity, price. Core shopping info matching what the review screen showed before confirming.
- **D-04:** Sessions sorted newest-first. Most recent session at top.

### History Page Actions
- **D-05:** View-only for v1. No clear, delete, or reorder actions. Pure display of past sessions.

### Review Mode Persistence
- **D-06:** Read `AppConfig.review_mode` in the shopping router and pass it to the review screen template. Alpine x-data initializes with the saved value instead of hardcoding `'exceptions'`.
- **D-07:** Toggle works within session as it does now (client-side only). Toggling during a shopping run does NOT save back to AppConfig — it's a temporary override. Settings page is the canonical place to change the default.

### Claude's Discretion
- Empty state design for history page when no sessions exist (helpful message + link to shopping page)
- Expand/collapse animation and styling for session rows
- Whether to use Alpine.js or pure HTMX for expand/collapse behavior
- Price display format (show promo price vs regular, or both)
- Pagination approach if session count grows large (or defer pagination)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Review Mode (SRCH-05 fix)
- `app/routers/shopping.py` — Shopping router; must read `AppConfig.review_mode` and pass to template context
- `templates/partials/review_screen.html` — Review screen; Alpine x-data hardcodes `mode: 'exceptions'` on line ~7; must use server-passed value
- `app/models/config_model.py` — `AppConfig` model with `review_mode` field (default `"exceptions"`)
- `app/routers/settings.py` — Settings router; `POST /settings/save-preferences` already saves `review_mode` correctly

### Cart History (CART-03 fix)
- `app/routers/pages.py` — Page router; `/history` endpoint returns stub template with no data
- `templates/pages/history.html` — History template; static placeholder content
- `app/models/cart_session.py` — `CartSession` model: `id`, `created_at`, `item_count`, `estimated_total`
- `app/models/cart_item.py` — `CartItem` model: `id`, `session_id` (FK), `upc`, `description`, `brand`, `size`, `quantity`, `price_regular`, `price_promo`, `added_at`

### Patterns to Follow
- `templates/base.html` — Base layout with dark sidebar nav, HTMX/Alpine.js/Tailwind CDN
- `templates/partials/` — Established pattern for HTMX partial responses
- `.planning/phases/02-core-loop/02-CONTEXT.md` — Phase 2 decisions on review UX (D-03 hybrid layout, D-05 dropdown swap)
- `.planning/phases/04-multi-provider-llm-and-settings/04-CONTEXT.md` — Phase 4 decisions on settings (D-11 review mode toggle)

### Audit Source
- `.planning/v1.0-MILESTONE-AUDIT.md` — Gap definitions and evidence

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AppConfig.review_mode` field — already exists, saved by settings, just needs to be read by shopping router
- `CartSession` and `CartItem` models — already exist, data accumulates on cart add
- `templates/partials/` directory — established HTMX partial pattern for dynamic content
- Alpine.js expand/collapse — used elsewhere in the app for accordion-style UI

### Established Patterns
- HTMX for server-driven partial updates (`hx-get`, `hx-target`, `hx-swap`)
- Alpine.js for client-side toggle state (review mode toggle, dropdown menus)
- SQLModel async queries via `AsyncSession` dependency injection
- Tailwind dark theme: `slate-950/900/800` palette with `green-500` accents
- `Jinja2Templates` instantiated per-router (router-local pattern, avoids circular imports)

### Integration Points
- `/history` route in `pages.py` — needs `AsyncSession` dependency added, query logic, template context
- `review_screen.html` — needs to accept `review_mode` from template context instead of hardcoding
- `shopping.py` — needs to query `AppConfig` for `review_mode` before rendering review screen
- `CartSession` → `CartItem` relationship may need explicit SQLModel `Relationship` field for eager loading

</code_context>

<specifics>
## Specific Ideas

- History row format: "Apr 6, 2026 — 12 items — $47.82" as the collapsed summary
- Expanded detail columns: product name, brand, quantity, price (matching review screen data)
- Review mode fix is minimal: one DB read in shopping router + one template variable change

</specifics>

<deferred>
## Deferred Ideas

- **HIST-02: Re-order from session** — User wanted a "Reorder" button per session that pre-fills the shopping list. Deferred to v2 as it's a new capability (HIST-02 in REQUIREMENTS.md).
- **Bidirectional toggle save** — Toggle override during shopping run could save back to AppConfig. Decided against for now; settings page is the canonical place to change defaults.
- **History pagination** — If session count grows large, pagination may be needed. Deferred unless data volume warrants it.

</deferred>

---

*Phase: 06-wire-review-mode-and-cart-history*
*Context gathered: 2026-04-06*
