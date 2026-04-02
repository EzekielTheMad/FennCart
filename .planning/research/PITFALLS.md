# Domain Pitfalls

**Domain:** Self-hosted grocery cart automation — Kroger API + LLM + OAuth + Docker
**Researched:** 2026-04-02
**Overall confidence:** MEDIUM (Kroger API behavior from docs + reference implementations; Docker/SQLite/LLM from verified community sources)

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

---

### Pitfall 1: Kroger Developer Credentials Embedded in the Repository

**What goes wrong:** The open source project ships with a default Kroger `client_id`/`client_secret` baked into config, environment defaults, or Docker Compose — violating the Kroger API Terms of Service and immediately exposing credentials to anyone who clones the repo.

**Why it happens:** Developers set convenience defaults during early development and forget to scrub them before publishing. Git history preserves secrets even after file edits — a secret committed once is recoverable forever via `git log -p`.

**Consequences:** Kroger can terminate the entire developer application key, breaking all users of the project simultaneously. GitHub secret scanning (enabled by default on public repos since 2024) may auto-revoke detected keys. The project creator assumes legal liability.

**Prevention:**
- Never use a default value for `KROGER_CLIENT_ID` or `KROGER_CLIENT_SECRET` — the app must refuse to start if they are absent
- Add `.env` to `.gitignore` before the first commit; add a pre-commit hook (gitleaks or git-secrets) to block any accidental commit
- Document in README and setup wizard: "Each user must register their own app at developer.kroger.com"
- Provide `.env.example` with placeholder strings like `YOUR_KROGER_CLIENT_ID_HERE`, never real values

**Detection (warning signs):**
- Any default value for credential env vars in `docker-compose.yml` or application config
- `.env` file not listed in `.gitignore`
- `git log --all -S "client_secret"` returns hits

**Phase:** Must be enforced from the very first commit. Address in Phase 1 (project scaffolding / setup wizard).

---

### Pitfall 2: OAuth Redirect URI Mismatch in Docker

**What goes wrong:** The Kroger OAuth flow redirects the user's browser to the registered `redirect_uri` after login. Inside Docker, the app's internal hostname (e.g., `http://fenncart:8080/auth/callback`) is not what the user's browser can reach. If the registered URI doesn't exactly match the request URI (including protocol, host, port, and path — byte for byte), Kroger rejects the flow with an `invalid_redirect_uri` error.

**Why it happens:** Docker networking separates internal container hostnames from the external address a browser uses. When running on `localhost`, the external address is `http://localhost:PORT` but the container might generate callback URLs using its own container name. Registration on developer.kroger.com must match what the end user's browser sends.

**Consequences:** OAuth flow silently fails. Users cannot authenticate. The app is unusable without developer intervention.

**Prevention:**
- Expose a configurable `BASE_URL` / `EXTERNAL_URL` environment variable that defaults to `http://localhost:8080`; all OAuth redirect URIs must be built from this variable, not from internal hostnames
- In the first-run setup wizard, display the exact redirect URI the user must register in their Kroger developer app before proceeding
- Document that `http://localhost` is an acceptable redirect URI for Kroger's public API (common OAuth providers allow this for self-hosted/native apps)
- Test the full OAuth flow end-to-end in Docker before any release

**Detection (warning signs):**
- OAuth callback URL constructed from `request.host` or a container-internal name rather than from a configured external URL
- `redirect_uri` error from Kroger during OAuth

**Phase:** Address in Phase 1 (auth / setup wizard). Validate the full redirect flow in a Docker container, not just bare Python.

---

### Pitfall 3: Kroger TOS — Persistent Storage of Search/API Response Data

**What goes wrong:** The app caches Kroger Products API results in SQLite to reduce API calls. This crosses into the prohibited "building a product database from API responses" if the cache is persistent across sessions or is retained long-term.

**Why it happens:** It's natural to cache expensive API calls. The distinction between "session cache" (allowed) and "persistent product database" (prohibited) is easy to blur when using SQLite with no TTL.

**Consequences:** Kroger can terminate the developer application. If the project is open source and the database schema shows a products table with no expiry, it is evidence of TOS violation.

