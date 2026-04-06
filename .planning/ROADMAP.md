# Roadmap: Fenn Cart

**Project:** Fenn Cart
**Core Value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.
**Granularity:** Standard (5-8 phases)
**Created:** 2026-04-02

---

## Phases

- [x] **Phase 1: Foundation and Auth** - Running Docker container with stable schema, credentials wizard, and working Kroger OAuth PKCE with silent token refresh (completed 2026-04-03)
- [x] **Phase 2: Core Loop** - End-to-end list-to-cart flow: paste list, LLM matches products, review, confirm, items added to Kroger cart (completed 2026-04-03)
- [x] **Phase 3: Preference System** - Receipt PDF upload and parsing, living preference profile, preference-compensated product matching, NL and manual preference editing (completed 2026-04-06)
- [x] **Phase 4: Multi-Provider LLM and Settings** - Provider selector UI (Claude, OpenAI, Ollama), settings surface for ongoing configuration (completed 2026-04-06)
- [ ] **Phase 5: Hardening and Distribution** - Minimal Docker image, Alembic migration verification, end-to-end test coverage, setup documentation, security pre-commit hooks
- [ ] **Phase 6: Wire Review Mode and Cart History** - Fix SRCH-05 review mode persistence and CART-03 history page stub; close integration and flow gaps from milestone audit
- [ ] **Phase 7: LLM Config Integration Fix** - Wire preferences.py receipt upload and NL chat to use get_active_llm_config instead of env vars

---

## Phase Details

### Phase 1: Foundation and Auth
**Goal**: Users can complete setup and authenticate with Kroger inside a running Docker container
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04
**Success Criteria** (what must be TRUE):
  1. User can run `docker compose up` and reach the setup wizard in a browser with no additional configuration beyond providing an `.env` file
  2. User can enter their LLM API key, Kroger developer credentials, and store location in the guided wizard and have them persisted across container restarts
  3. User can complete the Kroger OAuth PKCE flow — click Authorize, get redirected to Kroger, grant access, and land back in the app with a valid session
  4. App silently refreshes an expired Kroger access token without requiring user re-authentication (within the 6-month refresh window)
  5. App refuses to start and shows a clear error if Kroger developer credentials are absent from the environment
**Plans:** 4/4 plans complete
Plans:
- [x] 01-01-PLAN.md — Project skeleton: Docker, config, database, models, Alembic
- [x] 01-02-PLAN.md — App shell: nav sidebar, missing config page, placeholder pages, test scaffold
- [x] 01-03-PLAN.md — Setup wizard steps 1-3: LLM validation, Kroger credentials, store search
- [x] 01-04-PLAN.md — OAuth PKCE flow, token encryption, silent refresh, quick tour
**UI hint**: yes

### Phase 2: Core Loop
**Goal**: Users can go from a natural language grocery list to confirmed items in their Kroger cart
**Depends on**: Phase 1
**Requirements**: SRCH-01, SRCH-02, SRCH-03, SRCH-04, SRCH-05, CART-01, CART-02, CART-03, LLM-01
**Success Criteria** (what must be TRUE):
  1. User can paste or type a free-form grocery list and submit it for processing
  2. App returns matched Kroger products — only items available for curbside pickup — with the LLM's best match selected per list item
  3. By default, only uncertain or low-confidence matches appear for manual review; high-confidence matches are auto-selected
  4. User can toggle to full review mode and see all matched items before confirming
  5. User can confirm selections and have those items added to their Kroger cart, with a local session record of what was added
**Plans:** 4/4 plans complete
Plans:
- [x] 02-01-PLAN.md — Data layer: Pydantic schemas, SQLModel cart tables, Alembic migration, Kroger API extensions
- [x] 02-02-PLAN.md — LLM matching: parse_shopping_list and match_products via Instructor + LiteLLM
- [x] 02-03-PLAN.md — Cart service orchestration, shopping router, and all UI templates
- [x] 02-04-PLAN.md — Integration and unit tests for all Phase 2 requirements

**UI hint**: yes

### Phase 3: Preference System
**Goal**: Users can bootstrap and maintain a preference profile that makes product matching accurate to their actual buying habits
**Depends on**: Phase 2
**Requirements**: PREF-01, PREF-02, PREF-03, PREF-04, PREF-05, PREF-06
**Success Criteria** (what must be TRUE):
  1. User can upload a Fry's receipt PDF and have it parsed into purchase history entries they can review before saving
  2. App builds a preference profile that weights recurring purchases more heavily than one-off substitutions
  3. Product matching results visibly reflect the preference profile — a user's habitual brand appears ranked above a generic alternative
  4. User can type a natural language preference update ("we switched to oat milk") and have it applied to the profile
  5. User can view, add, edit, and delete individual preference entries directly in a settings UI
**Plans:** 4/4 plans complete
Plans:
- [x] 03-01-PLAN.md — Data layer: models, schemas, Alembic migration, preference service, receipt parser
- [x] 03-02-PLAN.md — Preferences router, page template, receipt upload UI, CRUD endpoints, all HTMX partials
- [x] 03-03-PLAN.md — NL chat endpoints and UI, CartService preference integration, shopping indicator
- [x] 03-04-PLAN.md — Unit and integration tests for all Phase 3 requirements
**UI hint**: yes

