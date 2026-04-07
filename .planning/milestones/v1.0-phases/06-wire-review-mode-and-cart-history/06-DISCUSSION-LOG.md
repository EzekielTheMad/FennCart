# Phase 6: Wire Review Mode and Cart History - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-06
**Phase:** 06-wire-review-mode-and-cart-history
**Areas discussed:** Cart history layout, History page actions, Review mode persistence

---

## Cart History Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Expandable session rows | Each session is a compact row showing date, item count, estimated total. Click to expand. | ✓ |
| Flat item table | One big table of all cart items across sessions, grouped by session date. | |
| Session cards | Each session rendered as a card with summary + item list always visible. | |

**User's choice:** Expandable session rows
**Notes:** Keeps page scannable, expand for detail.

### Row Data

| Option | Description | Selected |
|--------|-------------|----------|
| Date + item count + total | Clean and scannable summary | ✓ |
| Date + item count + total + top 3 items | More context at a glance but busier | |
| You decide | Claude picks | |

**User's choice:** Date + item count + total

### Item Detail Columns

| Option | Description | Selected |
|--------|-------------|----------|
| Product name + brand + qty + price | Core shopping info | ✓ |
| All available data | Name, brand, size, UPC, qty, regular price, promo price | |
| You decide | Claude picks | |

**User's choice:** Product name + brand + qty + price

### Sort Order

| Option | Description | Selected |
|--------|-------------|----------|
| Newest first | Most recent session at top | ✓ |
| Oldest first | Chronological order | |

**User's choice:** Newest first

---

## History Page Actions

| Option | Description | Selected |
|--------|-------------|----------|
| View-only | Pure display of past sessions. No clear/delete/reorder. | ✓ |
| View + clear history | Add a 'Clear all history' button | |
| View + re-order from session | Add a 'Reorder' button per session | |

**User's choice:** Initially selected "View + re-order from session" but agreed to defer after scope discussion.

### Scope Decision

| Option | Description | Selected |
|--------|-------------|----------|
| Defer to v2 | Keep Phase 6 focused on wiring existing data. Note HIST-02 as deferred. | ✓ |
| Pull into Phase 6 | Add reorder capability now | |

**User's choice:** Defer to v2

### Empty State

| Option | Description | Selected |
|--------|-------------|----------|
| You decide | Claude picks clean empty state with helpful message | ✓ |
| Specific idea | User has something in mind | |

**User's choice:** Claude's discretion

---

## Review Mode Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| Just the fix | Read from DB, pass to template, Alpine initializes with saved value | ✓ |
| Toggle override persists | Toggling during shopping run also saves back to AppConfig | |
| You decide | Claude picks simplest approach | |

**User's choice:** Just the fix — read from DB, pass to template

---

## Claude's Discretion

- Empty state design for history page
- Expand/collapse animation and styling
- HTMX vs Alpine.js for expand/collapse
- Price display format
- Pagination approach (deferred)

## Deferred Ideas

- HIST-02: Re-order from session (v2 requirement)
- Bidirectional toggle save (toggle during shopping saves to AppConfig)
- History pagination
