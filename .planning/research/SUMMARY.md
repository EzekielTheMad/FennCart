# Project Research Summary

**Project:** FennCart
**Domain:** Self-hosted grocery cart automation — Kroger API + LLM + OAuth + Docker
**Researched:** 2026-04-02
**Confidence:** MEDIUM-HIGH

## Executive Summary

FennCart is a single-container, self-hosted web application that bridges a user's grocery list to their Fry's/Kroger cart using LLM-powered product matching and a preference profile bootstrapped from historical receipt data. The domain is well-explored at the component level (FastAPI SSR apps, OAuth PKCE flows, LiteLLM integrations, SQLite-on-Docker) but the combination — particularly Kroger's non-standard Cart-is-add-only API and strict TOS around data persistence — introduces constraints that shape every architectural decision. The recommended approach is a Python 3.12 + FastAPI + HTMX/Jinja2 stack with LiteLLM for provider-agnostic LLM calls, pdfplumber for receipt parsing, and Authlib for OAuth PKCE — all inside a single Docker container with SQLite on a named volume.

The recommended build strategy is bottom-up: schema and Docker infrastructure first, then auth and Kroger API integration, then the LLM matching intelligence, and finally the UI. The core value loop ("paste a list, get a loaded cart") is achievable without the preference system and should ship first. Receipt PDF parsing and the living preference profile are high-value differentiators but should be layered in after the core loop is validated — the LLM makes reasonable generic matches without them, so deferring them does not block MVP.

The three most dangerous risk areas are: (1) Kroger TOS compliance — credentials must never ship in the image, customer search data must never persist, and product API results must be session-scoped only; (2) OAuth redirect URI configuration in Docker, which breaks the entire auth flow if the external URL is hardcoded rather than configurable; and (3) LLM cost runaway on large shopping lists if no `max_tokens` cap and batching strategy are in place from the start. All three are preventable with disciplined Phase 1 and Phase 2 implementation.

---

## Key Findings

### Recommended Stack

The stack is intentionally minimal: FastAPI (0.135.3) with Jinja2 + HTMX + Alpine.js for server-side rendering eliminates any Node.js build pipeline from the final Docker image while still supporting the dynamic review flow the app requires. SQLite via SQLModel + aiosqlite handles all persistence with zero operational overhead — exactly right for a single-user self-hosted app. LiteLLM (1.83.0) + Instructor (1.14.5) provide a stable, multi-provider LLM abstraction that returns validated Pydantic objects rather than raw text. Authlib (1.6.9) handles the OAuth 2.0 authorization code + PKCE flow that Kroger requires. pdfplumber (0.11.9) handles machine-generated receipt PDFs with superior table extraction.

The deliberate trade-off is SSR over a React SPA. For a single-user local app with form-based flows, HTMX + Jinja2 avoids Node.js in the image, reduces Docker complexity, and has no meaningful UX downside. The architecture document notes a multi-stage build pattern (frontend compiled at build time, static assets only in final image) — but with SSR there is no separate frontend build stage at all, making the Docker image simpler still.

**Core technologies:**
- **Python 3.12 + FastAPI 0.135.3**: async-native web framework with Pydantic v2 integration; FastAPI 0.128+ dropped Python 3.9 support, 3.12 is the stable target
- **SQLModel 0.0.37 + aiosqlite 0.22.1 + Alembic 1.18.4**: combined SQLAlchemy+Pydantic ORM with async SQLite driver and schema migration support
- **Jinja2 + HTMX 1.9.x + Alpine.js 3.x + Tailwind CSS 3.x**: SSR stack via FastAPI's built-in template system; HTMX/Alpine/Tailwind load from CDN (no Node.js in image)
- **LiteLLM 1.83.0 + Instructor 1.14.5**: unified multi-provider LLM SDK returning validated Pydantic objects; use the Python SDK directly, not the LiteLLM proxy
- **Authlib 1.6.9 + HTTPX 0.28.1**: async OAuth2 PKCE client + async HTTP client for Kroger API calls
- **pdfplumber 0.11.9**: MIT-licensed table-aware PDF text extraction for grocery receipts
- **python:3.12-slim Docker base**: avoids Alpine musl libc issues; significantly smaller than full Python image

