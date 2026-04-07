# Phase 4: Multi-Provider LLM and Settings - Research

**Researched:** 2026-04-04
**Domain:** FastAPI settings management, LLM provider hot-swap, HTMX settings UI with sidebar navigation
**Confidence:** HIGH

## Summary

Phase 4 extends the existing FennCart settings infrastructure into a full settings hub. The foundation is already solid: `AppConfig` stores `llm_provider` and `llm_model` in SQLite, `Settings` (pydantic-settings) reads env vars with `lru_cache`, and `llm_service.py` already accepts `provider/model/api_key` as explicit parameters — making LLM hot-swap primarily a cache invalidation and DB write problem, not a service redesign.

The largest design challenge is the `lru_cache` on `get_settings()`. This cache was appropriate for the static env-based configuration of Phases 1–2, but now needs to yield to a hybrid model: env vars provide the initial/default values; the SQLite `AppConfig` row is the source of truth for mutable settings. The cleanest solution is to eliminate the `lru_cache` and have the shopping router read LLM config from `AppConfig` at request time — or introduce a thin `get_active_llm_config(db)` helper that always reads from SQLite, bypassing the cache entirely.

The settings page replaces the current placeholder with a 4-section sidebar layout (LLM, Store, Account, Preferences) using the same HTMX partial-swap pattern established in the wizard. Most UI components (store search, OAuth trigger, API key masking, test-connection feedback) are already built and can be extracted as reusable partials.

**Primary recommendation:** Replace `lru_cache` on `get_settings()` with a request-scoped DB read for the three mutable LLM fields (`llm_provider`, `llm_model`, `llm_api_key`). Keep `lru_cache` for static infrastructure settings (database URL, port, Kroger credentials, base URL). This is the minimal change that achieves hot-swap without cache-busting complexity.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Single form with dropdown selector for provider (not tabbed sections). Selecting a provider dynamically changes the fields below (API key for cloud, endpoint URL for Ollama).
- **D-02:** Curated dropdown for model selection showing top 3-5 models per provider (e.g., Haiku/Sonnet/Opus for Claude, GPT-4o/4o-mini for OpenAI), plus a "Custom model ID" text field for power users.
- **D-04:** Full settings hub — not LLM-only. Includes: LLM provider config, store location change, Kroger re-authorization, and app preferences.
- **D-05:** Settings page uses sidebar sub-navigation to switch between sections (LLM, Store, Account, Preferences). Not a single scrollable page.
- **D-06:** Re-use the wizard's zip search component (HTMX partial) for store location changes in settings. Consistent UX, less new code.
- **D-08:** Test connection before saving — run `test_connection()` inline when user submits new provider/key. Show success/failure feedback. Same pattern as wizard's LLM step. Prevents saving broken config.
- **D-09:** API key fields use masked input with reveal toggle (eye icon). Standard password field pattern.
- **D-11:** Minimal app preferences — just default review mode toggle (exceptions-only vs full review). Keep it simple for now.

### Claude's Discretion
- **D-03:** Ollama configuration approach (endpoint URL + model name vs auto-detect)
- **D-07:** Kroger re-auth UX (manual button vs proactive expiry banner, or both)
- **D-10:** Hot-swap timing (immediate on save vs after confirmation)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| LLM-02 | User can select and configure their preferred LLM provider and model in settings | D-01 through D-11 locked; LLM hot-swap via DB read pattern; test_connection() reuse; AppConfig extension |
</phase_requirements>

---

## Standard Stack

All libraries below are already in the project. No new dependencies required for this phase.

### Core (already installed)
| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| FastAPI | 0.135.3 | Router for settings endpoints | Existing framework |
| SQLModel + aiosqlite | 0.0.37 / 0.22.1 | AppConfig persistence for mutable settings | Existing ORM |
| pydantic-settings | 2.x | Env-var baseline config via `Settings` | Existing |
| LiteLLM | 1.83.0 | Multi-provider LLM abstraction | Already used in `llm_service.py` |
| Instructor | 1.14.5 | Structured LLM outputs | Already used in `llm_service.py` |
| Jinja2 | FastAPI dep | Settings page templates | Existing SSR pattern |
| HTMX | 1.9.12 (CDN) | Section switching, inline form feedback | Already in `base.html` |
| Alpine.js | 3.14.8 (CDN) | Provider dropdown dynamic field toggling, eye-icon reveal | Already in `base.html` |
| Authlib | 1.6.9 | Re-trigger Kroger OAuth from settings | Already used in `auth.py` |

