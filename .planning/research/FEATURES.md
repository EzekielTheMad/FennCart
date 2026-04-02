# Feature Landscape

**Domain:** Grocery cart automation / AI shopping assistant (self-hosted, Kroger-connected)
**Researched:** 2026-04-02

---

## Table Stakes

Features users expect from a grocery cart automation tool. Missing any of these and the product feels broken or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Natural language list input | Every AI grocery assistant (Uber Eats Cart Assistant, Albertsons AI, Instacart) accepts free-text lists. Users will not tolerate a form-field-per-item interface. | Low | Paste, type, or dictate. Handle vague inputs ("some cheese", "stuff for tacos") |
| LLM-powered product matching | Products API returns hundreds of results per query. Manual selection defeats the purpose. Semantic matching is the entire value proposition. | High | Must handle brand specificity, unit/size inference, vague descriptions. 48% success rate for state-of-the-art LLMs on shopping tasks — prompting strategy matters enormously. |
| Review step before cart add | Kroger TOS explicitly forbids adding items without user's explicit knowledge. Users expect to confirm before anything hits their cart. | Medium | Cannot skip this. It is both a TOS requirement and a user trust requirement. |
| High-confidence auto-match with exceptions surfacing | Uber Eats Cart Assistant, Albertsons AI both auto-build carts and surface problems. Users hate reviewing 40 items when 35 are obvious. | Medium | "Exceptions-only" default. Toggle to full review available. Confidence threshold is a tunable parameter. |
| Store selection / location | Products API results are store-specific — prices, availability, and fulfillment all vary by location. No store = no useful results. | Low | Kroger Locations API: 1,600 calls/day. One-time setup, persisted. Must be set before any product search. |
| Kroger OAuth login | All cart operations require user-scoped auth. Without it, the app is read-only at best. | Medium | Authorization Code flow with PKCE. 30-min access token, 6-month refresh token. Must handle redirect within Docker/web UI context. |
| BYO credentials setup | Kroger TOS forbids distributing shared developer API keys. Users must bring their own. | Medium | Three credential sets: LLM API key, Kroger developer client ID/secret, Kroger account OAuth. Guided setup wizard is non-negotiable. |
| SQLite persistence | Without persistence, every session starts cold. Preferences, history, and auth tokens must survive restarts. | Low | Docker volume mount. Single-user-per-container model simplifies schema. |
| Fulfillment filtering (curbside) | Kroger Products API returns a fulfillment field indicating method approval. Users doing curbside pickup get burned if they add items only available for in-store. | Low | Filter at query time using `fulfillment=PICKUP` parameter. Not real-time stock — just method eligibility. |
| Token refresh without re-auth | 30-minute access token with silent refresh via stored refresh token. Requiring re-login mid-session destroys UX. | Low | Refresh token lasts 6 months. Check expiry before each API call with 30s buffer. CupOfOwls kroger-api library has this pattern documented. |
| Add to cart with confirmation | Explicit add action, not background automation. User sees what will be added, confirms, then items go to Kroger cart. | Medium | Cart API is add-only (no view, no remove via API). Must maintain local cart state in SQLite to show users what was added. |
| Local cart state tracking | Kroger's public Cart API has no "view cart" endpoint. Users need to know what was added. | Medium | Maintain local shadow of cart additions with timestamp, quantity, product ID. Matches what CupOfOwls kroger-mcp does with kroger_cart.json. |

---

## Differentiators