**Critical version/config notes:**
- Uvicorn must run with `--workers 1` — SQLite cannot handle concurrent writers
- `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000` required at DB init
- Tailwind standalone CLI (no Node.js) for production CSS generation; CDN acceptable for dev
- Pin `litellm` to specific extras (`litellm[anthropic,openai]`) to control Docker image size

### Expected Features

The MVP critical path is: credentials wizard → store selection → token management → natural language list input → Products API search → LLM matching → review flow → cart add → local cart state tracking. The preference system (receipt parsing, preference profile, NL preference updates) is high-value but not blocking — the LLM makes reasonable matches without it.

**Must have (table stakes):**
- Natural language list input — every competing product accepts free-text; form-per-item is a non-starter
- LLM-powered product matching — semantic ranking of Products API results is the entire value proposition
- Guided BYO credentials wizard — Kroger TOS forbids shared keys; no wizard = zero users get past setup
- Kroger OAuth login with silent token refresh — required for cart operations; 30-min token must refresh silently
- Store selection — Products API results are store-specific; no store = no useful results
- Exceptions-only review flow — Kroger TOS mandates explicit user confirmation before cart add
- Cart add with explicit confirmation — TOS requirement and user trust baseline
- Local cart state tracking — Cart API is add-only; local shadow is the only way to show users what was added
- Fulfillment filtering — prevents "not available for pickup" failures at curbside
- SQLite persistence (auth tokens, store, config) — basic session durability across restarts

**Should have (differentiators):**
- Receipt PDF parsing for preference bootstrapping — solves cold-start; LLMs achieve ~97% accuracy on clean PDFs
- Living preference profile — distinguishes recurring brand preferences from one-off substitutions
- Natural language preference updates — "we switched to oat milk" is faster than any settings UI
- Manual preference editing UI — power-user escape hatch for direct control
- Multi-provider LLM support (Claude, OpenAI, Ollama) — privacy-conscious users strongly prefer local model option
- Shopping history — enables "reorder last week's list" and feeds preference profile over time

**Defer to v2+:**
- Recipe-to-cart and meal planning — second-order complexity, competing products are still proving demand
- Multi-user / household support — significant auth complexity; single user per container is sufficient for v1
- Pantry inventory tracking — Grocy/KitchenOwl do this better as standalone tools
- Coupon clipping automation — Kroger coupon API not part of the public developer offering
- Mobile native app — Docker + responsive web is sufficient for the self-hosting audience

### Architecture Approach

FennCart is a single-container, single-process application. FastAPI serves both SSR HTML and the REST API from one process. SQLite on a named Docker volume handles all persistence. There is no reverse proxy sidecar, no LiteLLM proxy container, and no separate database service. The service layer is the only DB gate — routers call services, services call the DB; no raw SQL in route handlers. The LLM Service is the only component aware of which provider is configured; all other services call `llm_service.complete_structured()` and receive typed Pydantic objects.

**Major components:**
1. **FastAPI Router Layer** — HTTP request handling, auth middleware, input validation; thin layer, no business logic
2. **Cart Service** — orchestrates the list → search → LLM rank → review → add pipeline; the app's core flow
3. **LLM Service** — wraps LiteLLM SDK; provider (Claude/OpenAI/Ollama) is a config value, not a code branch
4. **Kroger API Client** — all HTTP calls to Kroger endpoints (products, cart, locations); uses Authlib OAuth + HTTPX
5. **OAuth Token Manager** — stores/refreshes Kroger tokens; manages PKCE state in Starlette SessionMiddleware
6. **Preference Service** — reads/updates/applies brand and product preferences; feeds LLM ranking prompts
7. **Receipt Parser** — pdfplumber text extraction → LLM entity extraction → Preference Service upsert
8. **SQLite (via SQLModel)** — single source of truth for preferences, receipts, shopping history, OAuth tokens, config

**Hard architectural boundaries:**
- UI never calls Kroger or LLM APIs directly — all external calls go through FastAPI backend
- Router layer never touches SQLite directly — all DB access flows through the Service Layer
- Customer search data (raw list queries) must never be persisted — in-memory only during request lifecycle
- LiteLLM Python SDK only — do not deploy LiteLLM proxy as a sidecar container

### Critical Pitfalls

1. **Kroger credentials embedded in the repo or image** — Enforce BYO-credentials from the first commit. Never set a default value for `KROGER_CLIENT_ID`/`KROGER_CLIENT_SECRET`. App must refuse to start if absent. Use gitleaks pre-commit hook. Provide `.env.example` with placeholder strings only.