### No New Dependencies
This phase introduces no new packages. The existing stack fully covers all requirements.

---

## Architecture Patterns

### Settings Hub Layout

The settings page replaces `templates/pages/settings.html` with a two-column layout: a left sidebar for sub-navigation and a right content area for the active section. The sub-navigation switches sections via HTMX partial swap, keeping the shell persistent.

```
templates/pages/settings.html          — Shell with sidebar + content target div
templates/partials/settings/
    llm.html                           — LLM provider config section
    store.html                         — Store location section (reuses search logic)
    account.html                       — Kroger auth status + re-authorize button
    preferences.html                   — Default review mode toggle
```

### Pattern 1: Settings Sub-Navigation via HTMX

Each sidebar link swaps only the content area, not the full page. This avoids full-page reloads while keeping server-side state.

```html
<!-- In settings.html shell -->
<div id="settings-content">
    {% include "partials/settings/llm.html" %}
</div>

<!-- Sidebar nav link -->
<a href="#"
   hx-get="/settings/section/llm"
   hx-target="#settings-content"
   hx-swap="innerHTML"
   hx-push-url="false">
    LLM Provider
</a>
```

```python
# In app/routers/settings.py
@router.get("/settings/section/{section}", response_class=HTMLResponse)
async def settings_section(
    request: Request,
    section: str,
    session: AsyncSession = Depends(get_session),
):
    cfg = await _get_config(session)
    template_map = {
        "llm": "partials/settings/llm.html",
        "store": "partials/settings/store.html",
        "account": "partials/settings/account.html",
        "preferences": "partials/settings/preferences.html",
    }
    template = template_map.get(section, "partials/settings/llm.html")
    return templates.TemplateResponse(request, template, {"cfg": cfg, ...})
```

### Pattern 2: Provider Dropdown with Dynamic Fields (Alpine.js)

D-01 requires that selecting a provider dynamically shows/hides the API key vs endpoint URL field. Alpine.js handles this entirely client-side — no round-trip needed.

```html
<div x-data="{ provider: '{{ cfg.llm_provider }}' }">
    <select name="provider" x-model="provider">
        <option value="anthropic">Claude (Anthropic)</option>
        <option value="openai">OpenAI</option>
        <option value="ollama">Ollama (local)</option>
    </select>

    <!-- Cloud provider: API key -->
    <div x-show="provider !== 'ollama'">
        <label>API Key</label>
        <input type="password" name="api_key" ...>
    </div>

    <!-- Ollama: endpoint URL -->
    <div x-show="provider === 'ollama'">
        <label>Ollama Endpoint URL</label>
        <input type="url" name="ollama_base_url" placeholder="http://localhost:11434" ...>
    </div>
</div>
```

### Pattern 3: LLM Hot-Swap — DB Read Instead of Cache

The `lru_cache` on `get_settings()` is the blocker for hot-swap. Three options analyzed:

**Option A (Recommended): DB-authoritative for mutable LLM fields**

Introduce `get_active_llm_config(db)` that always reads from `AppConfig`. `Settings` (`lru_cache`) only provides the static bootstrap. `shopping.py` already reads `AppConfig` for `store_id` at request time — same pattern.

```python
# app/services/llm_config.py (new)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.config_model import AppConfig
from app.config import get_settings

async def get_active_llm_config(db: AsyncSession) -> dict:
    """Return active LLM config from DB, falling back to env Settings."""
    result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    settings = get_settings()
    if cfg and cfg.llm_provider:
        return {
            "provider": cfg.llm_provider,
            "model": cfg.llm_model,
            "api_key": cfg.llm_api_key_encrypted or settings.llm_api_key,
        }
    return {
        "provider": settings.llm_provider,
        "model": settings.llm_model,
        "api_key": settings.llm_api_key,
    }
```