**Prevention:**
- Never write Kroger Products API results to a table without a strict TTL column; delete rows older than the session (or a short wall-clock window, e.g., 24 hours)
- Do NOT build a separate `products` table that persists across restarts; OK to cache within a request or an in-memory session store
- Store only user-derived data (preference profiles built from user-uploaded receipts, shopping history) in the durable SQLite volume; distinguish this clearly in the schema design
- Add a comment in schema migrations explaining which tables are TOS-restricted

**Detection (warning signs):**
- A `products` or `search_results` table in SQLite with no `expires_at` or `created_at` column
- Code that re-queries the local DB for products without a freshness check

**Phase:** Design schema with TTL from the start (Phase 1 / data model). Review in any phase that adds new tables.

---

### Pitfall 4: Cart API is Add-Only — No Read-Back, No Remove

**What goes wrong:** The Kroger Cart API can only add items. It cannot read current cart contents or remove items. If the app adds an item twice (e.g., user retries a failed submission, or re-runs the same list), duplicates accumulate silently in the real cart.

**Why it happens:** Developers assume a typical cart API has CRUD operations. Kroger's doesn't. Without a local shadow of the cart, there's no way to detect duplicate additions.

**Consequences:** User ends up with double quantities of items in their Fry's cart and only notices at checkout or curbside pickup.

**Prevention:**
- Maintain a local session-scoped cart shadow in SQLite (or in-memory for the session) that tracks every successful `PUT /cart/add` call with item, quantity, and timestamp
- Before adding an item, check the local shadow; if the item is already in the session cart, warn the user rather than adding again
- Clear the shadow when the user explicitly starts a new shopping session or after cart confirmation
- Surface a "items in current cart" view to the user, clearly labeling it "local tracking only — view your full cart on frysfood.com"

**Detection (warning signs):**
- No local cart state tracked anywhere in the codebase
- "Add to cart" action with no idempotency check

**Phase:** Address in Phase 2 (cart building feature). Do not defer — the add-only constraint shapes the entire cart flow.

---

## Moderate Pitfalls

---

### Pitfall 5: LLM Cost Runaway on Large Shopping Lists

**What goes wrong:** Each shopping session sends the user's full list + preference profile + Kroger search results as context to the LLM. For a 50-item list with a rich preference profile and 10 product candidates per item, the prompt can easily reach 20,000–40,000 tokens per session. At Claude or GPT-4 pricing, this is $0.20–$1.00 per grocery run — invisible during development but noticed immediately when users start using it.

**Why it happens:** No token budget is set on the prompt construction. Output tokens (ranked results + rationale) can also balloon without a `max_tokens` cap.

**Consequences:** Users with LLM API keys burn through credits fast. Project gets a reputation as "expensive." Users switch to local models or abandon the project.

