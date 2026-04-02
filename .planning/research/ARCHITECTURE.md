# Architecture Patterns

**Domain:** Self-hosted Docker web app — grocery cart automation with external API, LLM, OAuth
**Project:** FennCart
**Researched:** 2026-04-02

---

## Recommended Architecture

### Overview

Single-container, single-process web application. FastAPI serves both the REST API and the compiled React frontend from one process. SQLite on a Docker volume handles all persistence. There is no separate database service, no reverse proxy sidecar, and no external LLM gateway — complexity is kept inside one container boundary.

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Container                         │
│                                                             │
│  ┌────────────┐    ┌─────────────────────────────────────┐  │
│  │  React UI  │    │           FastAPI Process           │  │
│  │  (static,  │◄───│                                     │  │
│  │ built into │    │  ┌──────────┐  ┌─────────────────┐  │  │
│  │  /static)  │    │  │  Router  │  │  LLM Service    │  │  │
│  └────────────┘    │  │  Layer   │  │  (LiteLLM SDK)  │  │  │
│                    │  └────┬─────┘  └────────┬────────┘  │  │
│                    │       │                  │           │  │
│                    │  ┌────▼────────────────▼──────────┐ │  │
│                    │  │        Service Layer            │ │  │
│                    │  │  - Cart Service                 │ │  │
│                    │  │  - Preference Service           │ │  │
│                    │  │  - Receipt Parser Service       │ │  │
│                    │  │  - Kroger API Client            │ │  │
│                    │  │  - OAuth Token Manager          │ │  │
│                    │  └────────────────┬────────────────┘ │  │
│                    │                   │                   │  │
│                    │  ┌────────────────▼────────────────┐ │  │
│                    │  │    SQLite (via SQLModel/         │ │  │
│                    │  │    aiosqlite on /data/app.db)   │ │  │
│                    │  └─────────────────────────────────┘ │  │
│                    └─────────────────────────────────────┘  │
│                                                             │
│  Docker Volume: /data  (persists app.db across restarts)   │
└─────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
  Kroger Public API            LLM Provider APIs
  (products, cart,          (Anthropic, OpenAI,
   locations, OAuth)         local Ollama endpoint)
```

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| React UI | Rendering, user input, review flow, setup wizard | FastAPI REST endpoints only (no direct external calls) |
| FastAPI Router Layer | HTTP request handling, auth middleware, input validation | Service Layer |
| LLM Service | Abstracts provider differences, formats prompts, parses responses | LiteLLM Python SDK → LLM provider APIs |
| Kroger API Client | All HTTP calls to Kroger endpoints (products, cart, locations) | Kroger Public API, OAuth Token Manager |
| OAuth Token Manager | Stores/refreshes Kroger OAuth tokens, manages PKCE state | Kroger Authorization endpoints, SQLite |
| Cart Service | Orchestrates the list→match→review→add flow | LLM Service, Kroger API Client, Preference Service, SQLite |
| Preference Service | Reads/updates/applies brand and product preferences | SQLite |
| Receipt Parser | Extracts structured purchase data from uploaded PDFs | pdfplumber/pymupdf → LLM Service for entity extraction → Preference Service |
| Setup Wizard Backend | Validates credentials, stores initial config, triggers first OAuth | All services (initial wiring) |
| SQLite (via SQLModel) | Persistence for preferences, receipts, shopping history, OAuth tokens, config | Service Layer only — never directly from UI or Router |

**Hard boundaries:**

- The UI never calls Kroger or LLM APIs directly. All external calls go through the FastAPI backend. This is required to protect credentials (Kroger TOS) and to avoid CORS/auth complexity in the browser.
- The Router Layer never touches SQLite directly. All DB access flows through the Service Layer.
- The LLM Service is the only component aware of which LLM provider is configured. Other services call `llm_service.complete(prompt)` and get structured output back.
- TOS constraint: customer search data (Kroger product query terms derived from user shopping lists) must not persist. Cart Service must not write raw user list queries to SQLite — only matched results with user confirmation are logged.

---

## Data Flow

### Primary Flow: Shopping List to Cart

```
User pastes list (UI)
  → POST /api/cart/match (Router)
    → Cart Service: parse list items
    → Preference Service: load user brand/product preferences
    → Kroger API Client: Products API search per item (up to rate limit)
    → LLM Service: rank/select best match per item using preferences + results
    → Cart Service: partition into high-confidence (auto) vs. low-confidence (review)
  ← Return: review payload {auto_items[], review_items[]}