`shopping.py` calls `get_active_llm_config(session)` instead of `get_settings()` for LLM fields.

**Option B: `lru_cache` invalidation via `get_settings.cache_clear()`**

Call `get_settings.cache_clear()` after saving new LLM config so next request rebuilds from env. But this only works if env vars are updated — they aren't in this case (settings come from DB form fields). This approach requires writing env vars to disk, which is inappropriate for Docker and introduces file I/O complexity. **Do not use.**

**Option C: Module-level singleton with explicit update method**

A mutable `_active_config` dict updated on save. Works but requires careful thread safety reasoning and is essentially reinventing what the DB already provides. **No benefit over Option A.**

**Recommendation: Option A.** Extend `AppConfig` with `llm_api_key_encrypted` column (Fernet, same pattern as OAuth tokens), and always read LLM config from the DB row via `get_active_llm_config()`.

### Pattern 4: API Key Storage — Encrypted in AppConfig

The wizard currently reads `llm_api_key` from the env var and never persists it. For the settings page, the user enters a new API key in the form. This must be stored securely in SQLite using Fernet, the same mechanism as OAuth tokens.

```python
# AppConfig gets new field:
class AppConfig(SQLModel, table=True):
    ...
    llm_api_key_encrypted: Optional[str] = None
    llm_ollama_base_url: Optional[str] = None   # D-03: for Ollama endpoint
    review_mode: str = Field(default="exceptions")   # D-11: "exceptions" | "full"
```

The `get_or_create_fernet()` utility in `oauth_manager.py` is reused for encrypt/decrypt. The settings save endpoint calls it before writing to DB.

### Pattern 5: Test Connection Inline (D-08)

Identical to wizard pattern. The save form posts to `/settings/save-llm`, which calls `llm_service.test_connection()` before writing to DB.

```python
@router.post("/settings/save-llm", response_class=HTMLResponse)
async def save_llm_settings(
    request: Request,
    provider: str = Form(...),
    model: str = Form(...),
    api_key: str = Form(""),
    custom_model: str = Form(""),
    ollama_base_url: str = Form(""),
    session: AsyncSession = Depends(get_session),
):
    active_model = custom_model or model
    active_key = api_key if provider != "ollama" else ""

    success, message = await llm_service.test_connection(
        api_key=active_key,
        provider=provider,
        model=active_model,
        base_url=ollama_base_url if provider == "ollama" else None,
    )
    if not success:
        return templates.TemplateResponse(request, "partials/settings/llm.html",
            {"error": message, "cfg": ...})

    # Encrypt and persist
    ...
    return templates.TemplateResponse(request, "partials/settings/llm.html",
        {"success": "Provider updated successfully.", "cfg": updated_cfg})
```

Note: `llm_service.test_connection()` currently does not accept `base_url`. For Ollama support it needs a `base_url` parameter passed to LiteLLM's `api_base` argument.

### Pattern 6: Ollama Configuration (D-03 — Claude's Discretion)

**Recommendation:** Store endpoint URL explicitly (`llm_ollama_base_url` in `AppConfig`). Do not auto-detect. The user enters `http://localhost:11434` (or a custom Docker network address). LiteLLM accepts `api_base` to override the Ollama endpoint:

```python
# In llm_service.test_connection() for Ollama:
response = await litellm.acompletion(
    model=f"ollama/{model}",
    messages=[{"role": "user", "content": "ping"}],
    api_base=base_url,   # e.g. "http://localhost:11434"
    max_tokens=5,
)
```

No API key required for Ollama. The API key field in the UI is hidden when `provider === 'ollama'` (Alpine.js).

### Pattern 7: Kroger Re-Auth UX (D-07 — Claude's Discretion)

**Recommendation:** Show both — a status indicator and a manual re-authorize button. The Account section displays:
1. Current auth status: "Authorized" (green) or "Not authorized" (amber) — derived from whether `OAuthToken` record exists in DB with a non-expired `expires_at`
2. A "Re-authorize with Kroger" button that links to `/auth/kroger/start` (existing endpoint, no changes needed)
3. After successful re-auth, OAuth callback redirects to `/tour` (current behavior) — consider redirecting to `/settings?section=account` instead for better UX