Features that set FennCart apart from commercial alternatives and justify self-hosting. Not expected, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Receipt PDF parsing for preference bootstrapping | Solves cold-start problem without onboarding surveys. Upload 3-6 months of Fry's receipts and the system knows your brands, sizes, and frequency immediately. | High | LLMs achieve ~97% accuracy on clean receipt PDFs. Accuracy degrades with poor scan quality. Need cross-validation for price/item matching. Output: structured purchase history → preference profile. |
| Living preference profile | Commercial apps (Uber Eats, Instacart) use order history within their platform. FennCart builds a preference model from receipts regardless of purchase channel. Recurring purchases are weighted higher than one-off substitutions. | High | Key design decision: distinguish "I always buy Tillamook medium cheddar" from "I bought store-brand once because Tillamook was out." Confidence decay for infrequently purchased items. |
| Natural language preference updates | "We switched to oat milk" is faster and more natural than navigating a preference settings UI. Commercial products don't offer this. | Medium | LLM interprets command, updates preference store. Edge cases: ambiguous updates ("I don't like that yogurt anymore" — which one?). Need confirmation before applying. |
| Manual preference editing UI | Power-user escape hatch. For users who want direct control over what the system recommends. | Medium | CRUD interface for preference entries. Categories: always prefer (brand), avoid (brand/item), substitute rules. |
| Multi-provider LLM support | Self-hosters value not being locked into one AI provider. Claude, OpenAI, local models (Ollama) all viable. | Medium | Provider abstraction layer. Expose model selection in settings. Local model support is a strong differentiator for privacy-conscious users. |
| Preference-compensated matching | Kroger's Products API returns non-personalized results — prices may differ from the website. Preference system compensates by re-ranking API results based on learned brand/size preferences rather than relying on Kroger's personalization. | High | Core algorithmic challenge. LLM re-ranks candidates returned by Products API using preference profile as context. |
| Shopping history | Track what was added to cart in past sessions. Enables "reorder last week's list" and informs the preference profile over time. | Low | Natural extension of local cart state tracking. Useful for preference profile updates post-shopping. |
| Guided first-run wizard | Three credential sets required before anything works. A bad onboarding kills self-hosted tool adoption. The wizard makes setup tractable for non-developers. | Medium | Step-by-step: LLM key → Kroger developer credentials → OAuth login → store selection → receipt upload (optional). Each step validates before proceeding. |

---

## Anti-Features

Things to explicitly NOT build. Each has a specific reason — TOS constraint, scope creep, or complexity that doesn't pay off.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Coupon clipping automation | Explicit out-of-scope in PROJECT.md. Also, Kroger's coupon API is not part of the public developer offering. | Remind user at cart review to check coupons manually on frysfood.com. |
| Automated checkout or payment | Kroger TOS explicitly prohibits. Legal risk, potential account termination. | Stop at "items added to cart." User completes checkout on Kroger's site/app. |
| Multi-store price comparison | Explicitly prohibited by Kroger TOS: "Cannot compare prices across retailers." Even within Kroger, be careful about surfacing competitor positioning. | Focus on best match within the user's selected store. |
| Real-time stock availability | Kroger's public API does not expose real-time stock. The `fulfillment` field indicates method approval, not current inventory. Displaying stock data would be misleading. | Filter by fulfillment method. Warn user that stock is not guaranteed. |
| Product database persistence | Kroger TOS prohibits storing product data from the API beyond session use. Cannot build a local catalog for faster lookup. | Query Products API live. Cache only within session scope, purge on session end. |
| Background/scheduled cart building | Kroger TOS: cannot add items without user's explicit knowledge/request. Automated background additions violate this. | Always require user-initiated sessions with explicit confirmation. |
| Multi-user / household support (v1) | Adds significant auth complexity (multiple OAuth tokens, preference profile isolation, shared vs. personal preferences). Scope creep for v1. | Single user per container. Multiple households = multiple containers. |
| Mobile native app | Self-hosting audience will manage via browser. Docker + responsive web UI is sufficient. Flutter/React Native adds maintenance burden without meaningful audience gain. | Responsive web UI that works in mobile browser. |
| Pantry inventory tracking | Not the core use case. Grocy and KitchenOwl already do this well as standalone self-hosted tools. Adding it bloats scope significantly. | Recommend Grocy/KitchenOwl integration as future work if demand emerges. |
| Recipe-to-cart features | Interesting, but second-order complexity. Recipe parsing, ingredient normalization, serving size math — all distract from the core list-to-cart flow. | Consider as Phase 2+ feature if core product validates. |
| Meal planning | Same as recipe features. Albertsons AI, Uber Eats Cart Assistant both plan to add this. Let them prove the demand. | Out of scope for v1. |

---

## Feature Dependencies

```
Store selection
  → Products API search (required: locationId parameter)
    → LLM product matching (required: candidates to rank)
      → Preference profile (required: preferences to apply to ranking)
        → Receipt parsing (populates preference profile)
      → Review flow (required: match candidates)
        → Cart add (required: confirmed selections)
          → Local cart state (records what was added)
            → Shopping history (aggregates cart state over sessions)

Kroger OAuth login
  → Cart add (required: user-scoped token)

BYO credentials setup (wizard)
  → All API calls (required: LLM key + Kroger developer credentials + Kroger OAuth)

Preference profile
  ← Receipt PDF parsing (bootstrap)
  ← Natural language preference updates (ongoing)
  ← Manual preference editing UI (override)
  ← Shopping history (implicit feedback)

Token management (refresh)
  → All authenticated Kroger API calls
```

