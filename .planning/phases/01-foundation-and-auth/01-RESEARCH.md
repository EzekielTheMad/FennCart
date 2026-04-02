# Phase 1: Foundation and Auth - Research

**Researched:** 2026-04-02
**Domain:** FastAPI + SQLite + Docker + Kroger OAuth PKCE + HTMX Setup Wizard
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Wizard step order: LLM API key validation → Kroger developer credentials validation → Store selection via zip → Kroger OAuth login. Each step validates before allowing the user to proceed (test LLM connection, verify Kroger API keys, confirm store exists).
- **D-02:** Wizard is resumable — progress saved to SQLite so if user closes browser mid-wizard, they resume from last completed step on return.
- **D-03:** After setup completes, show a brief quick tour / tips walkthrough before the main screen (upload receipts, paste lists, how the flow works). Then land on the main app.
- **D-04:** All sensitive API credentials (Kroger client ID/secret, LLM API key) come from environment variables / `.env` file only. Never stored in SQLite. The wizard reads and validates them but does not persist them.
- **D-05:** Non-secret config stored in SQLite: store selection, OAuth tokens (refresh/access), wizard completion state, user preferences.
- **D-06:** OAuth tokens encrypted at rest in SQLite using an app-generated key stored in the Docker volume.
- **D-07:** If credentials are missing at container start, app starts but only serves a "missing config" page that explains which env vars are needed and how to set them. Does not refuse to start entirely.
- **D-08:** Build the full navigation shell in Phase 1 with all nav items (Shopping, Preferences, History, Settings). Non-Phase-1 pages show "Coming soon" placeholders.
- **D-09:** Single container, no compose dependencies. Docker setup must be Unraid Community Apps compatible.
- **D-10:** Design docker-compose.yml and Dockerfile with Unraid conventions in mind: single exposed port, named volume for `/data`, clear env var definitions with descriptions. Unraid CA XML template itself is Phase 5, but container design must not conflict with it.

### Claude's Discretion

- Error UX pattern (inline errors vs toasts vs dedicated pages) — Claude picks the approach that fits the HTMX/Jinja2 SSR pattern best.
- Navigation structure (top bar vs sidebar vs minimal) — Claude picks based on what works for a single-purpose app with 4-5 future pages.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SETUP-01 | User can complete a guided first-run wizard (LLM API key, Kroger developer credentials, Kroger OAuth login, store selection) | FastAPI + HTMX multi-step wizard pattern; Authlib StarletteIntegration for Kroger OAuth; LiteLLM connection test |
| SETUP-02 | User can select their Fry's/Kroger store location via zip code search | Kroger Locations API (1,600 calls/day); HTTPX async client; HTMX partial response for live zip search |
| SETUP-03 | User can authenticate with Kroger via OAuth PKCE flow within the web UI | Authlib AsyncOAuth2Client or StarletteIntegration; PKCE code_verifier in SessionMiddleware; BASE_URL env var for redirect_uri |
| SETUP-04 | App silently refreshes Kroger access tokens using stored refresh token (6-month validity) | OAuth Token Manager with expiry timestamp; proactive refresh at 60s margin; 401 retry logic; Fernet-encrypted tokens in SQLite |

</phase_requirements>

---

## Summary

Phase 1 is a greenfield bootstrapping phase with no existing code. It establishes every foundational system the remaining phases depend on: the FastAPI application skeleton, SQLite schema and Alembic migration pipeline, Docker container with a named volume, a multi-step setup wizard, and a complete Kroger OAuth PKCE authentication flow with encrypted token storage and silent refresh.

The stack is fully locked via CLAUDE.md: Python 3.12-slim Docker base, FastAPI 0.135.3, SQLModel 0.0.37, aiosqlite 0.22.1, Alembic 1.18.4, Authlib 1.6.9, HTTPX 0.28.1, HTMX 1.9.x via CDN, Alpine.js 3.x via CDN, Tailwind CSS 3.x via CDN play build, and the `cryptography` package for Fernet token encryption. The ARCHITECTURE.md and PITFALLS.md from prior research already document the primary patterns and failure modes in detail.

The highest-risk element in this phase is the Kroger OAuth PKCE redirect flow inside Docker. The redirect URI must be built from a configurable `BASE_URL` env var — never from internal container hostnames. The second-highest risk is token security: OAuth tokens must be Fernet-encrypted before writing to SQLite, using an app-generated key that lives on the Docker volume. Both risks are well-understood and preventable with the patterns documented here.

**Primary recommendation:** Build the Docker container and SQLite infrastructure first (Waves 1-2), then the setup wizard backend (Wave 3), then the OAuth flow (Wave 4), then the HTMX frontend (Wave 5). Validate the full OAuth PKCE round-trip inside Docker before marking the phase complete.