The re-auth flow reuses `auth.py` endpoints entirely. No new OAuth code.

### Pattern 8: Hot-Swap Timing (D-10 — Claude's Discretion)

**Recommendation:** Immediate on save, after successful `test_connection()`. No confirmation modal — test connection IS the confirmation. This is the simplest approach and matches user expectations: you tested it, it worked, it's now active. Next shopping run uses the new provider.

The hot-swap works because `shopping.py` calls `get_active_llm_config(db)` at request time, which always reads from the DB. There is no in-memory state to flush.

### Pattern 9: Eye-Icon Reveal for API Keys (D-09)

Standard Alpine.js toggle pattern:

```html
<div x-data="{ show: false }">
    <div class="relative">
        <input
            :type="show ? 'text' : 'password'"
            name="api_key"
            class="w-full bg-slate-700 ..."
        >
        <button type="button" @click="show = !show" class="absolute right-3 top-2.5 text-slate-400">
            <!-- eye / eye-slash SVG based on `show` -->
        </button>
    </div>
</div>
```

### Anti-Patterns to Avoid

- **Calling `get_settings.cache_clear()` to achieve hot-swap:** This only resets env var reads, not DB-stored values. Will not work for API keys entered in the settings form.
- **Storing the API key in plain text in AppConfig:** Use Fernet encryption (same as OAuth tokens). The Fernet key is already on the Docker volume.
- **Restarting the app or clearing all settings on provider change:** The whole point of this phase is zero-restart hot-swap.
- **Global mutable module-level state for current provider:** Concurrency-unsafe and unnecessary; DB is the source of truth.
- **Using `request.session` for LLM config:** Session is ephemeral and per-user. LLM config is persistent app config.
- **Redirecting to /setup after re-auth from settings:** Use `/settings?section=account` instead — user shouldn't see wizard again.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Multi-provider LLM routing | Custom provider switch/case | LiteLLM `provider/model` string | LiteLLM already handles auth, retries, error normalization per provider |
| Fernet key management | New key storage | `get_or_create_fernet()` in oauth_manager | Already handles /data/app.key on Docker volume |
| OAuth re-auth | New PKCE flow | `/auth/kroger/start` endpoint | Authlib already handles PKCE; just link to it |
| Store search | New store search UI | Extract `step_store.html` as partial | Fully functional, proven in wizard flow |
| Test-connection pattern | New LLM validation | `llm_service.test_connection()` | Already handles all 3 providers and error cases |
| API key masking | Custom masking | `_mask_value()` in setup.py | Already handles empty/short/long values |

---

## Common Pitfalls

### Pitfall 1: `lru_cache` Stale After Settings Save
**What goes wrong:** User updates LLM provider in settings UI. `get_settings()` still returns the old values because `lru_cache` froze them at first call. Shopping run uses old provider.
**Why it happens:** `lru_cache` caches the `Settings()` object on first call. Env vars don't change when DB changes.
**How to avoid:** Do not use `get_settings()` for LLM provider/model/api_key in `shopping.py`. Use `get_active_llm_config(db)` (Option A) which reads from `AppConfig` at request time.
**Warning signs:** Setting change in UI succeeds but next shopping run uses old provider.

### Pitfall 2: Ollama API Key Field Submitted as Empty String
**What goes wrong:** Ollama has no API key. If the form always submits `api_key`, an empty string gets encrypted and stored. On next load, the field shows `****` (masked empty), confusing the user.
**Why it happens:** HTML forms always submit named fields.
**How to avoid:** Backend sets `llm_api_key_encrypted = None` when `provider == "ollama"`. UI hides the API key field and doesn't include it in form submission (Alpine.js `x-show` with `:name` binding or remove field name).

