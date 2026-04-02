# Technology Stack

**Project:** FennCart
**Researched:** 2026-04-02
**Overall Confidence:** HIGH (all versions verified against PyPI as of research date)

---

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12 | Runtime | FastAPI 0.128+ dropped 3.9 support; 3.12 is the current stable with best performance. Avoid 3.13 — ecosystem lag on new releases. |
| FastAPI | 0.135.3 | Web framework + API | Native async, Pydantic v2 integration, first-class support for OAuth redirect flows via Starlette, and the de facto Python web framework for this type of app in 2025-2026. |
| Uvicorn | latest stable | ASGI server | FastAPI's recommended server; run with `--workers 1` for SQLite safety. |
| Starlette | (FastAPI dependency) | HTTP primitives, sessions | Provides session middleware needed for OAuth state/PKCE parameters across redirect round-trips. |
| Pydantic v2 | (FastAPI dependency) | Validation and settings | 50x faster than v1. Used for config/settings via `pydantic-settings`, request/response models, and LLM structured output schemas. |

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | stdlib (Python 3.12) | Persistence | Zero ops, single file on a Docker volume — exactly right for a single-user self-hosted app. No separate service. |
| SQLModel | 0.0.37 | ORM | Combines SQLAlchemy + Pydantic into one class hierarchy. Less boilerplate than raw SQLAlchemy. Since it wraps SQLAlchemy 2.0, you can drop to raw SQL when needed. Ideal for FastAPI projects. |
| aiosqlite | 0.22.1 | Async SQLite driver | Required for async SQLAlchemy with SQLite. Well-maintained (production-stable), single shared thread per connection. |
| Alembic | 1.18.4 | Schema migrations | Even for a single-user SQLite app, schema migrations are essential as the preference profile evolves across versions. Alembic autogenerates from SQLModel metadata. |

### Frontend (Server-Side Rendering)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Jinja2 | (FastAPI dependency) | HTML templating | FastAPI's built-in template system via Starlette. Server renders HTML — no separate frontend build step. Critical for a self-hosted Docker app where users shouldn't need Node.js. |
| HTMX | 1.9.x (CDN) | Dynamic interactions | 14KB CDN script enables partial page updates (shopping list review flow, live product matching results) without a JavaScript framework. Perfect for server-driven UIs. Load via CDN to keep Docker image lean. |
| Alpine.js | 3.x (CDN) | Client-side state | Lightweight (15KB) JavaScript reactivity for the bits HTMX can't handle: toggling review table visibility, accordion UI, form state. Pairs naturally with HTMX. |
| Tailwind CSS | 3.x (CDN play build) | Styling | Use the CDN play build for development. For production Docker image, use the standalone Tailwind CLI binary (no Node.js needed) to generate a purged CSS file at build time. |

**Rationale for SSR over React/Vue:** This app has no need for complex client-side state management. The review flow, preference editor, and cart confirmation are all form-based flows that SSR + HTMX handles cleanly. React/Vue add a build pipeline, Node.js dependency, and complexity that provides no benefit for a single-user self-hosted app.

### LLM Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| LiteLLM | 1.83.0 | Multi-provider LLM abstraction | Single unified API for Claude (Anthropic), OpenAI, and local models via Ollama. User switches provider via config; code doesn't change. Active development with 12-hour load-test-verified stable Docker tags. |
| Instructor | 1.14.5 | Structured LLM outputs | Wraps LiteLLM calls to return validated Pydantic models. Essential for product matching (returns typed `ProductMatch` objects, not raw text). Integrates directly with LiteLLM. |

**Why LiteLLM over raw SDK calls:** The PROJECT.md specifies multi-provider support as a requirement. Implementing provider-specific clients (Anthropic SDK, OpenAI SDK, Ollama client) and keeping them in sync is ongoing maintenance. LiteLLM collapses this into one interface. Use the Python SDK, not the proxy server — the proxy adds operational complexity that's unnecessary for a single-container app.

**Why Instructor over raw JSON parsing:** Receipt parsing and product matching require structured, validated outputs. Instructor handles retry-on-validation-failure and returns typed Pydantic objects, eliminating fragile `json.loads()` + manual validation.

### External API Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| HTTPX | 0.28.1 | Async HTTP client for Kroger API | Async-first, built-in connection pooling, type-safe. Starlette's background task context works naturally with async HTTPX. |
| Authlib | 1.6.9 | Kroger OAuth2 + PKCE implementation | Provides `AsyncOAuth2Client` with automatic PKCE support, token refresh handling, and code_verifier management. This is exactly the flow Kroger requires (authorization code + PKCE). Far safer than rolling OAuth by hand. |

**Kroger OAuth notes:** The Kroger API uses authorization code flow with PKCE for user accounts and client credentials for product/location lookups. Authlib's `AsyncOAuth2Client` handles both flows. OAuth state and PKCE verifier need to survive the browser redirect — store them in server-side session (Starlette's SessionMiddleware with a signed cookie). Token storage: encrypted in SQLite, not in the session cookie.