### Phase 4: Multi-Provider LLM and Settings
**Goal**: Users can choose their preferred LLM provider and manage app settings beyond initial setup
**Depends on**: Phase 2
**Requirements**: LLM-02
**Success Criteria** (what must be TRUE):
  1. User can navigate to a settings page and switch the active LLM provider between Claude, OpenAI, and a local Ollama endpoint without restarting the container
  2. User can enter or update the API key and model name for the selected provider and have the change take effect on the next shopping run
  3. Shopping runs succeed end-to-end after switching providers (same matching quality baseline)
**Plans:** 3/3 plans complete
Plans:
- [x] 04-01-PLAN.md — Backend foundation: AppConfig extension, Alembic migration, DB-authoritative LLM config reader, Ollama support
- [x] 04-02-PLAN.md — Settings hub: router, shell template, 4 section partials (LLM, Store, Account, Preferences)
- [x] 04-03-PLAN.md — Tests: unit tests for LLM config service, integration tests for all settings endpoints
**UI hint**: yes

### Phase 5: Hardening and Distribution
**Goal**: The app is ready for a non-developer to self-host confidently and for the project to be shared publicly
**Depends on**: Phase 3, Phase 4
**Requirements**: (none — non-functional hardening phase)
**Success Criteria** (what must be TRUE):
  1. A person following only the README can get the app running on a fresh machine without prior context
  2. Docker image size is minimized (LiteLLM provider extras pinned, Tailwind CSS purged) and the image builds cleanly from a cold pull
  3. Running the full Kroger OAuth flow inside Docker produces no redirect URI errors on a stock setup
  4. Upgrading from an earlier schema version runs Alembic migrations without data loss
**Plans:** 2/2 plans executed
Plans:
- [x] 05-01-PLAN.md — Docker optimization (.dockerignore, LLM SDK deps) and security hardening (SESSION_SECRET_KEY validator, .gitignore)
- [x] 05-02-PLAN.md — Alembic migration upgrade test (pytest-alembic) and quickstart README

### Phase 6: Wire Review Mode and Cart History
**Goal**: Close partial requirement gaps SRCH-05 and CART-03 — review mode persists across page loads and cart history page shows real data
**Depends on**: Phase 2, Phase 4
**Requirements**: SRCH-05, CART-03
**Gap Closure**: Closes gaps from v1.0 milestone audit
**Success Criteria** (what must be TRUE):
  1. Review mode toggle state persists across page loads by reading AppConfig.review_mode from the database
  2. Shopping router passes the saved review_mode to the review screen template instead of hardcoding 'exceptions'
  3. /history page queries CartSession/CartItem models and renders actual cart history data
  4. User can see what was added to cart across sessions (not just current session)
**Plans:** 1 plan
Plans:
- [ ] 06-01-PLAN.md — Review mode DB persistence (SRCH-05), history page with expandable session rows (CART-03), tests
**UI hint**: yes

### Phase 7: LLM Config Integration Fix
**Goal**: Ensure all LLM-using endpoints respect the user's configured provider from Settings, not just env vars
**Depends on**: Phase 3, Phase 4
**Requirements**: (integration fix — no new requirements)
**Gap Closure**: Closes integration gap from v1.0 milestone audit
**Success Criteria** (what must be TRUE):
  1. Receipt upload parsing uses get_active_llm_config(db) instead of settings.llm_* env vars
  2. Preference NL chat uses get_active_llm_config(db) instead of settings.llm_* env vars
  3. Changing LLM provider in Settings takes effect on receipt parsing and NL chat without restart
**Plans:** 0/0 plans

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Auth | 4/4 | Complete   | 2026-04-03 |
| 2. Core Loop | 4/4 | Complete   | 2026-04-03 |
| 3. Preference System | 4/4 | Complete   | 2026-04-06 |
| 4. Multi-Provider LLM and Settings | 3/3 | Complete   | 2026-04-06 |
| 5. Hardening and Distribution | 2/2 | Complete   |  |
| 6. Wire Review Mode and Cart History | 0/1 | Planning Complete |  |
| 7. LLM Config Integration Fix | 0/0 | Not Started |  |

---

## Coverage

| Requirement | Phase |
|-------------|-------|
| SETUP-01 | Phase 1 |
| SETUP-02 | Phase 1 |
| SETUP-03 | Phase 1 |
| SETUP-04 | Phase 1 |
| SRCH-01 | Phase 2 |
| SRCH-02 | Phase 2 |
| SRCH-03 | Phase 2 |
| SRCH-04 | Phase 2 |
| SRCH-05 | Phase 6 |
| CART-01 | Phase 2 |
| CART-02 | Phase 2 |
| CART-03 | Phase 6 |
| PREF-01 | Phase 3 |
| PREF-02 | Phase 3 |
| PREF-03 | Phase 3 |
| PREF-04 | Phase 3 |
| PREF-05 | Phase 3 |
| PREF-06 | Phase 3 |
| LLM-01 | Phase 2 |
| LLM-02 | Phase 4 |

**v1 requirements mapped: 20/20**

---
*Created: 2026-04-02*
*Last updated: 2026-04-06 after Phase 6 planning*