**Prevention:**
- Set an explicit `max_tokens` on every LLM call (150–300 tokens is sufficient for product ranking output)
- Batch product matching: don't send all 50 items in one prompt; process in batches of 10–15 items
- Trim the preference profile context: only include relevant preference categories for the items being matched in each batch (e.g., don't send dairy preferences when matching paper towels)
- Implement prompt caching for static system prompt content (Claude and OpenAI both support prefix caching at ~10% of input token cost)
- Display estimated token usage in the UI before calling the LLM; let users see per-session cost

**Detection (warning signs):**
- No `max_tokens` parameter in LLM API calls
- Full preference profile sent on every call regardless of item category
- No token counting before submitting prompts

**Phase:** Address in Phase 2 (LLM matching feature). Measure token usage in development with real shopping lists.

---

### Pitfall 6: Kroger Products API Rate Limits Exhausted by Naive Search

**What goes wrong:** The Products API allows 10,000 calls/day and the Cart API allows 5,000 calls/day. A naive implementation that issues one search query per shopping list item, with multiple retry attempts, can hit the limit in a single heavy session (50-item list × 3 search refinements = 150 calls; ten sessions = 1,500 calls; heavy PDF import parsing = thousands more).

**Why it happens:** Rate limits seem generous until you account for setup flows, preference-building from receipts, and search refinement iterations.

**Consequences:** The app returns 429 errors, the user's session breaks, and no further cart additions can be made for the rest of the day.

**Prevention:**
- Cache Products API responses with a short TTL (e.g., 1 hour) using an in-memory or SQLite cache keyed on `(query_term, location_id)`; don't re-query for the same search term in the same session
- Track daily API call counts in SQLite; surface remaining quota in the UI
- Batch search queries: search for the broad category, then filter results client-side rather than issuing separate narrow queries
- During receipt PDF import, search for products lazily (on demand) rather than eagerly for every line item

**Detection (warning signs):**
- No caching layer between the LLM matching loop and Kroger API calls
- 429 responses seen during load testing or heavy sessions

**Phase:** Address in Phase 2 (Kroger API integration). Build the cache layer before writing the LLM matching loop.

---

### Pitfall 7: Receipt PDF Parsing Fails Silently on Non-Standard Formats

**What goes wrong:** Kroger/Fry's digital receipts vary by source: emailed PDF receipts differ from receipts downloaded from the Fry's app, which differ from scanned paper receipts. Line item formats, abbreviations (e.g., "PRIV SEL CHCKN BRST" for "Private Selection Chicken Breast"), and encoding vary significantly. A parser tuned on one format produces garbage or empty output on another without raising an error.

**Why it happens:** PDF parsing libraries (PyMuPDF, pdfplumber, pdfminer) extract raw text; the structure of that text depends entirely on how the PDF was generated. Fry's abbreviates product names heavily to fit receipt width. There are no UPCs on the receipt line items in most formats.

**Consequences:** Preference profile is silently incomplete or corrupted. Users see products they didn't buy included, or products they bought missing. Cold-start problem is not actually solved.

**Prevention:**
- Use an LLM to parse receipt line items rather than regex/heuristics — the LLM handles abbreviations and variations far better
- Always return a structured result with a `confidence` field per parsed line item; surface low-confidence items to the user for review
- Test with at least three real receipt formats: emailed PDF, app-downloaded PDF, and a scanned image before shipping the feature
- Never silently discard a receipt — show the user how many items were extracted and prompt them to review
- Document that handwritten lists and photos of paper receipts are out of scope for v1

**Detection (warning signs):**
- Parser returns 0 items with no user-visible error
- Only tested against one receipt sample during development

**Phase:** Address in Phase 3 (receipt parsing / preference profile feature). Flag for deep research before implementation.

---

### Pitfall 8: SQLite "Database Is Locked" Under Async Concurrency

**What goes wrong:** An async Python web server (FastAPI, Starlette) handles multiple requests concurrently. If two coroutines attempt to write to SQLite simultaneously — e.g., saving a preference update while an ongoing cart session writes shopping history — SQLite throws `OperationalError: database is locked`.

**Why it happens:** SQLite allows only one writer at a time. Python's default `sqlite3` module uses blocking I/O, which stalls the event loop. Without WAL mode and a busy timeout, the second writer fails immediately.

**Consequences:** Intermittent 500 errors during concurrent operations. Difficult to reproduce in development (single user). Appears as data loss or crashes in production.

**Prevention:**
- Enable WAL journal mode at database initialization: `PRAGMA journal_mode=WAL`
- Set a busy timeout on every connection: `PRAGMA busy_timeout=5000` (5 seconds)
- Use `BEGIN IMMEDIATE` for write transactions to acquire the write lock upfront rather than upgrading lazily
- Use `aiosqlite` or `SQLAlchemy` with the async SQLite driver rather than bare `sqlite3` in an async app
- Keep writes short and transactional; avoid holding open write transactions across awaitable calls

**Detection (warning signs):**
- Bare `sqlite3.connect()` in an async FastAPI route handler
- No `journal_mode=WAL` in database initialization
- `OperationalError` in logs under any load

**Phase:** Address in Phase 1 (database setup). One-time configuration that prevents chronic issues.

---

### Pitfall 9: Docker Volume Data Loss on Container Rebuild

**What goes wrong:** User rebuilds or updates the Docker container image (`docker compose up --build`) and loses all their preference data and receipt history because SQLite was stored inside the container filesystem rather than on a named volume.

**Why it happens:** It's easy to write the database path as a relative path like `./data/fenncart.db` in development. When the container is rebuilt, this path lives inside the image layer and is wiped on recreation.

**Consequences:** User loses their entire preference profile, receipt history, and shopping history. Trust destroyed on first update.

**Prevention:**
- Define a named Docker volume in `docker-compose.yml` (e.g., `fenncart_data`) mounted to a fixed internal path (e.g., `/data/fenncart.db`)
- Never write the database to a path inside the container's writable layer
- Document the volume in README: "Your data lives in the `fenncart_data` Docker volume. Back it up before upgrading."
- Add a database migration framework (e.g., Alembic) from day one so schema changes on upgrade don't require wiping the database

**Detection (warning signs):**
- No `volumes:` key in `docker-compose.yml`
- SQLite database path not mounted from a named volume
- Data disappears after `docker compose down && docker compose up`

**Phase:** Address in Phase 1 (Docker setup). Must be correct before any user data is written.

---

### Pitfall 10: Kroger Access Token Expiry Not Handled — Silent 401 Failures

**What goes wrong:** Kroger access tokens expire after 30 minutes. If the app stores the access token but does not proactively check expiry or handle 401 responses by refreshing, API calls silently fail after the token expires mid-session (e.g., midway through adding cart items).

**Why it happens:** Token expiry is easy to handle in the happy path (initial auth flow) but easy to miss in background operations or long review sessions where the user sits on the confirmation page for more than 30 minutes.

**Consequences:** Cart additions silently fail or throw uncaught exceptions. The user thinks items were added when they weren't.

**Prevention:**
- Store token expiry timestamp alongside the access token; always check before use and refresh proactively if within 60 seconds of expiry
- Handle 401 responses from every Kroger API call with an automatic single retry after token refresh; never surface a raw 401 to the user
- Refresh tokens have a 6-month lifetime; store them encrypted in the SQLite volume; never store in a plain env var that is logged
- Test token expiry explicitly: mock a token that expires in 5 seconds and verify the refresh flow works end-to-end

**Detection (warning signs):**
- Token stored but expiry timestamp not stored alongside it
- No retry logic on 401 in Kroger API client code
- Users report "items not added" after leaving the review page open

**Phase:** Address in Phase 1 (auth infrastructure). Token lifecycle must be solid before building any feature that calls the Kroger API.

---

## Minor Pitfalls

---

### Pitfall 11: Non-Personalized API Results Feel "Wrong" to Users

**What goes wrong:** Kroger's Products API returns non-personalized results — it does not apply the user's Fry's loyalty card deals, digital coupons, or personalized pricing. The prices shown in the app may differ from what the user sees on the Fry's website (which is personalized). Users report "wrong prices" and lose trust.

**Prevention:** Document this prominently in the UI ("Prices shown are non-personalized and may differ from your Fry's app"). Direct users to verify final prices at frysfood.com at checkout. Do not present prices as definitive.

**Phase:** UI copy decision in Phase 2 (cart review flow).

---

### Pitfall 12: Kroger `fulfillment` Field Misunderstood as Live Stock

**What goes wrong:** The `fulfillment` field on Products API results indicates whether a product is *approved* for curbside pickup — not whether it is currently *in stock*. Filtering by `fulfillment=csp` does not guarantee the item is available when the user's pickup order is processed.

**Prevention:** Never label items as "in stock." Use language like "eligible for curbside pickup" rather than "available." Users should expect occasional substitutions from the store.

**Phase:** UI copy and product display in Phase 2.

---

### Pitfall 13: LLM Hallucinating Product Names That Don't Exist in Kroger

**What goes wrong:** The LLM generates a "best match" product name that sounds plausible but doesn't match any real Kroger SKU. The downstream Products API search returns zero results or completely wrong products.

**Prevention:** The LLM should generate structured search queries for the Kroger Products API, not final product names. The match decision must be made against actual API results, not LLM-generated names. The LLM ranks real API results; it does not fabricate them.

**Phase:** LLM matching architecture in Phase 2. This is a design constraint, not a runtime fix.

---

### Pitfall 14: First-Run Setup Wizard Credentials Stored in Plain Text Logs

**What goes wrong:** During the setup wizard, credentials (LLM API key, Kroger client secret, OAuth tokens) are logged at DEBUG level for troubleshooting. Log files end up in Docker volume or stdout and are captured by any log aggregation tool.

**Prevention:** Use a custom log formatter that redacts known secret field names (any field matching `*key*`, `*secret*`, `*token*`, `*password*`). Never log raw credential values at any level. Test with DEBUG logging enabled and audit the output.

**Phase:** Logging infrastructure in Phase 1.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Phase 1: Project scaffold + Docker | Docker volume not mounted; SQLite path inside container | Use named volume from day one; test rebuild persistence before adding any features |
| Phase 1: Auth / setup wizard | OAuth redirect URI mismatch in Docker; credential committed to git | Configurable BASE_URL; no credential defaults; pre-commit hook |
| Phase 1: Database init | SQLite locking under async; no WAL mode | Enable WAL + busy_timeout at first connection |
| Phase 1: Logging | Credentials in DEBUG logs | Redacting log formatter before any credential is handled |
| Phase 2: Kroger API integration | Token expiry mid-session; rate limit exhaustion | Auto-refresh on 401; Products API response cache with TTL |
| Phase 2: LLM matching | Token cost runaway; LLM hallucinating product names | max_tokens cap; LLM ranks real results, doesn't generate names |
| Phase 2: Cart building | Duplicate adds from add-only API | Local cart shadow; idempotency check before each add |
| Phase 2: Product display | Misleading stock/price information | Non-personalized price caveat; "eligible" not "in stock" |
| Phase 3: Receipt PDF parsing | Silent parse failures on format variation | LLM-assisted parsing; confidence scoring; user review of extracted items |
| Phase 3: Preference profile | Misattributing one-off substitutions as permanent preferences | Distinguish "purchased once" from "recurring preference" in schema |
| All phases: Open source distribution | Kroger credentials in repo; persistent API response cache | Mandatory BYO-credentials; TTL on all cached API data |

---

## Sources

- Kroger Developer Portal FAQ: https://developer.kroger.com/support/faq
- Kroger Refresh Token Tutorial: https://developer.kroger.com/documentation/partner/refresh-token-tutorial
- CupOfOwls kroger-api reference implementation: https://github.com/CupOfOwls/kroger-api
- Kroger MCP Server (cart shadow pattern): https://skywork.ai/skypage/en/automate-groceries-kroger-mcp/1981657738520883200
- SQLite WAL mode official docs: https://sqlite.org/wal.html
- SQLite concurrent writes and "database is locked": https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/
- SQLite in Docker: https://oneuptime.com/blog/post/2026-02-08-how-to-run-sqlite-in-docker-when-and-how/view
- Docker secrets management (GitGuardian): https://blog.gitguardian.com/how-to-handle-secrets-in-docker/
- Dockerfile secrets layer persistence: https://xygeni.io/blog/dockerfile-secrets-why-layers-keep-your-sensitive-data-forever/
- OAuth redirect URI in Docker (n8n community): https://community.n8n.io/t/oauth-redirect-docker-compose/13254
- OAuth redirect URI mismatch fix: https://www.reform.app/blog/fixing-oauth-2-0-redirect-uri-mismatches
- LLM token cost optimization: https://www.glukhov.org/post/2025/11/cost-effective-llm-applications
- LLM rate limiting and quotas: https://www.truefoundry.com/blog/rate-limiting-in-llm-gateway
- GitHub secret leaks scale (2024): https://medium.com/@instatunnel/github-secret-leaks-the-13-million-api-credentials-sitting-in-public-repos-1a3babfb68b1
- Receipt OCR edge cases: https://pyimagesearch.com/2021/10/27/automatically-ocring-receipts-and-scans/