### Pitfall 3: Alembic Migration Missing for New AppConfig Columns
**What goes wrong:** New columns (`llm_api_key_encrypted`, `llm_ollama_base_url`, `review_mode`) are defined in the model but not in the DB schema. Existing installations fail on startup or silently use None.
**Why it happens:** `SQLModel.metadata.create_all` only adds tables, not columns. Alembic is needed for ALTER TABLE on existing DBs.
**How to avoid:** Generate an Alembic migration for the new columns. Run `alembic revision --autogenerate -m "add llm settings columns"`. Include the migration in the Docker image.

### Pitfall 4: Store Search Partial Has Wizard-Specific Endpoint URLs
**What goes wrong:** Extracting `step_store.html` as a shared partial and using it in settings, but the form still posts to `/setup/search-stores` and `/setup/select-store`. Settings save overwrites `wizard_step` in AppConfig.
**Why it happens:** The store search form has hardcoded endpoint URLs for the wizard flow.
**How to avoid:** Create settings-specific endpoints (`/settings/search-stores`, `/settings/select-store`) that do NOT modify `wizard_step` or `wizard_complete`. The store select endpoint for settings only updates `store_id/name/zip`. Parameterize the partial or duplicate as a settings-specific version.

### Pitfall 5: Settings Router Conflicts with pages.py `/settings` Route
**What goes wrong:** `pages.py` has `@router.get("/settings")`. New `settings.py` router also registers `/settings/*`. FastAPI may conflict or require careful ordering.
**Why it happens:** Two routers both handling `/settings*` paths.
**How to avoid:** Move the `/settings` GET handler entirely into the new `settings.py` router. Remove it from `pages.py`. Register `settings.py` router in `main.py`.

### Pitfall 6: test_connection() Missing base_url Parameter for Ollama
**What goes wrong:** Calling `test_connection(provider="ollama", model="llama3")` fails because LiteLLM tries to reach the default Ollama endpoint, which may not be accessible from inside Docker.
**Why it happens:** Current `test_connection()` does not accept `base_url` / `api_base`.
**How to avoid:** Extend `test_connection()` signature with `base_url: Optional[str] = None`. Pass it to LiteLLM as `api_base=base_url` when provider is "ollama".

### Pitfall 7: Decrypting API Key When User Hasn't Changed It
**What goes wrong:** Settings form loads with masked key (`****abcd`). User changes provider but not the key. Form submits the masked value, which gets re-encrypted as the literal string `****abcd`.
**Why it happens:** Masked display value ≠ real value. Form submits what's displayed.
**How to avoid:** Use a sentinel value to detect "unchanged." Simplest: empty the API key field in the form (show placeholder only, not masked value). If submitted empty and provider is not ollama, keep the existing encrypted value. Document this in the form UX: "Leave blank to keep current key."

---

## Code Examples

### Verified Pattern: Reading AppConfig at Request Time (existing pattern in shopping.py)

```python
# Source: app/routers/shopping.py (existing)
result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
cfg = result.scalar_one_or_none()
location_id = (cfg.store_id or "") if cfg else ""
```

The LLM config hot-swap uses the exact same pattern — extend `AppConfig` read to include LLM fields.

### Verified Pattern: Fernet Encryption (existing in oauth_manager.py)

```python
# Source: app/services/oauth_manager.py (existing)
f = get_or_create_fernet()
encrypted = f.encrypt(plain_value.encode()).decode()
decrypted = f.decrypt(encrypted_value.encode()).decode()
```

Reuse `get_or_create_fernet()` for API key encryption in settings save.

### Verified Pattern: LiteLLM Ollama with Custom Base URL

```python
# Source: LiteLLM docs — litellm.acompletion with api_base
response = await litellm.acompletion(
    model="ollama/llama3",
    messages=[{"role": "user", "content": "ping"}],
    api_base="http://host.docker.internal:11434",  # Docker host
    max_tokens=5,
)
```

Confidence: HIGH — LiteLLM's `api_base` parameter for Ollama is documented and well-established.

### Verified Pattern: HTMX Section Swap (existing pattern from wizard)

```html
<!-- Target div stays persistent, only content swaps -->
<div id="settings-content">
    {# initial section renders here #}
</div>

<a hx-get="/settings/section/store"
   hx-target="#settings-content"
   hx-swap="innerHTML">
    Store
</a>
```