### PDF Parsing

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pdfplumber | 0.11.9 | Grocery receipt PDF parsing | Superior table extraction — Kroger/Fry's receipts are structured tabular data (item, quantity, price). pdfplumber excels at coordinate-based layout extraction. Better than pypdf for table-heavy documents. Pure Python, no system dependencies to manage in Docker. |

**Why not pymupdf4llm:** MuPDF has a more complex licensing situation (AGPL unless commercial). For an open source project, pdfplumber (MIT via pdfminer.six) avoids license complications.

**Fallback strategy:** pdfplumber works on machine-generated PDFs (Kroger email receipts). For scanned receipts, it degrades gracefully. Use an LLM to parse the extracted text into structured line items — this is more robust than pure rule-based extraction and the LLM is already in the stack.

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.x | Config from env vars / `.env` file | All app config: LLM keys, Kroger credentials, store location, port. Never hardcode. |
| python-multipart | latest stable | File upload parsing | Required by FastAPI for PDF upload endpoint. Starlette dependency. |
| passlib + bcrypt | latest stable | Credential hashing | If a future UI password is added. Not needed for v1 (single-user, no auth layer required). |
| pytest + httpx | latest stable | Testing | FastAPI's `TestClient` uses HTTPX under the hood. Async test support with `anyio`. |
| python-dotenv | latest stable | Local dev `.env` loading | Development convenience; pydantic-settings uses it in production. |

---

## Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Docker | 20.10+ | Container distribution | PROJECT.md requirement. Single `docker run` for self-hosters. |
| Docker Compose | v2 | Local dev + volume management | Defines the SQLite volume mount declaratively. Users edit a single `docker-compose.yml` to configure credentials. |
| python:3.12-slim | (Docker base) | Base image | Slim avoids Alpine's musl libc issues with compiled Python wheels (cryptography, pdfplumber deps). Significantly smaller attack surface than `python:3.12-full`. |

