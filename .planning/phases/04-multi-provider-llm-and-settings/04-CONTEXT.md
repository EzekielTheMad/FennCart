# Phase 4: Multi-Provider LLM and Settings - Context

**Gathered:** 2026-04-04
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can choose their preferred LLM provider (Claude, OpenAI, Ollama) and manage all app settings beyond the initial setup wizard — without restarting the container.

</domain>

<decisions>
## Implementation Decisions

### Provider Config UX
- **D-01:** Single form with dropdown selector for provider (not tabbed sections). Selecting a provider dynamically changes the fields below (API key for cloud, endpoint URL for Ollama).
- **D-02:** Curated dropdown for model selection showing top 3-5 models per provider (e.g., Haiku/Sonnet/Opus for Claude, GPT-4o/4o-mini for OpenAI), plus a "Custom model ID" text field for power users.

### Ollama Configuration
- **D-03:** Claude's discretion on how Ollama differs from cloud providers. Key distinction: endpoint URL + model name instead of API key. Simplest viable approach.

### Settings Page Scope
- **D-04:** Full settings hub — not LLM-only. Includes: LLM provider config, store location change, Kroger re-authorization, and app preferences.
- **D-05:** Settings page uses sidebar sub-navigation to switch between sections (LLM, Store, Account, Preferences). Not a single scrollable page.

### Store Change Flow
- **D-06:** Re-use the wizard's zip search component (HTMX partial) for store location changes in settings. Consistent UX, less new code.

### Kroger Re-Auth
- **D-07:** Claude's discretion on re-auth flow. Must show current auth status and provide a manual re-authorize button that triggers the existing OAuth PKCE flow.

### Validation & Feedback
- **D-08:** Test connection before saving — run `test_connection()` inline when user submits new provider/key. Show success/failure feedback. Same pattern as wizard's LLM step. Prevents saving broken config.
- **D-09:** API key fields use masked input with reveal toggle (eye icon). Standard password field pattern.

### Hot-Swap Behavior
- **D-10:** Claude's discretion on when provider switch takes effect. Must work without container restart. The `lru_cache` on `get_settings()` will need to be invalidated or replaced.

### App Preferences
- **D-11:** Minimal app preferences — just default review mode toggle (exceptions-only vs full review). Keep it simple for now.

### Claude's Discretion
- D-03: Ollama configuration approach (endpoint URL + model name vs auto-detect)
- D-07: Kroger re-auth UX (manual button vs proactive expiry banner, or both)
- D-10: Hot-swap timing (immediate on save vs after confirmation)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### LLM Integration
- `app/services/llm_service.py` — Current LLM abstraction: `test_connection()`, `parse_shopping_list()`, `match_products()`. All accept `provider`, `model`, `api_key` params.
- `app/config.py` — `Settings` class with `llm_provider`, `llm_model`, `llm_api_key` from env. Uses `lru_cache`.
- `app/models/config_model.py` — `AppConfig` model persists `llm_provider` and `llm_model` in SQLite.

### Existing Wizard (patterns to reuse)
- `templates/setup/step_llm.html` — LLM API key entry and test connection UI from wizard
- `templates/setup/step_store.html` — Store zip search and selection UI from wizard
- `templates/setup/step_oauth.html` — OAuth PKCE flow UI from wizard
- `app/routers/setup.py` — Wizard router with all setup endpoints

### Settings Page
- `templates/pages/settings.html` — Current placeholder (replace entirely)
- `app/routers/pages.py` — Page router with `/settings` endpoint
- `templates/base.html` — Base layout with sidebar nav (settings link already exists)

### Auth Flow
- `app/routers/auth.py` — OAuth PKCE endpoints (re-use for re-auth from settings)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `llm_service.test_connection()` — Already handles multi-provider connection testing via LiteLLM
- Wizard step templates — Store search and OAuth flow can be extracted as HTMX partials
- `templates/partials/` — Established pattern for HTMX partial responses (loading_spinner, error_block, etc.)
- Tailwind dark theme — Consistent slate-950/900/800 palette with green-500 accents

### Established Patterns
- HTMX for dynamic interactions (`hx-post`, `hx-target`, `hx-swap`)
- Alpine.js for client-side state (toggles, form state)
- FastAPI + Jinja2 server-side rendering
- SQLModel for DB persistence via `AppConfig`
- `pydantic-settings` for env-based config with `lru_cache`

### Integration Points
- `/settings` route already exists in `pages.py` — needs new handler logic
- `AppConfig` model needs new fields (or a new model) for expanded settings
- `get_settings()` cache invalidation needed for hot-swap
- Sidebar nav in `base.html` already links to settings

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-multi-provider-llm-and-settings*
*Context gathered: 2026-04-04*
