---
phase: 03-preference-system
plan: "01"
subsystem: preference-system
tags: [models, schemas, services, migration, pdfplumber, instructor]
dependency_graph:
  requires: []
  provides:
    - PreferenceEntry SQLModel table
    - ReceiptUpload SQLModel table
    - app/schemas/preferences.py (all Phase 3 Pydantic schemas)
    - PreferenceService (CRUD + contradiction detection + preferences dict)
    - ReceiptParser (PDF text extraction + LLM normalization)
    - Alembic migration 0004_preference_tables
  affects:
    - alembic/env.py (models autodiscovered via app/models/__init__.py)
    - app/services/llm_service.match_products (preferences hook now has data source)
tech_stack:
  added: []
  patterns:
    - SQLModel table=True with UniqueConstraint via __table_args__
    - Instructor from_provider pattern (same as llm_service.py)
    - pdfplumber extract_text(layout=True) with extract_words() fallback
    - purchase_count >= 2 threshold for preference strength signals
key_files:
  created:
    - app/models/preference_entry.py
    - app/models/receipt_upload.py
    - app/schemas/preferences.py
    - app/services/preference_service.py
    - app/services/receipt_parser.py
    - alembic/versions/0004_preference_tables.py
  modified:
    - app/models/__init__.py
decisions:
  - purchase_count >= 2 threshold for contradiction detection and preference signals — prevents single-purchase anomalies from overriding learned preferences
  - Items with empty brand never trigger contradictions — accommodates generic/store-brand items with no brand identity
  - get_preferences_for_matching limits to 50 entries — token budget for LLM match_products system prompt
  - TOS guard comment in PreferenceService — documents that preference signals must never come from Kroger API responses or cart_items
metrics:
  duration: "~2 min"
  completed_date: "2026-04-06"
  tasks_completed: 2
  files_created: 6
  files_modified: 1
---

# Phase 03 Plan 01: Preference Data Layer Summary

**One-liner:** SQLModel preference tables, 6 Pydantic schemas, PreferenceService with 10 CRUD/detection methods, and pdfplumber+Instructor receipt parsing pipeline — the complete data foundation for Phase 3.

## What Was Built

### Task 1: Data Models, Schemas, and Migration

**`app/models/preference_entry.py`** — `PreferenceEntry` SQLModel table tracking brand preferences by (product_category, brand, product_name). Unique constraint prevents duplicate entries. `purchase_count` tracks frequency; `source` distinguishes receipt imports from manual/NL chat entries.

**`app/models/receipt_upload.py`** — `ReceiptUpload` audit table tracking PDF uploads with parse status lifecycle (pending → parsed → confirmed → failed).

**`app/models/__init__.py`** — Updated with imports for both new models, ensuring Alembic autodiscovery via `alembic/env.py`.

**`app/schemas/preferences.py`** — 6 Pydantic schemas covering the full Phase 3 surface:
- `ReceiptLineItem` / `ParsedReceipt` — Instructor response models for receipt parsing
- `ContradictionCandidate` — Brand conflict resolution workflow
- `PreferenceDelta` — NL chat preference update interpretation
- `PreferenceCreateRequest` / `PreferenceUpdateRequest` — Manual CRUD API contracts

**`alembic/versions/0004_preference_tables.py`** — Migration creating both tables with the `uq_pref_category_brand_product` unique constraint and `ix_preference_entries_product_category` index. Down_revision points to `0003abcd5678`.

### Task 2: PreferenceService and ReceiptParser

**`app/services/preference_service.py`** — `PreferenceService` class with 10 methods:
- `upsert_from_receipt_item` — creates or increments preference entry; is_one_time skips increment
- `detect_contradictions` — finds items that conflict with established preferences (purchase_count >= 2)
- `get_preferences_for_matching` — builds preferences dict for LLM product matching (50-entry limit, strength=strong/moderate)
- `list_preferences` — ilike search across product_name/brand/category
- `get_preference` / `create_preference` / `update_preference` / `delete_preference` — standard CRUD
- `bulk_delete` — batch delete by IDs
- `apply_nl_delta` — applies add/remove/replace deltas from NL chat

**`app/services/receipt_parser.py`** — Two-function pipeline:
- `extract_receipt_text` — pdfplumber with `layout=True` extraction; falls back to `extract_words()` on empty pages; warns on < 50 chars extracted
- `parse_receipt_with_llm` — Instructor + LiteLLM with Fry's abbreviation system prompt (PRIV SEL, ORG, CHCKN, etc.); max_retries=2

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan delivers data layer and service layer only. No UI or routing wired yet (that is Phase 3 Plans 02-04).

## Self-Check: PASSED

Files verified:
- FOUND: app/models/preference_entry.py
- FOUND: app/models/receipt_upload.py
- FOUND: app/schemas/preferences.py
- FOUND: app/services/preference_service.py
- FOUND: app/services/receipt_parser.py
- FOUND: alembic/versions/0004_preference_tables.py

Commits verified:
- FOUND: 65e6be3 (Task 1 — models, schemas, migration)
- FOUND: 2db6ecf (Task 2 — services)