**Docker constraints for this project:**
- `replicas: 1` always — SQLite cannot handle concurrent writers from multiple app instances.
- Volume mount pattern: `docker run -v fenncart_data:/app/data` — SQLite file lives at `/app/data/fenncart.db`.
- Kroger OAuth redirect URI must match the container's exposed URL. Document clearly in setup instructions.
- Do NOT bake credentials into the image. All secrets come in via environment variables at runtime.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Web framework | FastAPI | Django | Django's ORM and admin are overkill; sync-by-default adds friction for async API calls to Kroger/LLM. FastAPI is naturally async. |
| Web framework | FastAPI | Flask | Flask lacks native async, Pydantic integration, and auto-generated OpenAPI. FastAPI is strictly better for this use case. |
| Frontend | HTMX + Jinja2 | React/Vue SPA | Adds Node.js build pipeline, increases Docker image complexity, no benefit for a single-user local app. |
| ORM | SQLModel | Raw SQLAlchemy | SQLModel's ergonomics are better for a medium-complexity schema. Raw SQLAlchemy available as escape hatch via SQLModel's internals. |
| ORM | SQLModel | Tortoise ORM | SQLModel's SQLAlchemy base is more mature; larger ecosystem; Alembic migration support is first-class. |
| Database | SQLite | PostgreSQL | PROJECT.md explicitly chose SQLite for single-container simplicity. PostgreSQL adds an unnecessary second service for a single-user app. |
| LLM | LiteLLM | Per-provider SDKs | Multi-provider is a stated requirement. Maintaining 3+ provider clients is ongoing work with no upside. |
| LLM structured output | Instructor | Manual JSON parsing | Instructor handles retry-on-failure, Pydantic validation, and provider normalization. Manual parsing is fragile. |
| PDF parsing | pdfplumber | pymupdf4llm | MuPDF is AGPL; pdfplumber is MIT. For an open source project this matters. pdfplumber handles tabular receipts well. |
| OAuth | Authlib | httpx-oauth | Authlib is more mature (1.6.9 vs httpx-oauth's smaller community), supports both client credentials and authorization code flows needed here. |
| CSS | Tailwind CSS | Bootstrap | Tailwind's utility classes are better for custom component design. Bootstrap's opinionated component styles conflict with building a branded UI. |

---

## Installation

```bash
# Core framework
pip install "fastapi[standard]"==0.135.3 uvicorn[standard]

# Database
pip install sqlmodel==0.0.37 aiosqlite==0.22.1 alembic==1.18.4

# LLM
pip install litellm==1.83.0 instructor==1.14.5

# External APIs
pip install httpx==0.28.1 authlib==1.6.9

# PDF parsing
pip install pdfplumber==0.11.9

# Config and utilities
pip install pydantic-settings python-multipart python-dotenv
```

**Note on LiteLLM size:** LiteLLM's full install pulls in many optional provider SDKs. In `requirements.txt`, pin `litellm` and test Docker image size — you may want `litellm[anthropic,openai]` with only the needed extras to keep the image lean.

---

## Confidence Assessment

| Component | Confidence | Basis |
|-----------|------------|-------|
| FastAPI 0.135.3 | HIGH | Verified on PyPI 2026-04-02 |
| SQLModel 0.0.37 | HIGH | Verified on PyPI 2026-04-02 |
| aiosqlite 0.22.1 | HIGH | Verified on PyPI 2026-04-02 |
| Alembic 1.18.4 | HIGH | Verified on PyPI 2026-04-02 |
| LiteLLM 1.83.0 | HIGH | Verified on PyPI 2026-04-02 |
| Instructor 1.14.5 | MEDIUM | Version from WebSearch (Jan 2026), not directly verified on PyPI |
| httpx 0.28.1 | HIGH | Verified on PyPI; 1.0.dev3 pre-release exists, do not use |
| Authlib 1.6.9 | HIGH | Verified on PyPI 2026-04-02 |
| pdfplumber 0.11.9 | HIGH | Verified on PyPI 2026-04-02 |
| HTMX + Alpine.js + Tailwind CDN | MEDIUM | Widely-documented pattern; CDN versions do not need pinning in requirements.txt |
| Jinja2 | HIGH | FastAPI standard dependency, widely documented |
| python:3.12-slim Docker base | HIGH | Official Docker Hub recommendation, verified Feb 2026 article |
| Kroger OAuth PKCE flow | MEDIUM | Authlib PKCE support verified; Kroger-specific PKCE requirement from developer docs reference (JS-rendered page, full content not verifiable) |

---

## Key Architectural Constraints from Stack Choices

1. **Single-worker Uvicorn** — SQLite write contention if multiple workers. `--workers 1` always.
2. **Session middleware required** — OAuth PKCE verifier and state survive the redirect. Starlette `SessionMiddleware` with a secret key (set via env var, not hardcoded).
3. **Alembic on container start** — Run `alembic upgrade head` in the container entrypoint before `uvicorn` starts. Handles schema migrations across app version upgrades without manual user intervention.
4. **LiteLLM SDK, not proxy** — Do not deploy the LiteLLM proxy service. Use `litellm.completion()` directly in application code. The proxy adds operational overhead that's unnecessary for a single-container app.
5. **Tailwind standalone CLI in Docker** — For production, use the Tailwind standalone CLI binary (no Node.js) to generate `output.css` at image build time. CDN is fine for development.
6. **No persistent customer search data** — Kroger TOS requires deleting search data on session end. Shopping list submissions (transient) must not be stored. Preference profiles (derived from user-uploaded receipts) are fine to persist.

---

## Sources

- FastAPI version: [fastapi · PyPI](https://pypi.org/project/fastapi/)
- FastAPI release notes: [Release Notes - FastAPI](https://fastapi.tiangolo.com/release-notes/)
- FastAPI Docker best practices: [FastAPI Docker Best Practices | Better Stack](https://betterstack.com/community/guides/scaling-python/fastapi-docker-best-practices/)
- SQLModel: [sqlmodel · PyPI](https://pypi.org/project/sqlmodel/) | [SQLModel docs](https://sqlmodel.tiangolo.com/)
- SQLModel vs SQLAlchemy comparison: [Is SQLModel Still Worth It in 2025?](https://python.plainenglish.io/sqlmodel-in-2025-the-hidden-gem-of-fastapi-backends-20ee8c9bf8a6)
- aiosqlite: [aiosqlite · PyPI](https://pypi.org/project/aiosqlite/)
- Alembic: [alembic · PyPI](https://pypi.org/project/alembic/) | [Alembic + FastAPI migrations](https://testdriven.io/blog/fastapi-sqlmodel/)
- LiteLLM: [litellm · PyPI](https://pypi.org/project/litellm/) | [LiteLLM GitHub](https://github.com/BerriAI/litellm)
- Instructor: [instructor · PyPI](https://pypi.org/project/instructor/) | [LiteLLM integration](https://python.useinstructor.com/integrations/litellm/)
- HTTPX: [httpx · PyPI](https://pypi.org/project/httpx/)
- Authlib: [authlib · PyPI](https://pypi.org/project/authlib/) | [Authlib OAuth2 client](https://docs.authlib.org/en/latest/client/oauth2.html)
- pdfplumber: [pdfplumber · PyPI](https://pypi.org/project/pdfplumber/) | [pdfplumber GitHub](https://github.com/jsvine/pdfplumber)
- PDF parser comparison: [I Tested 7 Python PDF Extractors (2025)](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257)
- HTMX for Python backends: [HTMX vs React, Vue, Angular: Frontend Development in 2025](https://redskydigital.com/au/htmx-vs-react-vue-angular-frontend-development-in-2025/)
- FastAPI + HTMX + Tailwind: [Full-stack FastAPI with HTMX and Tailwind | TestDriven.io](https://testdriven.io/courses/fastapi-htmx/)
- Docker Python base image: [The best Docker base image for your Python application (February 2026)](https://pythonspeed.com/articles/base-image-python-docker-images/)
- Kroger API OAuth: [Understanding OAuth2 | Kroger Developers](https://developer.kroger.com/documentation/partner/guides/guides-oauth)
- Kroger API Python reference: [kroger-api · PyPI](https://pypi.org/project/kroger-api/) (reference, not a dependency)