### Model Dropdown with Custom ID (D-02)

```html
<!-- Alpine.js manages custom model toggle -->
<div x-data="{ customModel: false, selectedModel: '{{ cfg.llm_model }}' }">
    <select name="model" x-model="selectedModel"
            @change="customModel = (selectedModel === '__custom__')">
        <!-- Claude models -->
        <template x-if="provider === 'anthropic'">
            <optgroup label="Claude">
                <option value="claude-3-haiku-20240307">Claude 3 Haiku (fast)</option>
                <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                <option value="claude-3-opus-20240229">Claude 3 Opus</option>
                <option value="__custom__">Custom model ID...</option>
            </optgroup>
        </template>
        <!-- OpenAI models -->
        <template x-if="provider === 'openai'">
            <optgroup label="OpenAI">
                <option value="gpt-4o-mini">GPT-4o mini (fast)</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="__custom__">Custom model ID...</option>
            </optgroup>
        </template>
        <!-- Ollama: always custom -->
        <template x-if="provider === 'ollama'">
            <option value="__custom__">Enter model name below</option>
        </template>
    </select>

    <!-- Custom model text field -->
    <input
        x-show="customModel || provider === 'ollama'"
        type="text"
        name="custom_model"
        placeholder="e.g. llama3, mistral, claude-3-opus-20240229"
    >
</div>
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `lru_cache` for all settings | DB-authoritative for mutable config | Phase 4 | Shopping router must call `get_active_llm_config(db)` not `get_settings()` for LLM fields |
| Wizard-only LLM config entry | Full settings hub with hot-swap | Phase 4 | Settings page replaces placeholder |
| API key from env var only | API key from env var OR encrypted DB | Phase 4 | `AppConfig` needs new columns + Alembic migration |

---

## Environment Availability

Step 2.6: SKIPPED — Phase is code and template changes only. No external tool dependencies beyond what is already running (Docker, SQLite, LiteLLM). Ollama availability is a user-side concern; the settings page handles the endpoint-not-reachable case via `test_connection()` error feedback.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + anyio + httpx AsyncClient |
| Config file | `pytest.ini` or `pyproject.toml [tool.pytest]` |
| Quick run command | `pytest tests/test_settings.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| LLM-02 | GET /settings renders settings hub | integration | `pytest tests/test_settings.py::test_settings_page_renders -x` | Wave 0 |
| LLM-02 | POST /settings/save-llm saves provider to AppConfig | integration | `pytest tests/test_settings.py::test_save_llm_settings -x` | Wave 0 |
| LLM-02 | POST /settings/save-llm with bad key returns error, does not save | integration | `pytest tests/test_settings.py::test_save_llm_invalid_key -x` | Wave 0 |
| LLM-02 | Provider change takes effect on next shopping match (hot-swap) | integration | `pytest tests/test_settings.py::test_llm_hotswap -x` | Wave 0 |
| LLM-02 | Ollama provider stores endpoint URL, not API key | integration | `pytest tests/test_settings.py::test_ollama_config -x` | Wave 0 |
| LLM-02 | GET /settings/section/{section} returns correct partial | integration | `pytest tests/test_settings.py::test_settings_sections -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_settings.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_settings.py` — all LLM-02 tests listed above
- [ ] `app/services/llm_config.py` — `get_active_llm_config()` helper (new module, not test)
- [ ] Alembic migration for new AppConfig columns — not a test file but a Wave 0 prerequisite

---

## Project Constraints (from CLAUDE.md)

