# Phase 5: Hardening and Distribution - Research

**Researched:** 2026-04-06
**Domain:** Docker optimization, README documentation, Alembic migration testing, security hardening
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Single-stage build retained (no multi-stage). Add `.dockerignore` to exclude `.git/`, `.planning/`, `tests/`, `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `docs/`, and other non-runtime files.
- **D-02:** Ship all LLM provider SDKs (anthropic, openai) baked into the image. Users switch providers in settings without rebuilding. Accept the larger image size for simplicity.
- **D-03:** Pin LiteLLM with provider extras explicitly in requirements.txt if possible (e.g., `litellm[proxy]` or individual SDKs) to avoid pulling unnecessary transitive dependencies. Investigate what LiteLLM actually needs for anthropic/openai/ollama only.
- **D-04:** Quickstart-focused README. What it does, prerequisites (Docker, Kroger dev account, LLM key), 5-step quickstart (clone, configure .env, docker compose up, complete wizard, start shopping). No separate docs/ folder for v1.
- **D-05:** Brief credential pointers — link to developer.kroger.com and LLM provider signup pages with 1-2 sentence guidance. No step-by-step portal walkthroughs.
- **D-06:** Automated upgrade-path test: applies migrations sequentially (empty DB -> 0001 -> 0002 -> ... -> head) and verifies the final schema matches SQLModel metadata. Catches broken migration chains before release.
- **D-07:** Forward-only migrations. No downgrade() support. If a migration breaks, user restores from backup. Simpler migration code.

### Claude's Discretion
- Security hardening scope: Claude will determine the right balance. Expected baseline includes SESSION_SECRET_KEY enforcement (refuse to start with default value), .gitignore verification for .env and /data/, and any other low-friction production safety checks. Pre-commit hooks are optional — only add if they provide clear value without burdening self-hosters.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

Phase 5 is a non-functional hardening phase covering four distinct domains: Docker optimization (`.dockerignore`, LiteLLM dependency audit), distribution documentation (README), migration safety testing (Alembic sequential upgrade test), and security hardening (startup validation for `SESSION_SECRET_KEY`). All four domains are largely independent and can be planned as separate tasks.

The biggest research finding is that **LiteLLM does not have per-provider extras** (`litellm[anthropic]` does not exist). Instead, LiteLLM 1.83.0 bundles `openai` as a hard dependency and relies on `anthropic` being installed separately. D-03 should be implemented by explicitly listing `anthropic` and `openai` in `requirements.txt` as peer dependencies rather than through LiteLLM extras syntax.

For the migration upgrade test (D-06), the recommended approach is `pytest-alembic` 0.12.1. Its `test_upgrade` built-in test covers the sequential empty→head run, and `test_model_definitions_match_ddl` verifies schema alignment. However, async SQLite requires a custom `alembic_engine` fixture in `conftest.py` using a synchronous SQLite engine (not aiosqlite), since pytest-alembic's DDL comparison test runs synchronously.

**Primary recommendation:** Implement the four domains as four focused tasks — `.dockerignore`, README, migration test, security hardening — in that order.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest-alembic | 0.12.1 | Migration chain testing | Built-in `test_upgrade` + `test_model_definitions_match_ddl`; zero boilerplate for the sequential upgrade test D-06 requires |
| pytest | 8.4.2 (already installed) | Test runner | Already in the project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| anthropic | (latest stable via pip) | Anthropic SDK | Needed for LiteLLM to call Claude models; must be listed explicitly since LiteLLM has no `[anthropic]` extra |
| openai | 2.30.0 (LiteLLM hard dep) | OpenAI SDK | Already pulled by LiteLLM; explicit pin in requirements.txt makes the dependency visible |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-alembic | Hand-rolled migration test using `alembic.command.upgrade()` | Hand-rolled is viable (8-15 lines), avoids a new dependency; pytest-alembic adds `test_model_definitions_match_ddl` automatically, which is the harder part to replicate manually |
| pytest-alembic | alembic-verify | Last maintained 2019; dead project |

**Installation (new dependency):**
```bash
pip install pytest-alembic==0.12.1
```

**Version verification:** pytest-alembic 0.12.1 confirmed current as of 2026-04-06 (released May 27, 2025 per PyPI).

---

## Architecture Patterns

### Recommended Project Structure (no changes needed)
The existing structure is correct for this phase. Phase 5 adds:
```
.dockerignore          # new — excludes non-runtime files from build context
README.md              # new — quickstart documentation
tests/test_migrations.py  # new — pytest-alembic migration upgrade test
```

### Pattern 1: .dockerignore for Python + FastAPI Projects
**What:** Exclude development artifacts and sensitive files from Docker build context.
**When to use:** Every Python Docker project.

```
# .dockerignore for FennCart
.git/
.planning/
.claude/
.vscode/
.idea/
tests/
docs/
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.eggs/
dist/
build/
.env
.venv/
venv/
env/
*.db
*.db-shm
*.db-wal
static/output.css
.pytest_cache/
.coverage
htmlcov/
Dockerfile
.dockerignore
.gitignore
*.md
requirements-dev.txt
```

**Note:** `tailwind.config.js` and `static/input.css` must remain — the Dockerfile runs Tailwind at build time and requires them.

### Pattern 2: pytest-alembic Migration Test with Sync SQLite Engine
**What:** Test that all 4 migrations apply cleanly from empty DB to head, and that the final schema matches SQLModel metadata.
**When to use:** Any project using Alembic — catches broken revision chains before release.

```python
# tests/test_migrations.py
# Source: pytest-alembic docs + issue #99 (async workaround)
import pytest
import sqlalchemy as sa
from pytest_alembic.config import Config