---

## Standard Stack

### Core (all versions locked in CLAUDE.md)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12 | Runtime | FastAPI 0.128+ requires 3.12+; avoid 3.13 ecosystem lag |
| FastAPI | 0.135.3 | Web framework | Native async, Pydantic v2, Starlette sessions for OAuth |
| Uvicorn | latest stable | ASGI server | FastAPI canonical server; `--workers 1` for SQLite safety |
| Starlette | (FastAPI dep) | SessionMiddleware | Required to persist OAuth PKCE verifier/state across redirect |
| Pydantic v2 | (FastAPI dep) | Validation + settings | 50x v1 performance; `pydantic-settings` for all config |
| SQLModel | 0.0.37 | ORM | SQLAlchemy 2.0 + Pydantic in one class; less boilerplate for FastAPI |
| aiosqlite | 0.22.1 | Async SQLite driver | Required for `create_async_engine` with SQLite |
| Alembic | 1.18.4 | Schema migrations | Autogenerates from SQLModel metadata; run `upgrade head` at entrypoint |
| HTTPX | 0.28.1 | Kroger API HTTP client | Async-first; used by both Authlib integration and direct Kroger calls |
| Authlib | 1.6.9 | OAuth2 PKCE client | `AsyncOAuth2Client` / Starlette integration; PKCE built-in |
| cryptography | latest stable | Fernet token encryption | Encrypts OAuth tokens before SQLite write (D-06) |
| pydantic-settings | 2.x | Env var config | All app settings: port, LLM key, Kroger creds, BASE_URL |
| python-multipart | latest stable | Form/file parsing | Required by FastAPI for file upload endpoints |
| python-dotenv | latest stable | Local dev .env loading | `pydantic-settings` uses it automatically |
| LiteLLM | 1.83.0 | LLM provider abstraction | Wizard step 1: test LLM API key connection |
| Instructor | 1.14.5 | Structured LLM output | Same dependency as LiteLLM; present from day one |

### Frontend (CDN only in Phase 1 — no build step)

| Library | Version | Purpose |
|---------|---------|---------|
| Jinja2 | (FastAPI dep) | HTML templating — server renders all pages |
| HTMX | 1.9.x CDN | Partial page swaps for multi-step wizard and nav |
| Alpine.js | 3.x CDN | Client-side form state, accordion, toggle visibility |
| Tailwind CSS | 3.x CDN play | Styling — play build for development; CLI binary at Docker build for prod |

**Installation:**
```bash
pip install "fastapi[standard]"==0.135.3 uvicorn[standard]
pip install sqlmodel==0.0.37 aiosqlite==0.22.1 alembic==1.18.4
pip install litellm==1.83.0 instructor==1.14.5
pip install httpx==0.28.1 authlib==1.6.9
pip install cryptography pydantic-settings python-multipart python-dotenv
pip install pytest httpx anyio pytest-anyio  # test dependencies
```

---

## Architecture Patterns

### Recommended Project Structure

```
fenncart/
├── Dockerfile                     # python:3.12-slim, Tailwind CLI build, Alembic upgrade at entrypoint
├── docker-compose.yml             # single service, fenncart_data volume, env_file: .env
├── .env.example                   # placeholder values only — never real credentials
├── requirements.txt
├── alembic.ini                    # sqlite+aiosqlite:///data/fenncart.db
├── alembic/
│   ├── env.py                     # imports SQLModel metadata; run_migrations_online() async-safe
│   └── versions/                  # generated migration files
├── app/
│   ├── main.py                    # FastAPI app factory, SessionMiddleware, StaticFiles, startup guard
│   ├── config.py                  # pydantic-settings Settings class; no credential defaults
│   ├── database.py                # create_async_engine, AsyncSession dependency, WAL init
│   ├── models/
│   │   ├── config_model.py        # AppConfig table (store_id, wizard_step, etc.)
│   │   └── oauth_token.py         # OAuthToken table (encrypted access/refresh, expiry)
│   ├── routers/
│   │   ├── setup.py               # /setup/* wizard step endpoints
│   │   ├── auth.py                # /auth/kroger/start, /auth/kroger/callback
│   │   └── pages.py               # shell pages: /, /shopping, /preferences, /history, /settings
│   └── services/
│       ├── oauth_manager.py       # PKCE generation, token exchange, encrypt/decrypt, refresh
│       ├── kroger_client.py       # Locations API (zip search), async HTTPX wrapper
│       └── llm_service.py         # LiteLLM connection test (wizard step 1 validation only)
├── static/
│   └── output.css                 # generated by Tailwind CLI at Docker build time
└── templates/
    ├── base.html                  # nav shell, HTMX/Alpine/Tailwind CDN script tags
    ├── setup/
    │   ├── wizard.html            # outer wrapper, step indicator
    │   ├── step_llm.html          # LLM key entry + test
    │   ├── step_kroger.html       # Kroger client_id/secret validation
    │   ├── step_store.html        # zip code search, store select
    │   └── step_oauth.html        # Kroger authorize button
    ├── tour.html                  # quick tour after setup completes
    ├── missing_config.html        # shown when required env vars absent
    └── pages/
        ├── shopping.html          # placeholder
        ├── preferences.html       # placeholder
        ├── history.html           # placeholder
        └── settings.html          # placeholder
```