| Directive | Category | Impact on Phase 4 |
|-----------|----------|-------------------|
| Python 3.12 + FastAPI + HTMX/Jinja2 SSR | Stack lock | Settings page is server-rendered; no React/Vue |
| LiteLLM for all LLM calls | Stack lock | Ollama integration uses LiteLLM `api_base`, not direct Ollama SDK |
| Instructor for structured output | Stack lock | Not impacted — settings page doesn't call structured LLM |
| SQLite single-file, `--workers 1` | Infrastructure | Settings save endpoints are safe (single writer) |
| `PRAGMA journal_mode=WAL` required | DB | Already in `init_db()` — new migration must not reset this |
| Customer search data must not be persisted | TOS | Not impacted — settings stores only config, not shopping data |
| Products API results must never be written to SQLite | TOS | Not impacted |
| OAuth redirect URI from `BASE_URL` env var | Auth | Re-auth button uses `/auth/kroger/start` — already compliant |
| Do not bake credentials into Docker image | Security | API keys stored encrypted in volume-mounted SQLite, not image |
| Secrets via env vars at runtime | Security | LLM API key from DB (entered in settings UI) takes priority over env default |
| GSD workflow enforcement | Process | Changes made through `/gsd:execute-phase` |
| `replicas: 1` always | Infrastructure | No concurrency concern for settings writes |

---

## Open Questions

1. **Should `/auth/kroger/callback` redirect to `/settings?section=account` instead of `/tour` when re-auth is triggered from settings?**
   - What we know: Current callback always redirects to `/tour`. When the user re-auths from settings, landing on `/tour` is confusing.
   - What's unclear: Whether the callback can know its origin (settings vs wizard).
   - Recommendation: Pass a `redirect_after` query param to `/auth/kroger/start`, persist in Starlette session, use in callback. Or simply redirect to `/settings` unconditionally if `wizard_complete=True`. The latter is simpler and covers the settings re-auth case.

2. **Should the settings page show the current model active in the DB, or the env var default when no DB override exists?**
   - What we know: On a fresh install, `AppConfig.llm_provider` defaults to "anthropic" and `AppConfig.llm_model` defaults to "claude-3-haiku-20240307", matching the env var defaults.
   - What's unclear: If user set `LLM_PROVIDER=openai` in their `.env` but DB still shows "anthropic" (Phase 1/2 default), which should the settings page show?
   - Recommendation: `get_active_llm_config()` checks DB first, falls back to env. Settings page displays what DB says. On first visit to settings, user sees whatever was saved in wizard/default — this is correct behavior. Sync DB from env on first app start if DB shows factory defaults.

3. **How should `review_mode` preference (D-11) integrate with the shopping flow?**
   - What we know: `SRCH-04/05` (Phase 2) implemented exceptions-only as the default. The toggle was already implemented in Phase 2.
   - What's unclear: Where is the current review mode preference stored? In session? In AppConfig?
   - Recommendation: Verify in `shopping.py` whether review mode is currently session-based or config-based before designing the preferences section. If session-based, Phase 4 persists it to `AppConfig.review_mode` and shopping reads from there.

---

## Sources

### Primary (HIGH confidence)
- Codebase: `app/config.py` — confirmed `lru_cache` pattern and Settings structure
- Codebase: `app/services/llm_service.py` — confirmed `test_connection()`, `provider/model/api_key` params
- Codebase: `app/models/config_model.py` — confirmed AppConfig schema
- Codebase: `app/routers/shopping.py` — confirmed DB-read pattern for `store_id` (template for LLM config)
- Codebase: `app/services/oauth_manager.py` — confirmed Fernet reuse pattern
- Codebase: `templates/base.html` — confirmed HTMX 1.9.12, Alpine.js 3.14.8 versions
- LiteLLM docs (CLAUDE.md verified): `api_base` parameter supported for Ollama
- CLAUDE.md: All stack and constraint directives

### Secondary (MEDIUM confidence)
- LiteLLM Ollama integration: documented `api_base` parameter for custom endpoints — verified via LiteLLM project patterns; Ollama LiteLLM support is widely documented

### Tertiary (LOW confidence)
- None — all findings verified against codebase or authoritative stack docs

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in codebase, versions confirmed
- Architecture: HIGH — patterns derived directly from existing codebase; hot-swap analysis based on confirmed `lru_cache` implementation
- Pitfalls: HIGH — all pitfalls derived from specific code inspection (existing wizard endpoints, Fernet usage, AppConfig schema)
- LLM provider model lists: MEDIUM — model names correct as of training knowledge; may need updating if providers release new models before implementation

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable stack; LLM model names may shift)
