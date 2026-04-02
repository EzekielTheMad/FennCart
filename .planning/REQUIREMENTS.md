# Requirements: Fenn Cart

**Defined:** 2026-04-02
**Core Value:** Go from a rough shopping list to a fully loaded Fry's curbside pickup cart with minimal effort, matching brand and price preferences automatically.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Setup & Credentials

- [ ] **SETUP-01**: User can complete a guided first-run wizard (LLM API key, Kroger developer credentials, Kroger OAuth login, store selection)
- [ ] **SETUP-02**: User can select their Fry's/Kroger store location via zip code search
- [ ] **SETUP-03**: User can authenticate with Kroger via OAuth PKCE flow within the web UI
- [ ] **SETUP-04**: App silently refreshes Kroger access tokens using stored refresh token (6-month validity)

### Product Search & Matching

- [ ] **SRCH-01**: User can input a natural language shopping list (paste, type, free-form text)
- [ ] **SRCH-02**: App uses LLM to interpret list items and match them to Kroger Products API results
- [ ] **SRCH-03**: App filters product results to items available for curbside pickup fulfillment
- [ ] **SRCH-04**: App auto-matches high-confidence items and surfaces uncertain matches for review (exceptions-only default)
- [ ] **SRCH-05**: User can toggle between exceptions-only and full review modes

### Cart Management

- [ ] **CART-01**: User can review matched products and explicitly confirm before items are added to Kroger cart
- [ ] **CART-02**: App maintains local cart state in SQLite (product, quantity, price, timestamp) since Cart API has no view endpoint
- [ ] **CART-03**: User can see what was added to cart in the current session

### Preference System

- [ ] **PREF-01**: User can upload Fry's receipt PDFs to bootstrap their preference profile
- [ ] **PREF-02**: App parses receipt PDFs and extracts purchase history (items, brands, sizes, quantities, prices)
- [ ] **PREF-03**: App builds a living preference profile weighted by purchase frequency, distinguishing recurring preferences from one-off substitutions
- [ ] **PREF-04**: User can update preferences via natural language ("we switched to oat milk", "stop buying Kroger brand yogurt")
- [ ] **PREF-05**: User can manually view, add, edit, and delete preference entries
- [ ] **PREF-06**: LLM product matching uses the preference profile to re-rank Kroger API results

### LLM Provider Support

- [ ] **LLM-01**: App supports multiple LLM providers (Claude, OpenAI, local models via Ollama) through a provider abstraction layer
- [ ] **LLM-02**: User can select and configure their preferred LLM provider and model in settings

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Shopping History

- **HIST-01**: User can view past shopping sessions with items, prices, and dates
- **HIST-02**: User can reorder items from a previous shopping session
- **HIST-03**: Shopping history feeds into preference profile updates over time

### Advanced Features

- **ADV-01**: User can import shopping lists from external sources (Apple Notes, Google Keep)
- **ADV-02**: App suggests items based on purchase frequency patterns ("You usually buy milk every week")

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Coupon clipping automation | Not available via Kroger public API; manual during checkout |
| Automated checkout or payment | Prohibited by Kroger TOS; legal risk |
| Multi-store price comparison | Explicitly prohibited by Kroger TOS |
| Real-time stock availability | Kroger API does not expose stock data; fulfillment field is method approval only |
| Product database persistence | Prohibited by Kroger TOS; cannot cache API product data beyond session |
| Background/scheduled cart building | Kroger TOS requires explicit user knowledge for cart additions |
| Multi-user / household support | Adds auth complexity; single user per container in v1 |
| Mobile native app | Responsive web UI sufficient; Docker + browser is the model |
| Pantry inventory tracking | Grocy/KitchenOwl serve this well; out of scope for cart automation |
| Recipe-to-cart features | Second-order complexity; defer until core loop is validated |
| Meal planning | Same as recipe features; let commercial products prove demand |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Pending |
| SETUP-02 | Phase 1 | Pending |
| SETUP-03 | Phase 1 | Pending |
| SETUP-04 | Phase 1 | Pending |
| SRCH-01 | Phase 2 | Pending |
| SRCH-02 | Phase 2 | Pending |
| SRCH-03 | Phase 2 | Pending |
| SRCH-04 | Phase 2 | Pending |
| SRCH-05 | Phase 2 | Pending |
| CART-01 | Phase 2 | Pending |
| CART-02 | Phase 2 | Pending |
| CART-03 | Phase 2 | Pending |
| PREF-01 | Phase 3 | Pending |
| PREF-02 | Phase 3 | Pending |
| PREF-03 | Phase 3 | Pending |
| PREF-04 | Phase 3 | Pending |
| PREF-05 | Phase 3 | Pending |
| PREF-06 | Phase 3 | Pending |
| LLM-01 | Phase 2 | Pending |
| LLM-02 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-04-02*
*Last updated: 2026-04-02 after roadmap creation*