### Pattern 1: Startup Guard (Missing Config vs. Setup vs. App)

**What:** On every request, FastAPI middleware checks three states: (1) required env vars absent — serve `missing_config.html` only; (2) wizard not complete — redirect to `/setup`; (3) wizard complete and OAuth done — serve normal app.

**When to use:** Every route handler is gated by this check. Implement as a Starlette middleware, not per-route.

```python
# app/main.py
from starlette.middleware.base import BaseHTTPMiddleware

class SetupGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exempt: /static, /setup, /auth (OAuth callback must be reachable)
        if request.url.path.startswith(("/static", "/setup", "/auth")):
            return await call_next(request)
        settings = get_settings()
        if not settings.kroger_client_id or not settings.kroger_client_secret:
            return templates.TemplateResponse("missing_config.html", {"request": request})
        # Check wizard completion in DB
        async with get_session() as session:
            cfg = await session.get(AppConfig, 1)
            if not cfg or not cfg.wizard_complete:
                return RedirectResponse("/setup")
        return await call_next(request)
```

**Source:** ARCHITECTURE.md Pattern 5 (Setup Wizard as Initialization Guard); CONTEXT.md D-07.

### Pattern 2: SQLite Initialization with WAL Mode

**What:** On first connection, run two PRAGMAs required for async safety.

**When to use:** Database startup, before any service layer is initialized.

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "sqlite+aiosqlite:////data/fenncart.db"

engine = create_async_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

async def init_db():
    async with engine.begin() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.execute(text("PRAGMA busy_timeout=5000"))
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
```

**Source:** PITFALLS.md Pitfall 8 (SQLite locking); STATE.md Architecture Constraints.

### Pattern 3: Alembic with Async SQLite

**What:** Alembic `env.py` uses an async engine to autogenerate migrations from SQLModel metadata. Migration runs at container entrypoint before Uvicorn starts.

**When to use:** Every schema change across all phases.

```python
# alembic/env.py — key async configuration
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
import app.models  # noqa: import all models to populate metadata

def run_migrations_online():
    connectable = create_async_engine(config.get_main_option("sqlalchemy.url"))
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=SQLModel.metadata)
        with context.begin_transaction():
            context.run_migrations()
```

```ini
# alembic.ini
sqlalchemy.url = sqlite+aiosqlite:////data/fenncart.db
```

```dockerfile
# Dockerfile entrypoint
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
```

**Source:** Alembic + FastAPI migrations (testdriven.io); STACK.md Key Architectural Constraints #3.

### Pattern 4: Kroger OAuth PKCE via Authlib Starlette Integration

**What:** Use Authlib's `StarletteIntegration` (wraps `AsyncOAuth2Client`) which stores PKCE state and code_verifier in the Starlette session cookie automatically.

**When to use:** `/auth/kroger/start` (initiate) and `/auth/kroger/callback` (exchange).

```python
# app/services/oauth_manager.py
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name="kroger",
    client_id=settings.kroger_client_id,
    client_secret=settings.kroger_client_secret,
    authorize_url="https://api.kroger.com/v1/connect/oauth2/authorize",
    access_token_url="https://api.kroger.com/v1/connect/oauth2/token",
    client_kwargs={"scope": "openid profile cart.basic:write"},
    # PKCE is enabled automatically by Authlib when using authorize_redirect
)

# app/routers/auth.py
@router.get("/auth/kroger/start")
async def kroger_auth_start(request: Request):
    redirect_uri = f"{settings.base_url}/auth/kroger/callback"
    return await oauth.kroger.authorize_redirect(request, redirect_uri, code_challenge_method="S256")

@router.get("/auth/kroger/callback")
async def kroger_auth_callback(request: Request, db: AsyncSession = Depends(get_session)):
    token = await oauth.kroger.authorize_access_token(request)
    await oauth_manager.store_token(token, db)  # encrypts before write
    return RedirectResponse("/tour")
