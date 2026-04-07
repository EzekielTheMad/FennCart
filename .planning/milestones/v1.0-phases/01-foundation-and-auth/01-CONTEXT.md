# Phase 1: Foundation and Auth - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a running Docker container with: SQLite schema + Alembic migrations, a guided setup wizard, Kroger OAuth PKCE flow, silent token refresh, and an app shell with placeholder pages for future phases. After this phase, a user can spin up the container, complete setup, and be authenticated with Kroger — ready for the shopping flow in Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Setup Wizard Flow
- **D-01:** Wizard step order: LLM API key validation → Kroger developer credentials validation → Store selection via zip → Kroger OAuth login. Each step validates before allowing the user to proceed (test LLM connection, verify Kroger API keys, confirm store exists).
- **D-02:** Wizard is resumable — progress saved to SQLite so if user closes browser mid-wizard, they resume from last completed step on return.

### Post-Setup Landing
- **D-03:** After setup completes, show a brief quick tour / tips walkthrough before the main screen (upload receipts, paste lists, how the flow works). Then land on the main app.

### Credential Storage
- **D-04:** All sensitive API credentials (Kroger client ID/secret, LLM API key) come from environment variables / `.env` file only. Never stored in SQLite. The wizard reads and validates them but does not persist them.
- **D-05:** Non-secret config stored in SQLite: store selection, OAuth tokens (refresh/access), wizard completion state, user preferences.
- **D-06:** OAuth tokens encrypted at rest in SQLite using an app-generated key stored in the Docker volume.

### Error Handling UX
- **D-07:** If credentials are missing at container start, app starts but only serves a "missing config" page that explains which env vars are needed and how to set them. Does not refuse to start entirely.

### Claude's Discretion
- Error UX pattern (inline errors vs toasts vs dedicated pages) — Claude picks the approach that fits the HTMX/Jinja2 SSR pattern best.
- Navigation structure (top bar vs sidebar vs minimal) — Claude picks based on what works for a single-purpose app with 4-5 future pages.

### App Shell / Navigation
- **D-08:** Build the full navigation shell in Phase 1 with all nav items (Shopping, Preferences, History, Settings). Non-Phase-1 pages show "Coming soon" placeholders. This avoids rebuilding nav structure in later phases.

### Docker / Distribution
- **D-09:** Single container, no compose dependencies. Docker setup must be Unraid Community Apps compatible — the long-term goal is an Unraid CA template with WebUI, port mappings, volume paths (`/mnt/user/appdata/fenncart/`), and env vars defined in the Unraid XML format.
- **D-10:** Design docker-compose.yml and Dockerfile with Unraid conventions in mind: single exposed port, named volume for `/data`, clear env var definitions with descriptions. The Unraid CA XML template itself can be a Phase 5 deliverable, but the container design must not conflict with it.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Kroger API
- `FennCartPitch.md` — Full Kroger API details, auth flow, rate limits, TOS constraints, acceptable use policy
- `.planning/research/STACK.md` — Verified stack recommendations with versions (FastAPI, Authlib, SQLModel, etc.)
- `.planning/research/ARCHITECTURE.md` — Component boundaries, data flow, OAuth PKCE pattern in Docker
- `.planning/research/PITFALLS.md` — 14 specific pitfalls with prevention strategies, especially OAuth redirect URI and credential management

### Project Context
- `.planning/PROJECT.md` — Three credential sets, TOS constraints, architecture decisions
- `.planning/REQUIREMENTS.md` — SETUP-01 through SETUP-04 acceptance criteria
- `.planning/STATE.md` — Architecture constraints (carry forward section) and research flags for Phase 1

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code.

### Established Patterns
- None yet. Phase 1 establishes the foundational patterns (FastAPI app structure, Jinja2 template organization, SQLModel models, Alembic migration workflow).

### Integration Points
- Phase 2 will build on: the app shell (nav, base templates), the SQLite database (adding cart/product models), the Kroger API client (adding product search), and the LLM service abstraction.

</code_context>

<specifics>
## Specific Ideas

- User wants Unraid Community Apps compatibility as the distribution target. Container must follow single-container, single-port, named-volume conventions.
- Receipt upload and preference features come in Phase 3, but the quick tour after setup should mention them as upcoming capabilities.
- The "missing config" page (when env vars are absent) should be helpful enough that a non-developer can figure out what to do.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation-and-auth*
*Context gathered: 2026-04-02*
