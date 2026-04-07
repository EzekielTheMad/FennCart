# Phase 5: Hardening and Distribution - Context

**Gathered:** 2026-04-06
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the app ready for a non-developer to self-host confidently and for the project to be shared publicly. No new features — hardening, optimization, documentation, and distribution polish only.

</domain>

<decisions>
## Implementation Decisions

### Docker Optimization
- **D-01:** Single-stage build retained (no multi-stage). Add `.dockerignore` to exclude `.git/`, `.planning/`, `tests/`, `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `docs/`, and other non-runtime files.
- **D-02:** Ship all LLM provider SDKs (anthropic, openai) baked into the image. Users switch providers in settings without rebuilding. Accept the larger image size for simplicity.
- **D-03:** Pin LiteLLM with provider extras explicitly in requirements.txt if possible (e.g., `litellm[proxy]` or individual SDKs) to avoid pulling unnecessary transitive dependencies. Investigate what LiteLLM actually needs for anthropic/openai/ollama only.

### Setup Documentation
- **D-04:** Quickstart-focused README. What it does, prerequisites (Docker, Kroger dev account, LLM key), 5-step quickstart (clone, configure .env, docker compose up, complete wizard, start shopping). No separate docs/ folder for v1.
- **D-05:** Brief credential pointers — link to developer.kroger.com and LLM provider signup pages with 1-2 sentence guidance. No step-by-step portal walkthroughs.

### Migration Safety
- **D-06:** Automated upgrade-path test: applies migrations sequentially (empty DB -> 0001 -> 0002 -> ... -> head) and verifies the final schema matches SQLModel metadata. Catches broken migration chains before release.
- **D-07:** Forward-only migrations. No downgrade() support. If a migration breaks, user restores from backup. Simpler migration code.

### Security Hardening
- **D-08:** Claude's Discretion. Appropriate scope for a single-user BYO-credentials self-hosted app. Essential runtime checks preferred over dev-tooling overhead.

### Claude's Discretion
- Security hardening scope: Claude will determine the right balance. Expected baseline includes SESSION_SECRET_KEY enforcement (refuse to start with default value), .gitignore verification for .env and /data/, and any other low-friction production safety checks. Pre-commit hooks are optional — only add if they provide clear value without burdening self-hosters.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Docker & Deployment
- `Dockerfile` — Current single-stage build with Tailwind CLI, healthcheck, Alembic on startup
- `docker-compose.yml` — Volume mount, env_file, restart policy
- `.env.example` — All credential placeholders with comments (Kroger, LLM, BASE_URL, SESSION_SECRET_KEY)
- `requirements.txt` — Current pinned dependencies
- `tailwind.config.js` — Tailwind content paths for CSS purging

### Database & Migrations
- `alembic.ini` — Alembic configuration
- `alembic/env.py` — Migration environment setup
- `alembic/versions/` — 4 migrations (0001-0004): initial schema, cart tables, LLM settings, preference tables

### Application Entry
- `app/main.py` — FastAPI app with middleware, health endpoint, startup config
- `app/config.py` — Settings via pydantic-settings, env var loading

### Test Suite
- `tests/` — 12 test files, 173 tests (conftest.py, test_cart_service, test_health, test_kroger_client, test_kroger_products, test_llm_config, test_llm_matching, test_oauth, test_preference_service, test_preferences_flow, test_receipt_parser, test_settings, test_shopping_flow, test_wizard)
- `requirements-dev.txt` — Test dependencies (pytest, pytest-anyio, httpx, anyio)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Dockerfile` with Tailwind CLI standalone build — already avoids Node.js
- `docker-compose.yml` with proper volume mount pattern
- `.env.example` with all required variables documented
- Health endpoint at `/health` already used by Docker HEALTHCHECK
- 4 sequential Alembic migrations with proper revision chain

### Established Patterns
- Alembic runs `upgrade head` on container start (CMD in Dockerfile)
- Fernet key auto-generated at `/data/app.key` on first run
- pydantic-settings loads from env vars / .env file
- SQLite at `/data/fenncart.db` via Docker volume
- `--workers 1` enforced for SQLite safety

### Integration Points
- README needs to reference the wizard flow (steps 1-4) that already exists
- .dockerignore must align with what Dockerfile COPY expects
- Migration test needs access to alembic config and all migration files
- SESSION_SECRET_KEY check would go in app startup (app/main.py or app/config.py)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches for a self-hosted Docker app distribution.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 05-hardening-and-distribution*
*Context gathered: 2026-04-06*