Critical path for MVP:
`Credentials wizard → Store selection → Token management → Natural language input → Products API search → LLM matching → Review flow → Cart add → Local cart state`

Preference system can be added incrementally — first run works with no preferences (LLM makes best-guess matches), preferences improve results over time.

---

## MVP Recommendation

The minimum viable product that delivers the core value proposition (rough list → loaded cart) without the full preference system:

**Prioritize for MVP:**
1. Guided credentials setup wizard — without this, nobody gets past setup
2. Store selection — required for all product queries
3. Kroger OAuth with silent token refresh — required for cart operations
4. Natural language list input — core UX entry point
5. LLM-powered product matching (no preferences yet, best-guess ranking) — core value
6. Exceptions-only review flow with full-review toggle — trust and TOS compliance
7. Cart add with explicit confirmation — TOS requirement and user trust
8. Local cart state tracking — compensates for Cart API's no-view limitation
9. Fulfillment filtering (curbside) — prevents "item not available for pickup" failures
10. SQLite persistence (auth tokens, store selection) — basic session durability

**Defer from MVP:**
- Receipt PDF parsing: Valuable but adds significant complexity. First run works with no preference data (LLM guesses well for generic items). Add in Phase 2.
- Preference profile: Same. System works without it. Preferences make it better.
- Natural language preference updates: Requires preference profile to exist first.
- Manual preference editing UI: Requires preference profile to exist first.
- Multi-provider LLM support: Start with one provider (Claude or OpenAI). Add abstraction layer in Phase 2.
- Shopping history: Nice-to-have, not blocking.

**Rationale:**
The core value — "paste a list, get a loaded cart" — is achievable without the preference system. Receipt parsing and preference learning are what make the second and subsequent uses great. Ship the core loop first, validate it works, then layer in the intelligence.

---

## Sources

- [Uber Eats Cart Assistant launch — TechCrunch (Feb 2026)](https://techcrunch.com/2026/02/11/uber-eats-launches-ai-assistant-to-help-with-grocery-cart-creation/)
- [Uber Eats Cart Assistant features — Axios (Feb 2026)](https://www.axios.com/2026/02/11/uber-eats-ai-grocery-cart-assistant)
- [Uber Eats Cart Assistant — Digital Commerce 360 (Feb 2026)](https://www.digitalcommerce360.com/2026/02/11/uber-eats-cart-assistant-ai-tool-grocery-shopping/)
- [Albertsons AI Shopping Assistant announcement (2025)](https://www.albertsonscompanies.com/newsroom/press-releases/news-details/2025/Albertsons-Companies-Accelerates-Digital-Transformation-with-the-Albertsons-AI-Shopping-Assistant-Redefining-the-Grocery-Shopping-Experience/default.aspx)
- [Kroger Cart API — developer.kroger.com](https://developer.kroger.com/reference/api/cart-api-public)
- [Kroger Products API overview — developer.kroger.com](https://developer.kroger.com/documentation/api-products/public/products/overview)
- [Automate Your Groceries: Kroger MCP Server deep dive — Skywork AI](https://skywork.ai/skypage/en/automate-groceries-kroger-mcp/1981657738520883200)
- [ShoppingComp: Are LLMs Ready for Your Shopping Cart? — arXiv (2024)](https://arxiv.org/html/2511.22978v1)
- [Receipt OCR Benchmark with LLMs — AIMultiple Research](https://research.aimultiple.com/receipt-ocr/)
- [Cold Start Problem Guide 2025 — ShadeCoder](https://www.shadecoder.com/topics/cold-start-problem-a-comprehensive-guide-for-2025)
- [Kroger API refresh token tutorial — developer.kroger.com](https://developer.kroger.com/documentation/partner/refresh-token-tutorial)
- [CupOfOwls kroger-api Python client — GitHub](https://github.com/CupOfOwls/kroger-api)
- [Online Grocery UX best practices — Baymard Institute](https://baymard.com/blog/grocery-ecommerce-benchmark)
- [Grocery List Automation App Market Report 2033 — Dataintelo](https://dataintelo.com/report/grocery-list-automation-app-market)