2. **OAuth redirect URI hardcoded to container-internal hostname** — Always build redirect URIs from a configurable `BASE_URL` / `EXTERNAL_URL` env var (default: `http://localhost:8080`). Display the exact URI in the setup wizard so users can register it in their Kroger developer app. Test the full OAuth round-trip inside Docker before any release.

3. **Persistent storage of Kroger API response data** — Never write Products API results to a durable SQLite table. Session-scoped in-memory caching is acceptable; persistent product tables violate TOS. Shopping history stores confirmed cart items (user-derived), not search responses (API-derived).

4. **Cart API add-only constraint not accounted for** — Maintain a local session-scoped cart shadow in SQLite. Check for duplicates before every `PUT /cart/add`. Clearly label the shadow "local tracking only — view full cart on frysfood.com." Design this into the Cart Service from Phase 1, not as an afterthought.

5. **SQLite locking under async concurrency** — Enable `journal_mode=WAL` and `busy_timeout=5000` at DB initialization. Use `aiosqlite` exclusively (never bare `sqlite3` in async routes). Short transactional writes only — do not hold write transactions across awaitable calls.

---

## Implications for Roadmap

Based on combined research, a 5-phase structure emerges naturally from the dependency graph. The architecture document's suggested build order is well-reasoned and should be followed closely.

### Phase 1: Foundation and Auth Infrastructure
**Rationale:** Every component depends on the DB schema, Docker volume, and working Kroger OAuth. These are not parallelizable — cart, LLM, and preference features are all blocked until auth tokens can be obtained and persisted. TOS and security constraints (credential handling, WAL mode, secrets redaction in logs) must be correct before any user data touches the system.
**Delivers:** Running Docker container with a stable schema, named volume for data persistence, setup wizard that collects and validates all three credential sets (LLM key, Kroger dev creds, Kroger OAuth), and a working Kroger OAuth PKCE flow with silent token refresh.
**Addresses:** BYO credentials setup, store selection, Kroger OAuth login, token refresh, SQLite persistence
**Avoids:** Credential leak (Pitfall 1), OAuth redirect mismatch (Pitfall 2), SQLite locking (Pitfall 8), Docker volume data loss (Pitfall 9), credentials in logs (Pitfall 14)

### Phase 2: Core Loop — List to Cart
**Rationale:** This is the MVP. With auth working, the entire list→match→review→add pipeline can be implemented. The Kroger API Client, LLM Service, and Cart Service are the app's value proposition. LLM cost, rate limit, and cart-add-only constraints must be designed in from the start.
**Delivers:** Working end-to-end flow: user pastes a grocery list → LLM matches products from Kroger API → exceptions-only review → confirmed items added to Kroger cart → local cart state tracking. No preference system yet — LLM makes best-guess matches.
**Uses:** LiteLLM + Instructor (structured output), HTTPX + Authlib (Kroger API), HTMX (review flow partial updates), pydantic-settings (config)
**Implements:** Cart Service, LLM Service, Kroger API Client, Router Layer endpoints for cart flow
**Avoids:** Persistent API response storage (Pitfall 3), cart add-only duplicate problem (Pitfall 4), LLM cost runaway (Pitfall 5), rate limit exhaustion (Pitfall 6), LLM hallucinating product names (Pitfall 13), misleading stock/price display (Pitfalls 11, 12)

### Phase 3: Preference System
**Rationale:** Once the core loop works, the preference system makes it genuinely good on repeat use. Receipt parsing solves the cold-start problem. The preference profile re-ranks LLM results from generic to personalized. Natural language updates and manual editing round out the preference management surface. These features depend on the LLM Service and Kroger API Client already being stable.
**Delivers:** Receipt PDF upload and parsing pipeline (pdfplumber + LLM extraction with confidence scoring + user review), preference profile CRUD, preference-compensated product matching, natural language preference updates, manual preference editing UI.
**Uses:** pdfplumber, LLM Service (structured extraction), Preference Service, HTMX (receipt review flow)
**Avoids:** Silent parse failures on non-standard receipt formats (Pitfall 7), misattributing one-off substitutions as permanent preferences