User reviews and confirms (UI)
  → POST /api/cart/add (Router)
    → Cart Service: receive confirmed items
    → Kroger API Client: Cart API add per item
    → Cart Service: log shopping session to SQLite (confirmed items only — TOS)
  ← Return: success/failure per item
```

### OAuth Flow: Kroger Account Authorization

```
User initiates auth (UI → button click)
  → GET /api/auth/kroger/start (Router)
    → OAuth Token Manager: generate PKCE code_verifier + code_challenge
    → OAuth Token Manager: store state + verifier in SQLite (short-lived)
    → Build Kroger authorization URL with redirect_uri = http://localhost:{PORT}/api/auth/kroger/callback
  ← 302 Redirect to Kroger authorization page (browser follows)

User logs in at Kroger (external browser)
  → Kroger redirects to http://localhost:{PORT}/api/auth/kroger/callback?code=...&state=...
    → OAuth Token Manager: validate state parameter (CSRF guard)
    → OAuth Token Manager: exchange code + code_verifier for access + refresh tokens
    → OAuth Token Manager: store encrypted tokens in SQLite
  ← 302 Redirect to UI (success page)
```

This works in Docker because the container port is mapped to `localhost` on the host. The redirect URI `http://localhost:PORT/callback` is valid for this self-hosted single-user deployment.

### Receipt Upload and Preference Learning

```
User uploads PDF receipt (UI)
  → POST /api/receipts/upload (Router)
    → Receipt Parser: extract text with pdfplumber
    → Receipt Parser: LLM Service: "extract line items as structured JSON from this grocery receipt text"
    → Preference Service: upsert items into preference profile (brand, price point, frequency)
  ← Return: parsed items for user review/correction
User confirms/edits parsed items (UI)
  → POST /api/receipts/confirm (Router)
    → Preference Service: finalize preference updates
```

### Preference Update (Natural Language)

```
User types "we switched to oat milk" (UI)
  → POST /api/preferences/update-nl (Router)
    → LLM Service: "interpret this preference instruction and return structured preference delta"
    → Preference Service: apply delta to profile
  ← Return: preview of what changed
```

---

## Patterns to Follow

### Pattern 1: Service Layer as the Only DB Gate

**What:** All SQLite access lives in service classes. Routers call services, services call the DB. No raw SQL in route handlers.

**When:** Always.

**Example:**
```python
# Router
@router.post("/cart/match")
async def match_cart(request: MatchRequest, cart_svc: CartService = Depends()):
    return await cart_svc.match_items(request.items)

# Service
class CartService:
    def __init__(self, db: AsyncSession, llm: LLMService, kroger: KrogerClient):
        self.db = db
        self.llm = llm
        self.kroger = kroger

    async def match_items(self, items: list[str]) -> MatchResult:
        prefs = await self.preference_svc.get_profile()
        results = await self.kroger.search_products(items)
        ranked = await self.llm.rank_matches(items, results, prefs)
        # Do NOT persist raw `items` — TOS
        return ranked
```

### Pattern 2: LLM Service Encapsulates Provider

**What:** One `LLMService` class wraps LiteLLM SDK. Provider (Claude, OpenAI, Ollama) is a config value, not a code branch.

**When:** All LLM calls.

**Example:**
```python
class LLMService:
    def __init__(self, provider: str, model: str, api_key: str | None):
        self.model = model  # e.g. "anthropic/claude-3-5-haiku", "openai/gpt-4o-mini", "ollama/llama3"
        self.api_key = api_key

    async def complete_structured(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        response = await litellm.acompletion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            api_key=self.api_key,
            response_format=schema,
        )
        return schema.model_validate_json(response.choices[0].message.content)
```

### Pattern 3: Multi-Stage Docker Build for Single Container

**What:** Stage 1 builds the React/Vite app. Stage 2 copies the built `/dist` into the Python image. FastAPI mounts the static directory and has a catch-all route returning `index.html` for SPA routing.

**When:** Dockerfile only — no nginx sidecar needed for single-user local deployment.