```

**Critical:** `SessionMiddleware` must be added with a secret key from env — never hardcoded. The session stores `code_verifier` and `state` automatically across the browser redirect.

```python
# app/main.py
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
```

**Source:** Authlib Starlette client docs; STACK.md Kroger OAuth notes; ARCHITECTURE.md Pattern 4.

### Pattern 5: OAuth Token Encryption with Fernet (D-06)

**What:** Generate a Fernet key at first startup and store it on the Docker volume (`/data/app.key`). Use it to encrypt access and refresh tokens before writing to the `oauth_tokens` table.

**When to use:** Every token write/read in `oauth_manager.py`.

```python
# app/services/oauth_manager.py
from cryptography.fernet import Fernet
from pathlib import Path

KEY_PATH = Path("/data/app.key")

def get_or_create_fernet() -> Fernet:
    if KEY_PATH.exists():
        return Fernet(KEY_PATH.read_bytes())
    key = Fernet.generate_key()
    KEY_PATH.write_bytes(key)
    return Fernet(key)

async def store_token(token: dict, db: AsyncSession):
    f = get_or_create_fernet()
    record = OAuthToken(
        access_token=f.encrypt(token["access_token"].encode()).decode(),
        refresh_token=f.encrypt(token["refresh_token"].encode()).decode(),
        expires_at=datetime.utcnow() + timedelta(seconds=token["expires_in"]),
    )
    db.add(record)
    await db.commit()

async def get_valid_access_token(db: AsyncSession) -> str:
    record = await db.get(OAuthToken, 1)
    f = get_or_create_fernet()
    if record.expires_at - datetime.utcnow() < timedelta(seconds=60):
        # Proactive refresh
        new_token = await _refresh_token(f.decrypt(record.refresh_token.encode()).decode())
        await store_token(new_token, db)
        return new_token["access_token"]
    return f.decrypt(record.access_token.encode()).decode()
```

**Source:** ARCHITECTURE.md Pattern 4; Fernet docs (cryptography.io); CONTEXT.md D-06.

### Pattern 6: HTMX Multi-Step Wizard

**What:** Each wizard step is a separate Jinja2 partial. HTMX replaces `#wizard-step` with the next partial after the current step validates. Progress is saved to SQLite (D-02) before each swap.

**When to use:** All four wizard steps.

```html
<!-- templates/setup/step_llm.html (partial) -->
<div id="wizard-step">
  <form hx-post="/setup/validate-llm"
        hx-target="#wizard-step"
        hx-swap="outerHTML"
        hx-indicator="#spinner">
    <label>LLM API Key</label>
    <input name="llm_api_key" type="password" required />
    <button type="submit">Test Connection</button>
    <span id="spinner" class="htmx-indicator">Testing...</span>
  </form>
</div>
```

```python
# app/routers/setup.py
@router.post("/setup/validate-llm")
async def validate_llm(request: Request, db: AsyncSession = Depends(get_session)):
    form = await request.form()
    ok = await llm_service.test_connection(form["llm_api_key"])
    if not ok:
        # Return same partial with error message (inline error, no redirect)
        return templates.TemplateResponse("setup/step_llm.html",
            {"request": request, "error": "Could not connect. Check your API key."})
    await save_wizard_step(db, step="llm_validated")
    return templates.TemplateResponse("setup/step_kroger.html", {"request": request})
```

**Error UX decision:** Inline errors within the step partial (no toasts, no page redirects). HTMX swaps the same partial back with an error message. This is the natural pattern for HTMX SSR — no JavaScript needed.

**Source:** HTMX docs (hx-target, hx-swap, hx-indicator); CONTEXT.md D-01, D-02.

### Pattern 7: Settings from Environment (No Credential Defaults)

**What:** `pydantic-settings` `BaseSettings` class reads all config from env vars. Credential fields have no default — app fails validation at startup if absent.

**When to use:** All config. Never hardcode or provide defaults for credential values.

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Required credentials — no defaults (raises ValidationError if absent)
    kroger_client_id: str
    kroger_client_secret: str
    # Optional with reasonable defaults
    llm_api_key: str = ""
    llm_provider: str = "anthropic"
    base_url: str = "http://localhost:8000"
    session_secret_key: str = "change-me-in-production"
    port: int = 8000

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Note:** Per D-07, the app does NOT crash if `kroger_client_id` is absent. Instead, the startup guard middleware detects the missing value and serves `missing_config.html`. This means the `Settings` class should use `str = ""` defaults for credential fields, with the guard middleware validating presence before serving app routes.

**Source:** PITFALLS.md Pitfall 1; CONTEXT.md D-04, D-07; STATE.md Architecture Constraints.

