---
phase: 05-hardening-and-distribution
plan: 01
subsystem: infrastructure
tags: [docker, security, configuration, hardening]
dependency_graph:
  requires: []
  provides: [docker-build-context-exclusions, llm-sdk-dependencies, session-key-validator]
  affects: [app/config.py, requirements.txt, requirements-dev.txt, pytest.ini]
tech_stack:
  added: [pytest-env==1.6.0]
  patterns: [pydantic-field-validator, docker-build-context-optimization]
key_files:
  created: [.dockerignore]
  modified: [requirements.txt, app/config.py, .gitignore, pytest.ini, requirements-dev.txt]
decisions:
  - pytest-env for SESSION_SECRET_KEY in test environment
  - anthropic and openai added after litellm in requirements.txt
metrics:
  duration: ~15min
  completed: 2026-04-06
  tasks_completed: 2
  files_changed: 6
---

# Phase 05 Plan 01: Docker Optimization and Security Hardening Summary

Docker build context trimmed to runtime-only files, LLM provider SDKs made explicit, and a startup safety check added for the session secret key.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Create .dockerignore and add LLM SDKs to requirements.txt | 58e99fe | .dockerignore, requirements.txt |
| 2 | Add SESSION_SECRET_KEY startup validator and update .gitignore | dd753c8 | app/config.py, .gitignore, pytest.ini, requirements-dev.txt |

## What Was Built

**`.dockerignore`** (new file, 44 lines): Excludes `.git/`, `.planning/`, `.claude/`, `tests/`, `__pycache__/`, `*.pyc`, `.env`, `.venv/`, `*.db` files, `static/output.css`, `Dockerfile`, and `.dockerignore` itself from the Docker build context. Deliberately preserves `tailwind.config.js` and `static/input.css` which the Dockerfile needs to run Tailwind CLI at build time.

**`requirements.txt`** (updated): Added `anthropic` and `openai` after the existing `litellm==1.83.0` line. LiteLLM does not bundle provider SDKs as extras — `anthropic` must be listed explicitly or `litellm.completion()` raises `ImportError` at runtime when using the Claude provider. `openai` was already a transitive dep but is now explicit for visibility. Total: 17 entries.

**`app/config.py`** (updated): Added `from pydantic import field_validator` import and a `session_key_must_be_changed` validator. The validator raises `ValueError` with a clear message if `SESSION_SECRET_KEY` is the literal default `"change-me-in-production"`. Any other value passes (including `"test-secret"` used in test fixtures). This causes the app to fail fast at startup rather than silently running with an insecure session key.

**`.gitignore`** (updated): Added `/data/` directory exclusion at the end. The `/data/` mount point contains `fenncart.db` (SQLite database) and `app.key` (Fernet encryption key) — neither should ever be committed. The existing `*.db` pattern already catches loose .db files, but `/data/` is needed to protect `app.key` too.

**`pytest.ini`** (updated): Added `env = SESSION_SECRET_KEY=test-secret` section using `pytest-env`. This sets the env var before conftest imports, which is necessary because `tests/conftest.py` imports `from app.main import app` at module level, which triggers `get_settings()` before any fixture can run. Without this, the validator would reject the default value during test collection.

**`requirements-dev.txt`** (updated): Added `pytest-env` to support the `env =` section in `pytest.ini`.

## Deviations from Plan

### Auto-added Issues

**1. [Rule 2 - Missing Critical Functionality] Add pytest-env for SESSION_SECRET_KEY in test environment**
- **Found during:** Task 2
- **Issue:** `app/main.py` line 62 calls `get_settings()` at module level for `SessionMiddleware`. When tests import `app.main`, this triggers `Settings()` instantiation with the default `session_secret_key="change-me-in-production"` — before any test fixture can override it. The validator would reject this value during test collection, breaking all 82 tests.
- **Fix:** Added `pytest-env` to `requirements-dev.txt` and configured `env = SESSION_SECRET_KEY=test-secret` in `pytest.ini`. The `pytest_load_initial_conftests` hook in pytest-env runs before any conftest is imported, ensuring the env var is set before `get_settings()` is called.
- **Files modified:** `pytest.ini`, `requirements-dev.txt`
- **Commit:** dd753c8

## Verification Results

- `.dockerignore` exists with all required exclusions, `tailwind.config.js` and `static/input.css` not excluded
- `requirements.txt` contains `anthropic`, `openai`, and `litellm==1.83.0`
- `Settings(session_secret_key="change-me-in-production")` raises `ValueError` with "insecure default" message
- `Settings(session_secret_key="test-secret", ...)` succeeds
- All 82 tests pass (full test suite for phases 01-02)

## Known Stubs

None.

## Self-Check: PASSED
- `.dockerignore` exists: FOUND
- `requirements.txt` contains anthropic: FOUND
- Commits 58e99fe and dd753c8: FOUND (verified via git log)