```dockerfile
FROM node:22 AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./static/
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 4: OAuth Token Storage Encrypted at Rest

**What:** Kroger access and refresh tokens stored in SQLite with application-level encryption (Fernet symmetric key derived from a per-install secret stored in `config.json` on the Docker volume).

**When:** Any write of OAuth tokens to DB.

**Why:** SQLite files are plaintext by default. Docker volumes are on the host filesystem. For a single-user local app, this is defense-in-depth, not compliance theater.

### Pattern 5: Setup Wizard as Initialization Guard

**What:** On startup, FastAPI checks if initial config (LLM key, Kroger creds, store) exists in SQLite. If not, all routes except `/setup/*` return 302 to the setup wizard UI. The wizard walks through each credential type and validates before saving.

**When:** Every server startup.

**Why:** Prevents partially-configured app from serving broken requests. Forces the BYO-credentials workflow.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Storing Customer Search Data Persistently

**What:** Writing raw shopping list text or Kroger product query terms to SQLite beyond the current session.

**Why bad:** Explicit Kroger TOS violation. "Cannot track/share/store data from customer searches."

**Instead:** Keep raw search terms in memory only during the request-response cycle. Log only confirmed cart items (user-initiated, explicit action). Shopping history stores what was added, not what was searched.

### Anti-Pattern 2: Embedding Kroger Credentials in the Image

**What:** Baking `KROGER_CLIENT_ID` or `KROGER_CLIENT_SECRET` into the Dockerfile, a default config file, or the GitHub repository.

**Why bad:** Explicit Kroger TOS violation. Distributing shared API keys would make every user subject to the app owner's rate limits and could get the developer account banned.

**Instead:** All three credential sets (LLM key, Kroger developer creds, Kroger OAuth) are collected at first-run via the setup wizard and stored in the volume-mounted SQLite. The image ships with no credentials.

### Anti-Pattern 3: LLM Calls on Every Kroger API Response

**What:** Making an LLM call per product search result or per search page, before knowing the full candidate set.

**Why bad:** Wastes LLM tokens. The LLM's value is in ranking and preference-matching across a candidate set, not in evaluating individual items.

**Instead:** Gather all product candidates from Kroger Products API first (all items in the shopping list), then pass the full candidate set to the LLM in one prompt for ranking.

### Anti-Pattern 4: Rebuilding Frontend on Every Container Start

**What:** Running `npm run build` as part of the container entrypoint or startup script.

**Why bad:** Adds 30-60 seconds to startup time. Requires Node.js in the final image, increasing attack surface and image size.

**Instead:** Multi-stage build — frontend compiled at image build time, only static assets in the final image.

### Anti-Pattern 5: Polling Kroger Cart API to Read Cart State

**What:** Calling the Cart API on load to show "what's in the cart" or to validate items.

**Why bad:** Kroger Cart API is add-only. There is no read endpoint. Polling will fail or waste rate limit budget (5,000 calls/day).

**Instead:** Maintain a local cart state table in SQLite that tracks items added during the current session. Clearly communicate to users that this is local tracking, not live cart contents. On session start, offer to clear local state (since cart state on Kroger's end is unknown).

### Anti-Pattern 6: Running a Separate LiteLLM Proxy Container

**What:** Standing up a LiteLLM proxy as a sidecar service in docker-compose for a single-user personal app.

**Why bad:** Doubles container count and operational complexity for no benefit at single-user, low-concurrency scale. LiteLLM proxy's production features (load balancing, 1M+ request log performance) are irrelevant here.

**Instead:** Use the LiteLLM Python SDK directly inside the FastAPI process. One import, same unified interface, no extra infrastructure.

---

## Scalability Considerations

This app is explicitly single-user per container instance (per PROJECT.md). Scalability concerns are therefore minimal, but worth noting for future reference.

| Concern | At 1 user (current) | At N users (future, different containers) | Notes |
|---------|--------------------|-----------------------------------------|-------|
| SQLite concurrency | No issue — single writer | Each container has its own SQLite | Horizontal scaling via separate instances, not shared DB |
| Kroger API rate limits | 10K products/day is ample | Same — each user has their own dev credentials | BYO-credentials model means per-user rate limits |
| LLM latency | ~1-3s per match request | Same — each container independent | No shared LLM gateway needed |
| OAuth token refresh | Single token set, proactive refresh | Same per container | Token manager handles refresh on 401 |
| Docker volume | Single `/data/app.db` | Each container maps its own volume | No shared storage needed |

---

## Suggested Build Order

Components have clear dependencies. Build from the bottom up.

```
Phase 1: Foundation
  1. SQLite schema + SQLModel models (preferences, receipts, sessions, OAuth tokens, config)
  2. Docker container (multi-stage build, volume mount, env config)
  3. FastAPI skeleton with static file serving

Phase 2: Credentials and Auth
  4. Setup wizard backend (credential storage, validation endpoints)
  5. OAuth Token Manager (PKCE flow, token storage, refresh logic)
  6. Kroger API Client (wraps products, cart, locations endpoints)

Phase 3: Core Intelligence
  7. LLM Service (LiteLLM SDK wrapper, structured output)
  8. Preference Service (CRUD + query API for preference profile)
  9. Receipt Parser (pdfplumber + LLM extraction pipeline)

Phase 4: Primary Feature
  10. Cart Service (list → search → rank → review → add pipeline)

Phase 5: UI
  11. React UI (setup wizard, list input, review flow, preference editor, receipt upload)

Phase 6: Polish
  12. Natural language preference updates
  13. Exceptions-only / full review toggle
  14. Shopping history log UI
```

**Why this order:**
- Schema first: every component depends on the DB model being stable.
- OAuth before Cart: can't test Cart Service without valid Kroger tokens.
- LLM Service before Cart Service: Cart Service depends on ranked output from LLM.
- Preference Service before LLM prompt construction: preferences must be loadable before they can be injected into prompts.
- Receipt Parser before full preference profile: solves cold-start so preferences exist before the first shopping run.
- UI last: backend APIs can be tested with curl/Postman during development; building UI against a stable API is far easier than building both simultaneously.

---

## Directory Structure

```
fenncart/
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # Volume mount, port mapping
├── requirements.txt
├── backend/
│   ├── main.py                 # FastAPI app factory, static mount, startup guard
│   ├── config.py               # Settings from env + volume config
│   ├── database.py             # SQLModel engine, session dependency
│   ├── models/                 # SQLModel table definitions
│   │   ├── preferences.py
│   │   ├── receipts.py
│   │   ├── sessions.py
│   │   └── oauth_tokens.py
│   ├── routers/                # FastAPI route handlers (thin)
│   │   ├── setup.py
│   │   ├── auth.py
│   │   ├── cart.py
│   │   ├── preferences.py
│   │   └── receipts.py
│   └── services/               # Business logic + external calls
│       ├── llm_service.py
│       ├── kroger_client.py
│       ├── oauth_manager.py
│       ├── cart_service.py
│       ├── preference_service.py
│       └── receipt_parser.py
└── frontend/                   # React + Vite
    ├── src/
    │   ├── components/
    │   ├── pages/
    │   │   ├── Setup.tsx
    │   │   ├── ShoppingList.tsx
    │   │   ├── ReviewCart.tsx
    │   │   └── Preferences.tsx
    │   └── api/                # API client (fetch wrappers)
    └── vite.config.ts
```

---

## Sources

- FastAPI static files and SPA routing: [FastAPI Discussions #5134](https://github.com/fastapi/fastapi/discussions/5134), [FastAPI Docs: Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- Single-container FastAPI + React patterns: [Medium: FastAPI React single container](https://dakdeniz.medium.com/fastapi-react-dockerize-in-single-container-e546e80b4e4d)
- LiteLLM SDK vs proxy tradeoffs: [LiteLLM Docs](https://docs.litellm.ai/docs/), [Multi-provider LLM orchestration guide](https://dev.to/ash_dubai/multi-provider-llm-orchestration-in-production-a-2026-guide-1g10)
- SQLite in Docker: [How to Run SQLite in Docker](https://oneuptime.com/blog/post/2026-02-08-how-to-run-sqlite-in-docker-when-and-how/view)
- Kroger API OAuth implementation reference: [CupOfOwls kroger-api (GitHub)](https://github.com/CupOfOwls/kroger-api)
- OAuth 2.0 authorization code + PKCE flow: [OAuth 2.0 Simplified](https://www.oauth.com/oauth2-servers/server-side-apps/authorization-code/), [OAuth token storage best practices](https://fusionauth.io/articles/oauth/oauth-token-storage)
- PDF extraction pipeline: [DEV Community: PDF extraction Python 2026](https://dev.to/kreuzberg/how-to-extract-text-from-pdf-in-python-2026-3a97)
- OAuth BFF pattern: [Baeldung: OAuth2 BFF with Spring Cloud Gateway](https://www.baeldung.com/spring-cloud-gateway-bff-oauth2) (concept applies regardless of framework)