### Pattern 8: Docker Compose for Unraid Compatibility (D-09, D-10)

**What:** Single service, single exposed port, named volume at `/data`, all secrets via env vars.

```yaml
# docker-compose.yml
services:
  fenncart:
    image: fenncart:latest
    build: .
    ports:
      - "${PORT:-8000}:8000"
    volumes:
      - fenncart_data:/data
    env_file:
      - .env
    restart: unless-stopped

volumes:
  fenncart_data:
    name: fenncart_data
```

**Unraid-compatible constraints (D-10):**
- Single service (no compose dependencies)
- Single exposed port
- Named volume (`fenncart_data`) — Unraid maps this to `/mnt/user/appdata/fenncart/`
- All secrets in env vars (never baked into image)
- `restart: unless-stopped` — Unraid manages lifecycle via Docker daemon

**Source:** CONTEXT.md D-09, D-10; PITFALLS.md Pitfall 9 (Docker volume data loss); Selfhosters.net Unraid template guide.

### Anti-Patterns to Avoid

- **Hardcoding redirect URI:** Always build from `settings.base_url + "/auth/kroger/callback"`. Never use `request.base_url` or container hostname. (Pitfall 2)
- **Storing credentials in SQLite:** Kroger client_id/secret and LLM API key live in env vars only. Wizard reads from `get_settings()` for validation but never writes them to DB. (D-04)
- **Default values for credential env vars:** Providing `kroger_client_id: str = "your_id_here"` in Settings is just as dangerous as a hardcoded value — it can be committed. Use empty-string defaults with guard middleware validation. (Pitfall 1)
- **SQLite without WAL mode:** `aiosqlite` + FastAPI async = concurrent access possible. WAL + busy_timeout is non-negotiable. (Pitfall 8)
- **Storing Fernet key in env vars or code:** Key lives at `/data/app.key` (Docker volume) — generated at first startup, persists across restarts. (D-06)
- **Logging credentials at DEBUG level:** Redacting log formatter must be in place before any credential handling code. (Pitfall 14)

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth PKCE flow | Custom PKCE verifier/challenge logic | Authlib Starlette integration | Authlib generates code_verifier, code_challenge (S256), state, stores them in session automatically |
| Token refresh | Manual expiry check + re-auth prompt | `get_valid_access_token()` with proactive 60s margin + 401 retry | Token expiry mid-session is the known failure mode (Pitfall 10) |
| Field-level SQLite encryption | SQLCipher or custom XOR | `cryptography` Fernet | Fernet is AES-128-CBC + HMAC-SHA256; MIT licensed; one import |
| Env var config | Manual `os.getenv()` with defaults | `pydantic-settings` `BaseSettings` | Type coercion, validation, `.env` support, auto-documentation of settings |
| Multi-step form state | Cookie-based custom step tracking | SQLite `AppConfig.wizard_step` column | Resumable across browser closes (D-02); single source of truth |
| Schema migrations | Manual `CREATE TABLE IF NOT EXISTS` | Alembic + `alembic upgrade head` in entrypoint | Schema evolution across Docker updates without data loss |

**Key insight:** Kroger OAuth is the most brittle part of this phase. Every non-trivial part of the OAuth flow has an existing solution in Authlib. The redirect URI, PKCE verifier storage, token exchange, and session handling are all handled — do not reimplement any of them.

---

## Common Pitfalls

### Pitfall 1: OAuth Redirect URI Mismatch in Docker

**What goes wrong:** App generates callback URL from `request.base_url` or internal container hostname (`fenncart:8000`). Browser gets redirected to a URI that doesn't match the registered Kroger developer app redirect URI. Kroger rejects with `invalid_redirect_uri`.

**Why it happens:** Docker networking separates internal hostnames from external `localhost` address.

**How to avoid:** Always build redirect URI from `settings.base_url` (configurable env var, defaults to `http://localhost:8000`). Display the exact redirect URI in the setup wizard step 2 so the user can copy it to their Kroger developer app registration.

**Warning signs:** OAuth callback URL contains `fenncart`, `172.`, or any hostname other than what users see in their browser.

### Pitfall 2: Fernet Key Lost on Container Rebuild

**What goes wrong:** Fernet key generated at `/data/app.key` is not on the Docker volume — it's inside the container filesystem layer. Container rebuild wipes it. All stored OAuth tokens become unreadable.

**How to avoid:** Key path must be `/data/app.key` where `/data` is the named volume mount point. Test by running `docker compose down && docker compose up --build` and verifying the app still reads stored tokens correctly.

### Pitfall 3: Wizard Accessible After OAuth Redirect (CSRF)