@pytest.fixture
def alembic_config():
    return Config.from_raw_config({
        "script_location": "alembic",
        "sqlalchemy.url": "sqlite:///",
    })


@pytest.fixture
def alembic_engine(alembic_config):
    engine = sa.create_engine("sqlite:///", echo=False)
    yield engine
    engine.dispose()


def test_migrations_upgrade(alembic_runner):
    """Empty DB to head runs without error."""
    alembic_runner.migrate_up_to("head")


def test_model_definitions_match_ddl(alembic_runner):
    """Final schema matches SQLModel metadata."""
    alembic_runner.migrate_up_to("head")
    alembic_runner.check_model_definitions_match_ddl()
```

**Critical:** Use synchronous `sqlalchemy.create_engine("sqlite:///")`, not `create_async_engine`. pytest-alembic's DDL check runs synchronously. The project's production DB uses async aiosqlite, but the test uses a temporary sync SQLite — this is correct and intentional.

**alembic/env.py compatibility:** The current `env.py` uses `asyncio.run()`. pytest-alembic injects its connection via `context.config.attributes.get("connection", None)`. The `env.py` needs a guard to use the injected connection when present:

```python
# alembic/env.py — add this pattern at the top of run_migrations_online()
def run_migrations_online():
    # pytest-alembic injects the connection directly
    connectable = context.config.attributes.get("connection", None)
    if connectable is not None:
        do_run_migrations(connectable)
        return
    # normal async path for production
    asyncio.run(run_async_migrations())
```

### Pattern 3: SESSION_SECRET_KEY Startup Enforcement
**What:** App refuses to start if `SESSION_SECRET_KEY` still has the default value.
**When to use:** Any app that uses signed sessions with a placeholder default in config.

```python
# app/config.py — add validator
from pydantic import validator  # or field_validator for Pydantic v2

class Settings(BaseSettings):
    session_secret_key: str = "change-me-in-production"

    @field_validator("session_secret_key")
    @classmethod
    def session_key_must_be_changed(cls, v: str) -> str:
        if v == "change-me-in-production":
            raise ValueError(
                "SESSION_SECRET_KEY must be changed from the default value. "
                "Set a random string in your .env file."
            )
        return v
