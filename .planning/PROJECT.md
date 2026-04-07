# Fenn Cart

## What This Is

A self-hosted, Docker-containerized web application that converts grocery shopping lists into loaded Kroger/Fry's carts. Users paste a natural language shopping list, the app matches items against learned brand preferences using an LLM, presents selections for review, and adds confirmed items to the user's Kroger cart via the Kroger Public API. Named after Fenn, a DnD character who doubled as the party's chef.

## Core Value

Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

## Current State

**Version:** v1.0 MVP (shipped 2026-04-07)
**Codebase:** ~6,400 Python + ~5,000 HTML (187 tests passing)
**Stack:** Python 3.12, FastAPI, HTMX/Jinja2/Alpine.js/Tailwind, SQLite, LiteLLM + Instructor

**What's working:**
- Guided first-run wizard (LLM key, Kroger credentials, store selection, OAuth)
- NL shopping list -> LLM product matching -> review -> Kroger Cart API
- Receipt PDF parsing to build a living preference profile
- Multi-provider LLM (Claude, OpenAI, Ollama) with DB-authoritative hot-swap
- NL preference chat and manual preference CRUD
- Cart history tracking across sessions
- Docker-ready with Alembic migration safety

## Requirements

### Validated

- ✓ SETUP-01: Guided first-run setup wizard — v1.0
- ✓ SETUP-02: Store location via zip code search — v1.0
- ✓ SETUP-03: Kroger OAuth PKCE flow within web UI — v1.0
- ✓ SETUP-04: Silent token refresh (6-month validity) — v1.0
- ✓ SRCH-01: Natural language shopping list input — v1.0
- ✓ SRCH-02: LLM product matching against Kroger Products API — v1.0
- ✓ SRCH-03: Curbside pickup fulfillment filtering — v1.0
- ✓ SRCH-04: Exceptions-only default with auto-match for high confidence — v1.0
- ✓ SRCH-05: Review mode toggle (persisted across page loads) — v1.0
- ✓ CART-01: Explicit confirmation before cart add — v1.0
- ✓ CART-02: Local cart state in SQLite — v1.0
- ✓ CART-03: Cart history view across sessions — v1.0
- ✓ PREF-01: Receipt PDF upload to bootstrap preferences — v1.0
- ✓ PREF-02: Receipt parsing (items, brands, sizes, prices) — v1.0
- ✓ PREF-03: Living preference profile weighted by frequency — v1.0
- ✓ PREF-04: NL preference updates — v1.0
- ✓ PREF-05: Manual preference CRUD — v1.0
- ✓ PREF-06: Preference-ranked product matching — v1.0
- ✓ LLM-01: Multi-provider support (Claude, OpenAI, Ollama) — v1.0
- ✓ LLM-02: Provider selector and settings hub — v1.0

### Active

(No active requirements — next milestone not yet defined)

### Out of Scope

- Coupon clipping automation — not available via Kroger public API
- Automated checkout or payment — prohibited by Kroger TOS
- Multi-store price comparison — prohibited by Kroger TOS
- Real-time stock availability — Kroger API doesn't expose stock data
- Product database persistence — prohibited by Kroger TOS
- Background/scheduled cart building — Kroger TOS requires explicit user action
- Multi-user/household support — single user per container in v1
- Mobile native app — responsive web UI sufficient
- Pantry inventory tracking — Grocy/KitchenOwl serve this well
- Recipe-to-cart / meal planning — defer until core loop validated

## Context

**Kroger API ecosystem:**
- Kroger is the only major US grocery chain with a public developer API including cart management
- Products API: 10,000 calls/day, returns price/promo/aisle/fulfillment per location
- Cart API: 5,000 calls/day, add-only (no remove, no view cart contents)
- Locations API: 1,600 calls/day
- OAuth tokens: 30-min access, 6-month refresh
- API results are non-personalized (may differ from website which uses personalized data)
- Fulfillment field indicates approval for method, NOT current stock availability

**Three credential sets required per user:**
1. LLM API key (Anthropic, OpenAI, or local model endpoint)
2. Kroger Developer API credentials (client ID + secret from developer.kroger.com)
3. Kroger account login (Fry's/Kroger shopping account, via OAuth)

**TOS constraints (shape the architecture):**
- Developer credentials must NOT be embedded in open source projects
- Cannot create an API client that substantially replicates the APIs for third parties
- Cannot track/share/store data from customer searches (temporary caching OK, delete on session end)
- Cannot add items without user's explicit knowledge/request
- Cannot compare prices across retailers
- Must not circumvent rate limits

## Constraints

- **TOS**: Each user must bring their own Kroger developer credentials — cannot distribute with shared keys
- **API**: Cart API is add-only; cannot view or remove items via API. Must track cart state locally.
- **API**: Product results are non-personalized; preference system compensates for this gap
- **Auth**: Kroger OAuth requires browser redirect flow — must work within Docker/web UI context
- **Data**: Customer search data must not be persistently stored beyond session (TOS). Preference profiles derived from receipts (user-provided data) are fine.
- **Distribution**: Open source, BYO-credentials model. Users self-host via Docker.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Docker container distribution | Makes it easy for anyone to self-host without environment setup | ✓ Good — .dockerignore, README quickstart, SESSION_SECRET_KEY validator |
| Web UI (not CLI or Claude Desktop) | Broader accessibility, visual review flow, guided setup | ✓ Good — HTMX+Jinja2 delivers interactive UX without JS build step |
| LLM-agnostic with multi-provider support | Don't lock users into one AI provider | ✓ Good — DB-authoritative hot-swap, all endpoints respect settings |
| SQLite for persistence | Single-container simplicity, no separate DB service | ✓ Good — WAL mode + single worker is reliable |
| Receipt PDF parsing for preference learning | Solves cold-start problem for preferences | ✓ Good — pdfplumber handles Fry's receipt format well |
| BYO-credentials model | Required by Kroger TOS | ✓ Good — no legal risk |
| Exceptions-only default review flow | Fast path for high-confidence matches | ✓ Good — review mode toggle persists user preference |
| Fernet encryption for API keys in DB | Protect sensitive keys at rest | ✓ Good — /data/app.key auto-generated, keys never in plaintext |
| Router-local Jinja2Templates | Avoids circular imports from app.main | ⚠️ Revisit — adds boilerplate per router |
| Server-side session for match state | Starlette session persists multi-step HTMX flow | ✓ Good — simpler than client-side state management |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-07 after v1.0 milestone*
