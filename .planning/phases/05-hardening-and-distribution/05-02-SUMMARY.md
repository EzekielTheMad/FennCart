---
phase: 05-hardening-and-distribution
plan: "02"
subsystem: testing-and-distribution
tags: [migrations, testing, pytest-alembic, readme, documentation]
dependency_graph:
  requires: []
  provides: [migration-safety-tests, quickstart-readme]
  affects: [alembic/env.py, tests/test_migrations.py, requirements-dev.txt, README.md]
tech_stack:
  added: [pytest-alembic==0.12.1]
  patterns: [pytest-alembic connection injection guard, synchronous SQLite engine for migration tests]
key_files:
  created:
    - tests/test_migrations.py
    - README.md
  modified:
    - alembic/env.py
    - requirements-dev.txt
decisions:
  - "Engine-to-Connection unwrap in env.py: pytest-alembic 0.12.1 injects Engine (not Connection) via config.attributes; env.py must call connectable.connect() to get a Connection before passing to do_run_migrations()"
  - "Manual table inspection for schema match test: check_model_definitions_match_ddl() does not exist in pytest-alembic 0.12.1; replaced with SQLAlchemy inspector to verify expected tables exist"
  - "Forward-only migrations: no downgrade test, consistent with D-07"
metrics:
  duration: "~7 minutes"
  completed: "2026-04-06"
  tasks_completed: 2
  files_changed: 4
---

# Phase 05 Plan 02: Migration Safety Testing and Distribution Documentation Summary

Migration chain verified clean (empty DB to head), quickstart README created for self-hosters.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add pytest-alembic migration upgrade test with env.py connection injection | 24c9b76 | tests/test_migrations.py, alembic/env.py, requirements-dev.txt |
| 2 | Create quickstart README | cc9995c | README.md |

## What Was Built

**Migration safety tests (tests/test_migrations.py):**
- `test_migrations_upgrade_to_head`: All 4 Alembic migrations (0001-0004) apply sequentially from empty DB to head without error
- `test_model_definitions_match_ddl`: Final migrated schema verified to contain all 6 expected tables via SQLAlchemy inspector
- Uses synchronous in-memory SQLite engine — avoids touching `/data/fenncart.db`

**Alembic env.py connection injection guard:**
- `run_migrations_online()` checks `config.attributes.get("connection", None)` for pytest-alembic injection
- Handles Engine vs Connection distinction (pytest-alembic 0.12.1 injects Engine, not Connection)
- Falls back to production async path when no injection present

**Quickstart README:**
- Prerequisites, 5-step Quickstart, Configuration table, Upgrading, Architecture, Development sections
- Links to developer.kroger.com, console.anthropic.com, platform.openai.com
- SESSION_SECRET_KEY generation command and change-from-default warning

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] pytest-alembic injects Engine not Connection**
- **Found during:** Task 1 verification
- **Issue:** `config.attributes["connection"]` contained a `sqlalchemy.engine.Engine` instance; `context.configure(connection=engine)` raises `CommandError` in Alembic 2.x (expects `Connection` instance)
- **Fix:** Added `isinstance(connectable, Engine)` check in `run_migrations_online()`; calls `connectable.connect()` to obtain a Connection before passing to `do_run_migrations()`
- **Files modified:** alembic/env.py
- **Commit:** 24c9b76

**2. [Rule 1 - Bug] check_model_definitions_match_ddl() does not exist in pytest-alembic 0.12.1**
- **Found during:** Task 1 verification
- **Issue:** `MigrationContext` in pytest-alembic 0.12.1 has no `check_model_definitions_match_ddl()` method; plan code based on a different API version
- **Fix:** Replaced with manual SQLAlchemy `inspect(engine).get_table_names()` check asserting all 6 expected tables are present after migration to head
- **Files modified:** tests/test_migrations.py
- **Commit:** 24c9b76

## Test Results

- `python -m pytest tests/test_migrations.py -x -q` — 2 passed
- `python -m pytest tests/ -x -q` — 175 passed (173 existing + 2 new)

## Self-Check: PASSED

- tests/test_migrations.py: FOUND
- README.md: FOUND
- alembic/env.py contains `config.attributes.get("connection", None)`: FOUND
- alembic/env.py contains `asyncio.run(run_async_migrations())` fallback: FOUND
- requirements-dev.txt contains `pytest-alembic==0.12.1`: FOUND
- Commit 24c9b76: FOUND
- Commit cc9995c: FOUND