**What goes wrong:** OAuth callback endpoint at `/auth/kroger/callback` is reachable even when wizard guard is active. If the guard middleware redirects `/auth/*` paths to `/setup`, the callback never executes and Kroger's auth code expires.

**How to avoid:** The guard middleware must exempt `/static`, `/setup`, and `/auth` paths. This is a correctness requirement, not just a convenience.

### Pitfall 4: Alembic env.py Sync/Async Mismatch

**What goes wrong:** Alembic's default `env.py` uses synchronous SQLAlchemy. With `sqlite+aiosqlite://`, the sync engine fails to run migrations.

**How to avoid:** Use `run_sync` within Alembic env.py for aiosqlite. The `run_migrations_online()` function must use `asyncio.run()` and an async engine. Reference implementation: testdriven.io fastapi-sqlmodel tutorial.

### Pitfall 5: Credentials Leaked to Logs

**What goes wrong:** During wizard validation (LLM key test, Kroger API test), the credentials pass through FastAPI request objects and service calls. At DEBUG log level, these appear in stdout/container logs.

**How to avoid:** Add a custom `logging.Filter` that redacts any value for keys matching `*key*`, `*secret*`, `*token*`, `*password*` before the first wizard endpoint is wired.

---

## Code Examples

### LLM Connection Test (Wizard Step 1)

```python
# app/services/llm_service.py
import litellm

async def test_connection(api_key: str, provider: str = "anthropic") -> bool:
    """Verify LLM API key works. Returns True on success."""
    try:
        response = await litellm.acompletion(
            model=f"{provider}/claude-3-haiku-20240307",
            messages=[{"role": "user", "content": "ping"}],
            api_key=api_key,
            max_tokens=5,
        )
        return bool(response.choices)
    except Exception:
        return False
```

### Kroger Locations Search (Wizard Step 3 / SETUP-02)

```python
# app/services/kroger_client.py
import httpx

KROGER_BASE = "https://api.kroger.com/v1"

async def get_app_token(client_id: str, client_secret: str) -> str:
    """Client credentials grant for public API access (no user account needed)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{KROGER_BASE}/connect/oauth2/token",
            data={"grant_type": "client_credentials", "scope": "product.compact"},
            auth=(client_id, client_secret),
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

async def search_stores_by_zip(zip_code: str, app_token: str) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{KROGER_BASE}/locations",
            params={"filter.zipCode.near": zip_code, "filter.limit": 10},
            headers={"Authorization": f"Bearer {app_token}"},
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
```

### SQLModel Schema for Phase 1

```python
# app/models/config_model.py
from sqlmodel import SQLModel, Field
from typing import Optional

class AppConfig(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    wizard_step: str = Field(default="start")  # start|llm|kroger|store|oauth|complete
    wizard_complete: bool = Field(default=False)
    store_id: Optional[str] = None
    store_name: Optional[str] = None
    store_zip: Optional[str] = None
    llm_provider: str = Field(default="anthropic")
    llm_model: str = Field(default="claude-3-haiku-20240307")

# app/models/oauth_token.py
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class OAuthToken(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    access_token_encrypted: str      # Fernet-encrypted, base64
    refresh_token_encrypted: str     # Fernet-encrypted, base64
    expires_at: datetime
    scope: Optional[str] = None
    token_type: str = Field(default="Bearer")
```

### Dockerfile (Phase 1 skeleton)

```dockerfile
FROM python:3.12-slim AS app

# Install Tailwind CLI standalone binary (no Node.js)
ADD https://github.com/tailwindlabs/tailwindcss/releases/download/v3.4.17/tailwindcss-linux-x64 /usr/local/bin/tailwindcss
RUN chmod +x /usr/local/bin/tailwindcss

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./

# Generate purged CSS at build time
RUN tailwindcss -i ./static/input.css -o ./static/output.css --minify

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `sqlite3` + blocking I/O in async | `aiosqlite` + `create_async_engine` | SQLAlchemy 2.0 (2023) | Event loop no longer blocks on DB writes |
| Flask + Requests for OAuth | FastAPI + Authlib + HTTPX | 2022-2023 | Native async throughout; PKCE built-in |
| React SPA + build pipeline in Docker | HTMX + Jinja2 SSR | 2023-2024 | Eliminates Node.js from Docker image; 14KB CDN script vs 500KB+ bundle |
| pydantic v1 `BaseSettings` | pydantic-settings (separate package, v2) | Pydantic 2.0 (2023) | Import is `from pydantic_settings import BaseSettings` not `from pydantic import BaseSettings` |
| `alembic revision --autogenerate` requires sync engine | Use `run_sync` in async Alembic env.py | SQLAlchemy 2.0 | Minor config change; see testdriven.io guide |

**Deprecated/outdated:**
- `from pydantic import BaseSettings`: Removed in pydantic v2 — use `pydantic-settings` package
- Authlib `OAuth1Session` / sync client: Use `AsyncOAuth2Client` or Starlette integration
- HTMX 2.x: Not yet mainstream; 1.9.x is the stable CDN target for 2026

---

## Open Questions

1. **Kroger redirect URI for localhost vs. custom domain**
   - What we know: Kroger's developer portal accepts `http://localhost:PORT/callback` for self-hosted apps (per FennCartPitch.md and common OAuth practice for native apps)
   - What's unclear: Whether Kroger enforces exact port matching (e.g., `http://localhost:8000` but not `http://localhost:8001`) or allows wildcard port
   - Recommendation: Register `http://localhost:8000/auth/kroger/callback` as the canonical redirect URI in the setup wizard instructions. Document that users must update their Kroger developer app registration if they change the default port.