```

**Alternative location:** In `app/main.py` lifespan function as a startup check. The config validator approach is cleaner — fails at import time with a clear message rather than deep in startup.

### Anti-Patterns to Avoid
- **Using `create_async_engine` in pytest-alembic fixtures:** pytest-alembic's `test_model_definitions_match_ddl` test runs sync DDL introspection; async engines cause "cannot run a coroutine" errors.
- **Excluding `tailwind.config.js` from .dockerignore:** The Dockerfile runs `tailwindcss -i ./static/input.css -o ./static/output.css` at build time; these files must be present in the build context.
- **Excluding `static/input.css` from .dockerignore:** Same reason — Tailwind CLI needs it.
- **Adding `litellm[anthropic]` to requirements.txt:** This extra does not exist. LiteLLM uses openai as a hard dep and requires anthropic to be listed separately.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sequential migration upgrade test | Manual `alembic.command.upgrade()` loop + schema introspection | `pytest-alembic` | Built-in `test_model_definitions_match_ddl` does table/column comparison against SQLModel metadata automatically; schema introspection is 30+ lines of SQLAlchemy inspection code |
| Docker build context reduction | Manual COPY statements listing each file | `.dockerignore` | Standard Docker mechanism; simpler than selective COPY |

**Key insight:** The migration test is the one area where a small external library (pytest-alembic) saves significant code. The `.dockerignore`, README, and startup validation are all hand-written with zero external dependencies.

---

## Common Pitfalls

### Pitfall 1: LiteLLM "extras" that don't exist
**What goes wrong:** `litellm[anthropic]` or `litellm[openai]` in requirements.txt raises a pip error at build time ("no such extra").
**Why it happens:** LiteLLM does not define per-provider extras. openai is a hard dependency; anthropic is a separate package.
**How to avoid:** List `anthropic` and `openai` explicitly in `requirements.txt` alongside `litellm==1.83.0`. Do not use extras syntax for LiteLLM providers.
**Warning signs:** `pip install` fails with "no such extra" during Docker build.

### Pitfall 2: pytest-alembic async engine incompatibility
**What goes wrong:** `test_model_definitions_match_ddl` fails or hangs with async engine.
**Why it happens:** pytest-alembic's DDL introspection calls sync SQLAlchemy inspect() under the hood.
**How to avoid:** Use `sqlalchemy.create_engine("sqlite:///")` (sync) for `alembic_engine` fixture. The production DB uses async; the test uses a separate throwaway sync engine.
**Warning signs:** `RuntimeError: no running event loop` or `greenlet_spawn has not been called`.

### Pitfall 3: env.py asyncio conflict with pytest-alembic
**What goes wrong:** Migration test fails with "asyncio.run() cannot be called from a running event loop."
**Why it happens:** pytest-alembic runs inside the pytest event loop; `asyncio.run()` in env.py conflicts.
**How to avoid:** Add the connection injection guard to env.py (see Pattern 2 code above) so pytest-alembic provides the connection directly.
**Warning signs:** `RuntimeError: This event loop is already running`.

### Pitfall 4: .dockerignore excluding Tailwind build inputs
**What goes wrong:** Docker build fails at `RUN tailwindcss -i ./static/input.css ...` with "no such file".
**Why it happens:** `static/input.css` or `tailwind.config.js` excluded from build context.
**How to avoid:** Never add `static/input.css`, `static/*.css`, or `tailwind.config.js` to `.dockerignore`. Only exclude `static/output.css` (it's regenerated at build time).
**Warning signs:** `error: failed to read CSS file`.

### Pitfall 5: SESSION_SECRET_KEY validation fires in tests
**What goes wrong:** `pytest` fails immediately because test settings use a non-default but valid test key ("test-secret"), but the validator logic is too broad.
**Why it happens:** If the validator rejects anything containing "test" or short strings.
**How to avoid:** The validator should only reject the literal string `"change-me-in-production"`. Any other value — including short test strings — should pass. The existing `conftest.py` sets `session_secret_key="test-secret"` which is fine.
**Warning signs:** All pytest tests fail at collection time with `ValueError`.

### Pitfall 6: alembic.ini database URL used in migration test
**What goes wrong:** Migration test connects to `/data/fenncart.db` (the production path from `alembic.ini`) instead of in-memory SQLite.
**Why it happens:** pytest-alembic reads `alembic.ini` unless `alembic_config` fixture overrides the URL.
**How to avoid:** Override `sqlalchemy.url` in the `alembic_config` fixture to `sqlite:///` (in-memory).
**Warning signs:** Test creates files at `/data/fenncart.db` or fails with "unable to open database file".

---

## Code Examples

Verified patterns from official sources and project inspection:

### LiteLLM dependency declaration (D-03)
```
# requirements.txt — correct way to pin LiteLLM with Anthropic + OpenAI support
litellm==1.83.0
anthropic           # explicit peer dep for Claude models (no litellm[anthropic] extra exists)
openai==2.30.0      # LiteLLM hard dep; pin explicitly for clarity
```

Source: LiteLLM pyproject.toml (WebFetch 2026-04-06) — openai listed as core dep, no anthropic/openai extras defined.

### .dockerignore content
```dockerignore
# Version control
.git/
.gitignore

# Planning and development
.planning/
.claude/
docs/
*.md

# Tests and dev dependencies
tests/
requirements-dev.txt
pytest.ini
.pytest_cache/
.coverage
htmlcov/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
*.egg-info/
.eggs/
dist/
build/

# Secrets and local config
.env
.venv/
venv/
env/

# Database files (runtime, not build)
*.db
*.db-shm
*.db-wal

# Generated CSS (regenerated at build time)
static/output.css

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker meta
Dockerfile
.dockerignore
```

### alembic/env.py connection injection guard
```python
# Source: pytest-alembic issue #99 pattern
def run_migrations_online():
    # Allow pytest-alembic to inject a synchronous connection directly
    connectable = context.config.attributes.get("connection", None)
    if connectable is not None:
        do_run_migrations(connectable)
        return
    # Production: async SQLite via aiosqlite
    asyncio.run(run_async_migrations())
```

### Pydantic v2 field validator for SESSION_SECRET_KEY
```python
# app/config.py
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    session_secret_key: str = "change-me-in-production"

    @field_validator("session_secret_key")
    @classmethod
    def session_key_must_be_changed(cls, v: str) -> str:
        if v == "change-me-in-production":
            raise ValueError(
                "SESSION_SECRET_KEY must be set to a random string in your .env file. "
                "It is currently using the insecure default value."
            )
        return v
```

Source: Pydantic v2 `field_validator` docs — replaces deprecated `@validator`.

### README quickstart structure (D-04, D-05)
```markdown
# FennCart

[1-sentence description]. Named after Fenn, a DnD character who doubled as the party's chef.

## Prerequisites

- Docker and Docker Compose
- A [Kroger developer account](https://developer.kroger.com) (free)
- An API key from Anthropic, OpenAI, or a local Ollama instance

## Quickstart

1. Clone the repo: `git clone https://github.com/you/fenncart && cd fenncart`
2. Copy the env template: `cp .env.example .env` and fill in your credentials
3. Start the app: `docker compose up -d`
4. Open http://localhost:8000 and complete the setup wizard (LLM key → Kroger OAuth → store selection)
5. Paste a shopping list and start adding to cart

## Configuration

All configuration is via environment variables in `.env`. See `.env.example` for all options.

| Variable | Required | Description |
|----------|----------|-------------|
| KROGER_CLIENT_ID | Yes | From developer.kroger.com → My Apps |
| KROGER_CLIENT_SECRET | Yes | From developer.kroger.com → My Apps |
| LLM_API_KEY | Yes | Your Anthropic/OpenAI key, or leave blank for Ollama |
| SESSION_SECRET_KEY | Yes | A random string for session cookie signing |
| BASE_URL | Yes | The URL users access (e.g., http://localhost:8000) |

## Upgrading

`docker compose pull && docker compose up -d`

Alembic migrations run automatically on container start. Data in the `fenncart_data` volume is preserved.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@validator` (Pydantic v1) | `@field_validator` (Pydantic v2) | Pydantic v2 (2023) | Different decorator signature; `@validator` works but deprecated |
| Docker multi-stage builds for size | `.dockerignore` + single-stage (D-01 decision) | N/A — both valid | Multi-stage is not needed here; `.dockerignore` achieves same build context reduction |
| `litellm[proxy]` for deployment | Separate `anthropic` + `openai` in requirements.txt | Always been this way | No per-provider extras exist in LiteLLM |

**Deprecated/outdated:**
- `@validator` in Pydantic v1: Still works in Pydantic v2 with deprecation warning; replace with `@field_validator`.
- alembic-verify (PyPI): Last maintained 2019; do not use. Use pytest-alembic instead.

---

## Open Questions

1. **Does `anthropic` SDK need explicit pinning in requirements.txt?**
   - What we know: `litellm==1.83.0` does NOT list anthropic as a dependency. Users will hit an ImportError if they select Claude without anthropic installed.
   - What's unclear: Whether LiteLLM lazy-imports anthropic (import at call time) or fails at import of litellm itself.
   - Recommendation: Add `anthropic` unpinned to requirements.txt. LiteLLM's tested compatible version range handles the constraint.

2. **Should the migration test use `test_model_definitions_match_ddl` or just `test_upgrade`?**
   - What we know: `test_model_definitions_match_ddl` requires a sync engine and verifies final schema matches SQLModel metadata — catches missing columns added after migrations were written.
   - What's unclear: Whether SQLite's limited DDL introspection causes false failures (e.g., column type mapping differences).
   - Recommendation: Include both tests. If `test_model_definitions_match_ddl` produces SQLite-specific false positives, drop it and keep only `test_upgrade`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | README validation / image build | ✗ (not in dev shell) | — | Test with `docker build` on host machine manually |
| pytest | Migration test | ✓ | 8.4.2 | — |
| pytest-alembic | Migration test (D-06) | ✗ | — | Add to requirements-dev.txt; install before running migration tests |
| SQLAlchemy sync | Migration test alembic_engine fixture | ✓ | 2.0.44 | — |
| anthropic SDK | LiteLLM Claude calls | ✗ (not installed) | — | Add to requirements.txt |

**Missing dependencies with no fallback:**
- pytest-alembic: Must be added to `requirements-dev.txt` before migration tests can run.
- anthropic: Must be added to `requirements.txt` before Claude provider works in Docker image.

**Missing dependencies with fallback:**
- Docker: Not available in dev shell — Docker build and integration validation must be done on host machine separately.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 |
| Config file | `pytest.ini` (exists) |
| Quick run command | `python -m pytest tests/test_migrations.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map

Phase 5 has no formal requirement IDs. The four success criteria map to tests as follows:

| Success Criterion | Behavior | Test Type | Automated Command | File Exists? |
|-------------------|----------|-----------|-------------------|--------------|
| Fresh-machine setup works | README accuracy | manual | N/A — human follow-along | ❌ N/A |
| Docker image builds cleanly | .dockerignore + deps correct | smoke | `docker build .` | ❌ manual |
| OAuth inside Docker produces no redirect errors | BASE_URL env var documented | manual | N/A | ❌ N/A |
| Migrations apply without data loss | Sequential upgrade 0001→head | automated | `python -m pytest tests/test_migrations.py -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -q` (173 existing tests must stay green)
- **Migration task specifically:** `python -m pytest tests/test_migrations.py -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_migrations.py` — pytest-alembic sequential upgrade test (D-06)
- [ ] `pytest-alembic==0.12.1` must be added to `requirements-dev.txt`

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 5 |
|-----------|-------------------|
| Python 3.12-slim Docker base | Keep — no change |
| `--workers 1` Uvicorn | Keep in CMD — no change |
| Volume mount: `/data/fenncart.db` | Document in README |
| TOS: No customer search data persisted | No impact — hardening only |
| pydantic-settings for all config | SESSION_SECRET_KEY validator goes in Settings class |
| Replicas: 1 | Document in README as constraint |
| Secrets via env vars only | .env handling must be clear in README and .dockerignore |
| pytest + httpx for testing | Migration test adds pytest-alembic; no conflict |
| Pydantic v2 | Use `@field_validator`, not deprecated `@validator` |

---

## Sources

### Primary (HIGH confidence)
- LiteLLM pyproject.toml (WebFetch 2026-04-06) — verified no per-provider extras exist; openai is core dep
- PyPI: pytest-alembic 0.12.1 (verified 2026-04-06)
- PyPI: openai 2.30.0 (verified via local pip show 2026-04-06)
- pytest-alembic issue #99 — async workaround (connection injection via `context.config.attributes`)
- Docker .dockerignore best practices — [Docker official docs](https://docs.docker.com/build/building/best-practices/)
- Pydantic v2 field_validator docs (known, HIGH confidence — Pydantic v2 is project constraint)

### Secondary (MEDIUM confidence)
- [pytest-alembic PyPI](https://pypi.org/project/pytest-alembic/) — built-in tests documented
- [pytest-alembic GitHub](https://github.com/schireson/pytest-alembic) — async native example (uses postgres fixture, not directly applicable but shows pattern)
- [Docker Python best practices TestDriven.io](https://testdriven.io/blog/docker-best-practices/) — .dockerignore patterns

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- .dockerignore content: HIGH — standard Docker patterns, project structure verified by inspection
- LiteLLM extras claim: HIGH — verified from pyproject.toml; no anthropic/openai extras defined
- pytest-alembic async pattern: MEDIUM — issue #99 shows the connection injection fix; exact env.py wiring is a judgment call
- SESSION_SECRET_KEY validator: HIGH — standard Pydantic v2 field_validator pattern
- README structure: HIGH — locked in D-04/D-05; content is straightforward

**Research date:** 2026-04-06
**Valid until:** 2026-05-06 (stable domain — Docker, pytest, Pydantic v2 are slow-moving)
