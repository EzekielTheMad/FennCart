# Fenn Cart

## What This Is

A self-hosted, Docker-containerized web application that converts grocery shopping lists into loaded Kroger/Fry's carts. Users paste a natural language shopping list, the app matches items against learned brand preferences using an LLM, presents selections for review, and adds confirmed items to the user's Kroger cart via the Kroger Public API. Named after Fenn, a DnD character who doubled as the party's chef.

## Core Value

Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

## Requirements

### Validated

- [x] Guided first-run setup wizard (LLM API key, Kroger developer credentials, Kroger OAuth login, store selection) — Validated in Phase 1: Foundation and Auth
- [x] Natural language shopping list input (paste, type, or dictate) — Validated in Phase 2: Core Loop
- [x] LLM-powered product matching against Kroger Products API — Validated in Phase 2: Core Loop
- [x] Smart review flow: exceptions-only by default, full review table toggle — Validated in Phase 2: Core Loop
- [x] Cart building via Kroger Cart API with explicit user confirmation — Validated in Phase 2: Core Loop
- [x] Kroger OAuth flow handled within the web UI — Validated in Phase 1: Foundation and Auth
- [x] Curbside pickup fulfillment filtering — Validated in Phase 2: Core Loop
- [x] SQLite persistence via Docker volume — Validated in Phase 1: Foundation and Auth

### Active

- [ ] LLM-powered product matching ranked by user preferences (preference system in Phase 3)
- [ ] Receipt PDF upload and parsing to build/update preference profile over time
- [ ] Living preference profile that learns from receipt history and weights recurring purchases vs one-off substitutions
- [ ] Natural language preference updates ("we switched to oat milk", "stop buying Kroger brand yogurt")
- [ ] Manual preference editing UI for direct control
- [x] Multi-provider LLM support (Claude, OpenAI, local models) with provider selector and settings hub — Validated in Phase 4: Multi-Provider LLM and Settings

### Out of Scope

- Coupon clipping automation — manual during checkout on frysfood.com
- Automated checkout or payment — legal/TOS risk, users complete checkout on Kroger's site
- Multi-store price comparison — explicitly prohibited by Kroger TOS
- Mobile native app — web UI is sufficient, mobile browser works
- Multi-user/household support in v1 — single user per container instance
- Building a product database from API responses — prohibited by Kroger TOS
- Real-time stock availability — Kroger API doesn't provide this, same limitation as their website

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

**Existing open source:**
- kroger-mcp (CupOfOwls) — MCP server wrapping Kroger API, MIT licensed
- kroger-api (CupOfOwls) — Python client for Kroger API, MIT licensed
- These are reference implementations, not dependencies (we're building a standalone app)

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
| Docker container distribution | Makes it easy for anyone to self-host without environment setup | Validated in Phase 05 — .dockerignore, README quickstart, SESSION_SECRET_KEY validator |
| Web UI (not CLI or Claude Desktop) | Broader accessibility, visual review flow, guided setup | — Pending |
| LLM-agnostic with multi-provider support | Don't lock users into one AI provider; Claude, OpenAI, local models all viable | — Pending |
| SQLite for persistence | Single-container simplicity, no separate DB service needed, Docker volume for durability | — Pending |
| Receipt PDF parsing for preference learning | Solves cold-start problem — users don't have to manually build preference profiles | — Pending |
| BYO-credentials model | Required by Kroger TOS — cannot distribute shared API keys | — Pending |
| Exceptions-only default review flow | Fast path for high-confidence matches, full review available when wanted | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-06 after Phase 06 completion — review mode persistence and cart history wired*