### Phase 4: Multi-Provider LLM and Polish
**Rationale:** Multi-provider support (Claude, OpenAI, Ollama) is a differentiator but not blocking for initial release. With the LLMService abstraction already in place from Phase 2 (provider is a config value, not a code branch), adding provider switching is primarily a settings UI + testing concern. Shopping history log, full-review toggle, and UX refinements complete the product.
**Delivers:** Provider selection in settings UI (Claude, OpenAI, Ollama endpoint config), shopping history log with session-level detail, full-review toggle (not just exceptions), UX polish (loading states, error handling, mobile-responsive layout).
**Uses:** LiteLLM's multi-provider abstraction (already in place), HTMX for dynamic settings updates

### Phase 5: Hardening and Distribution
**Rationale:** Self-hosted projects live or die by how easy they are to set up and maintain. Before advertising the project, the setup experience, Docker image size, Alembic migration path, and documentation must be production-quality. This phase converts a working prototype into something a non-developer can confidently deploy.
**Delivers:** Minimal Docker image (LiteLLM extras pinned to only needed providers, Tailwind standalone CLI for purged CSS), Alembic migrations tested across version upgrades, comprehensive setup documentation, `.env.example` with clear instructions, gitleaks pre-commit hook in repo, end-to-end test coverage of OAuth flow in Docker environment.

### Phase Ordering Rationale

- Schema and Docker first because every other component writes to the DB or runs inside the container. Getting these wrong after data exists is expensive.
- Auth before any Kroger API feature because the Kroger API Client requires valid tokens for every call. Testing the cart flow without real tokens requires heavy mocking that introduces false confidence.
- Core loop (Phase 2) before preferences (Phase 3) because the LLM makes usable matches without preferences. This lets the app ship value while the preference system is being built.
- Multi-provider deferred (Phase 4) because the LLMService abstraction is already provider-agnostic from Phase 2 — adding a settings UI for provider switching is incremental, not foundational.
- Polish and distribution last (Phase 5) because hardening a moving target wastes effort; harden when the feature set is stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (LLM Matching):** Prompting strategy for product ranking with Instructor + LiteLLM needs hands-on experimentation. The 48% LLM success rate on shopping tasks (ShoppingComp paper) suggests prompt engineering is non-trivial. Recommend a research spike on prompt templates and `max_tokens` budgets before full implementation.
- **Phase 3 (Receipt Parsing):** Fry's receipt format variation (emailed PDF vs. app-downloaded vs. scanned) needs empirical testing with real samples. Research before implementation — format assumptions made during design that are wrong will require full parser rewrites.
- **Phase 1 (Kroger OAuth PKCE in Docker):** The PKCE redirect flow in a Docker context has one known failure mode (redirect URI mismatch). Authlib PKCE support is documented but the Kroger-specific implementation details come from a JS-rendered developer docs page. Validate the full round-trip in Docker in Phase 1 before building anything that depends on it.

Phases with standard, well-documented patterns:
- **Phase 1 (SQLite + FastAPI setup):** WAL mode, aiosqlite, SQLModel, Alembic — all well-documented; community consensus is consistent.
- **Phase 4 (Multi-provider LiteLLM):** LiteLLM's provider abstraction is the library's core feature; switching providers via config is documented extensively.
- **Phase 5 (Docker image optimization):** Standalone Tailwind CLI, multi-stage builds, slim base image — all established patterns with multiple verified sources.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All PyPI versions verified 2026-04-02 except Instructor (MEDIUM — WebSearch Jan 2026). HTMX/Alpine/Tailwind CDN patterns well-documented. python:3.12-slim Docker recommendation verified Feb 2026. |
| Features | HIGH | Kroger API capabilities and limitations confirmed via developer docs + CupOfOwls reference implementation. Commercial competitor features (Uber Eats Cart Assistant, Albertsons AI) confirmed via press sources. LLM shopping task success rate from arXiv paper. |
| Architecture | MEDIUM-HIGH | Single-container SSR pattern is well-documented for FastAPI. OAuth PKCE in Docker has one confirmed failure mode. Kroger-specific API constraints (add-only cart, no-view endpoint) from developer docs but JS-rendered page limits full verification. |
| Pitfalls | MEDIUM | SQLite, Docker, OAuth pitfalls are well-sourced. Kroger TOS specifics are from developer.kroger.com docs — authoritative but the developer portal is JS-rendered and full content could not be directly verified. LLM cost/token behavior from community sources. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Kroger TOS full text**: The developer.kroger.com portal is JS-rendered; key TOS clauses (search data persistence, price comparison prohibition) are cited from community sources rather than directly verified. During Phase 1, confirm current TOS before finalizing schema design for any table that touches Kroger data.
- **Kroger Products API result shape**: The exact JSON response schema for Products API (field names, fulfillment enum values, pagination behavior) should be validated with a real API call early in Phase 2. Do not design the LLM prompt or matching logic against assumed field names.
- **Instructor version**: Pinned to 1.14.5 from WebSearch (Jan 2026) — verify current version on PyPI before writing `requirements.txt` in Phase 1.
- **LLM prompt strategy for product matching**: The 48% state-of-the-art success rate on shopping tasks suggests the prompting strategy matters enormously. Plan a dedicated spike in Phase 2 before building the full Cart Service around a fixed prompt template.
- **Fry's receipt PDF format variation**: Parser design should be deferred until at least three real receipt formats (emailed PDF, app-downloaded, older format) have been tested with pdfplumber. Do not assume format uniformity.