2. **Authlib Starlette integration PKCE behavior**
   - What we know: Authlib's `StarletteIntegration` uses `SessionMiddleware` to store state/verifier. `code_challenge_method="S256"` enables PKCE.
   - What's unclear: Whether `authorize_redirect` auto-passes the PKCE challenge to Kroger's authorization URL, or whether manual `code_challenge` parameter injection is required.
   - Recommendation: Test the Authlib Starlette flow against Kroger's sandbox in Wave 4. If auto-injection fails, fall back to `AsyncOAuth2Client` with manual PKCE construction.

3. **Tailwind standalone CLI version for Linux**
   - What we know: Tailwind v3.x has a standalone CLI binary for Linux x64 (no Node.js required)
   - What's unclear: Exact GitHub release URL and whether `tailwindcss-linux-x64` binary is available for `linux/arm64` (Raspberry Pi / some Unraid servers)
   - Recommendation: Use `linux/arm64` binary URL as a `--platform` conditional in Dockerfile, or fall back to CDN in production (acceptable for v1).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Partial | 3.11.9 (host) | Dev: use 3.11 locally; Docker: 3.12-slim image is the target |
| Docker | Container build/run | Not found in shell | — | Must install Docker Desktop for Windows; required for phase completion |
| Docker Compose | Service orchestration | Not found in shell | — | Installed with Docker Desktop; no separate fallback |
| pip | Package install | Available | 25.3 | — |
| git | Version control | Available | 2.51.1 | — |

**Note on Python version mismatch:** Host has Python 3.11.9; the stack specifies 3.12. For local development outside Docker this is acceptable — FastAPI 0.135.3 works on 3.11. However, the Dockerfile must use `python:3.12-slim`. Run all integration tests inside the Docker container, not on the host Python.

**Missing dependencies with no fallback:**
- Docker / Docker Desktop for Windows — required to build/run the container. Phase cannot be completed without it.

**Missing dependencies with fallback:**
- Python 3.12 on host — use Docker container as the runtime; develop against 3.11 locally for basic syntax/import checking only.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + anyio (async support) + httpx (FastAPI TestClient) |
| Config file | `pytest.ini` — Wave 0 |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SETUP-01 | Wizard steps render and validate in sequence | integration | `pytest tests/test_wizard.py -x` | Wave 0 |
| SETUP-01 | Wizard progress saves to SQLite (resumable) | unit | `pytest tests/test_wizard.py::test_wizard_resumable -x` | Wave 0 |
| SETUP-02 | Kroger Locations API returns stores for valid zip | integration | `pytest tests/test_kroger_client.py::test_store_search -x` | Wave 0 |
| SETUP-03 | OAuth start endpoint builds correct authorization URL with PKCE | unit | `pytest tests/test_oauth.py::test_auth_url_has_pkce -x` | Wave 0 |
| SETUP-03 | OAuth callback exchanges code for tokens and stores encrypted | unit | `pytest tests/test_oauth.py::test_callback_stores_encrypted -x` | Wave 0 |
| SETUP-04 | Token refresh triggered when access token within 60s of expiry | unit | `pytest tests/test_oauth.py::test_proactive_refresh -x` | Wave 0 |
| SETUP-04 | 401 from Kroger API triggers one refresh + retry | unit | `pytest tests/test_oauth.py::test_401_retry -x` | Wave 0 |

**Manual-only items:**
- Full Kroger OAuth round-trip in Docker (real browser redirect) — automated in unit tests via mocks; must be validated manually in Docker once before phase sign-off.

### Sampling Rate
- **Per task commit:** `pytest tests/unit/ -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/__init__.py`
- [ ] `tests/unit/__init__.py`
- [ ] `tests/conftest.py` — shared `TestClient`, in-memory SQLite session fixture
- [ ] `tests/test_wizard.py` — covers SETUP-01
- [ ] `tests/test_kroger_client.py` — covers SETUP-02 (mocked HTTPX)
- [ ] `tests/test_oauth.py` — covers SETUP-03, SETUP-04
- [ ] `pytest.ini` — anyio mode, test paths
- [ ] Framework install: `pip install pytest pytest-anyio httpx`

---

## Project Constraints (from CLAUDE.md)

The following directives from `CLAUDE.md` apply to this phase and constrain all planning and implementation decisions:

| Constraint | Requirement |
|------------|-------------|
| TOS: BYO credentials | Each user must bring their own Kroger developer credentials — cannot distribute with shared keys |
| TOS: No persistent customer search data | Raw shopping list queries must not be written to SQLite |
| TOS: Cart API is add-only | Local cart shadow in SQLite required (Phase 2, but schema should anticipate it) |
| Auth: OAuth requires browser redirect | Must work within Docker/web UI; Authlib Starlette integration is the solution |
| Data: Preference profiles from user-uploaded receipts are fine to persist | Schema must distinguish TOS-restricted tables from user-derived tables |
| Stack: Python 3.12 | Dockerfile uses `python:3.12-slim`; do not use 3.13 |
| Stack: FastAPI 0.135.3 exact | Pin in requirements.txt |
| Stack: Uvicorn `--workers 1` | SQLite cannot handle concurrent writers |
| Stack: HTMX + Jinja2 SSR | No Node.js in Docker image; no React/Vue |
| Stack: Tailwind standalone CLI in Docker | No Node.js; CDN play build acceptable for development only |
| Stack: SQLModel + aiosqlite + Alembic | All three required together for async SQLite with migrations |
| Stack: LiteLLM SDK (not proxy) | Do not spin up LiteLLM proxy as a sidecar |
| Stack: Authlib for OAuth | Do not hand-roll PKCE |
| Docker: `python:3.12-slim` base image | Not Alpine (musl libc issues with cryptography wheels) |
| Docker: Named volume `fenncart_data:/data` | SQLite at `/data/fenncart.db`; Fernet key at `/data/app.key` |
| Docker: No credentials in image | All secrets via env vars at runtime |
| Security: No credential defaults | `KROGER_CLIENT_ID`, `KROGER_CLIENT_SECRET` must have no default value |
| GSD Workflow: Work through GSD commands | Use `/gsd:execute-phase` for this phase; no direct edits outside GSD |

---

## Sources

### Primary (HIGH confidence)
- CLAUDE.md — project stack constraints, all versions verified PyPI 2026-04-02
- `.planning/research/STACK.md` — full stack with verified versions
- `.planning/research/ARCHITECTURE.md` — component boundaries, OAuth flow, directory structure
- `.planning/research/PITFALLS.md` — 14 pitfalls specific to this domain
- `.planning/phases/01-foundation-and-auth/01-CONTEXT.md` — locked decisions D-01 through D-10
- Kroger API rate limits and auth details — `FennCartPitch.md`

### Secondary (MEDIUM confidence)
- [Authlib OAuth2 Session docs](https://docs.authlib.org/en/latest/client/oauth2.html) — PKCE and AsyncOAuth2Client patterns
- [FastAPI + SQLModel + Alembic (testdriven.io)](https://testdriven.io/blog/fastapi-sqlmodel/) — async Alembic configuration
- [Fernet docs (cryptography.io)](https://cryptography.io/en/latest/fernet/) — key generation and encryption API
- [Selfhosters.net Unraid template guide](https://selfhosters.net/docker/templating/templating/) — XML schema for CA templates
- [Kroger Authorization Endpoints](https://developer.kroger.com/api-products/api/authorization-endpoints-partner) — OAuth endpoint URLs

### Tertiary (LOW confidence)
- WebSearch results for HTMX multi-step wizard patterns — confirmed against HTMX docs conceptually but no single authoritative tutorial verified
- Authlib Starlette auto-PKCE behavior — unverified; flagged as Open Question 2

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions locked in CLAUDE.md, verified PyPI 2026-04-02
- Architecture patterns: HIGH — drawn directly from project's own ARCHITECTURE.md and PITFALLS.md
- OAuth PKCE specifics: MEDIUM — Authlib Starlette PKCE auto-injection behavior not independently verified; flagged
- Unraid CA template format: MEDIUM — verified from selfhosters.net; XML schema itself is Phase 5 deliverable
- Pitfalls: HIGH — drawn from project's own PITFALLS.md, cross-referenced with official docs

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stack is stable; Kroger API OAuth behavior could change with portal updates)