---

## Sources

### Primary (HIGH confidence)
- [fastapi · PyPI](https://pypi.org/project/fastapi/) — version verification
- [sqlmodel · PyPI](https://pypi.org/project/sqlmodel/) — version verification
- [aiosqlite · PyPI](https://pypi.org/project/aiosqlite/) — version verification
- [alembic · PyPI](https://pypi.org/project/alembic/) — version verification
- [litellm · PyPI](https://pypi.org/project/litellm/) — version verification
- [httpx · PyPI](https://pypi.org/project/httpx/) — version verification
- [authlib · PyPI](https://pypi.org/project/authlib/) — version verification
- [pdfplumber · PyPI](https://pypi.org/project/pdfplumber/) — version verification
- [Kroger Cart API — developer.kroger.com](https://developer.kroger.com/reference/api/cart-api-public) — cart add-only constraint
- [Kroger Products API overview — developer.kroger.com](https://developer.kroger.com/documentation/api-products/public/products/overview) — rate limits, fulfillment field
- [CupOfOwls kroger-api (GitHub)](https://github.com/CupOfOwls/kroger-api) — PKCE flow, token refresh pattern
- [SQLite WAL mode official docs](https://sqlite.org/wal.html) — concurrency configuration
- [SQLite in Docker — OneUptime (Feb 2026)](https://oneuptime.com/blog/post/2026-02-08-how-to-run-sqlite-in-docker-when-and-how/view)
- [Docker Python base image — PythonSpeed (Feb 2026)](https://pythonspeed.com/articles/base-image-python-docker-images/)

### Secondary (MEDIUM confidence)
- [ShoppingComp: Are LLMs Ready for Your Shopping Cart? — arXiv (2024)](https://arxiv.org/html/2511.22978v1) — 48% LLM success rate on shopping tasks
- [Receipt OCR Benchmark with LLMs — AIMultiple Research](https://research.aimultiple.com/receipt-ocr/) — ~97% LLM accuracy on clean PDFs
- [Uber Eats Cart Assistant — TechCrunch (Feb 2026)](https://techcrunch.com/2026/02/11/uber-eats-launches-ai-assistant-to-help-with-grocery-cart-creation/) — competitive feature landscape
- [Albertsons AI Shopping Assistant (2025)](https://www.albertsonscompanies.com/newsroom/press-releases/news-details/2025/Albertsons-Companies-Accelerates-Digital-Transformation-with-the-Albertsons-AI-Shopping-Assistant-Redefining-the-Grocery-Shopping-Experience/default.aspx) — competitive feature landscape
- [HTMX vs React, Vue, Angular (2025)](https://redskydigital.com/au/htmx-vs-react-vue-angular-frontend-development-in-2025/) — SSR vs SPA rationale
- [LiteLLM GitHub](https://github.com/BerriAI/litellm) — multi-provider abstraction pattern
- [Authlib OAuth2 client docs](https://docs.authlib.org/en/latest/client/oauth2.html) — PKCE async flow
- [SQLite concurrent writes — Ten Thousand Meters](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/) — locking behavior

### Tertiary (LOW confidence)
- [Kroger Developer Portal TOS](https://developer.kroger.com/support/faq) — JS-rendered, full content not directly verified; key TOS clauses cited via community sources
- [instructor · PyPI](https://pypi.org/project/instructor/) — version 1.14.5 from WebSearch Jan 2026, not directly re-verified

---
*Research completed: 2026-04-02*
*Ready for roadmap: yes*
