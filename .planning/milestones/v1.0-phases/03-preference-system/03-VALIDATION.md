---
phase: 03
slug: preference-system
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-04
updated: 2026-04-08
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Backfilled to nyquist_compliant: true on 2026-04-08 (Phase 09 plan 01).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 with pytest-asyncio |
| **Config file** | `pytest.ini` (project root) |
| **asyncio_mode** | auto (pytest.ini) |
| **SESSION_SECRET_KEY** | Set via `pytest-env` in pytest.ini |
| **Quick run command** | `python -m pytest tests/test_receipt_parser.py tests/test_preference_service.py tests/test_preferences_flow.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_receipt_parser.py tests/test_preference_service.py tests/test_preferences_flow.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PREF-01 | unit | `python -m pytest tests/test_receipt_parser.py::test_extract_receipt_text_valid_pdf -x` | ✅ | ✅ green |
| 03-01-02 | 01 | 1 | PREF-01 | unit | `python -m pytest tests/test_receipt_parser.py::test_extract_receipt_text_empty_pdf -x` | ✅ | ✅ green |
| 03-01-03 | 01 | 1 | PREF-01 | unit | `python -m pytest tests/test_receipt_parser.py::test_extract_receipt_text_invalid_bytes -x` | ✅ | ✅ green |
| 03-01-04 | 01 | 1 | PREF-01 | unit | `python -m pytest tests/test_receipt_parser.py::test_parse_receipt_with_llm -x` | ✅ | ✅ green |
| 03-02-01 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_upsert_new_item -x` | ✅ | ✅ green |
| 03-02-02 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_upsert_increment -x` | ✅ | ✅ green |
| 03-02-03 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_upsert_one_time_no_increment -x` | ✅ | ✅ green |
| 03-02-04 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_detect_contradictions_triggers -x` | ✅ | ✅ green |
| 03-02-05 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_detect_contradictions_no_trigger_low_count -x` | ✅ | ✅ green |
| 03-02-06 | 02 | 1 | PREF-03 | unit | `python -m pytest tests/test_preference_service.py::test_detect_contradictions_empty_brand_ignored -x` | ✅ | ✅ green |
| 03-02-07 | 02 | 1 | PREF-06 | unit | `python -m pytest tests/test_preference_service.py::test_get_preferences_for_matching -x` | ✅ | ✅ green |
| 03-02-08 | 02 | 1 | PREF-06 | unit | `python -m pytest tests/test_preference_service.py::test_get_preferences_for_matching_cap_at_50 -x` | ✅ | ✅ green |
| 03-02-09 | 02 | 1 | PREF-06 | unit | `python -m pytest tests/test_preference_service.py::test_get_preferences_empty -x` | ✅ | ✅ green |
| 03-02-10 | 02 | 1 | PREF-05 | unit | `python -m pytest tests/test_preference_service.py::test_list_preferences_with_query -x` | ✅ | ✅ green |
| 03-02-11 | 02 | 1 | PREF-05 | unit | `python -m pytest tests/test_preference_service.py::test_create_preference_manual -x` | ✅ | ✅ green |
| 03-02-12 | 02 | 1 | PREF-05 | unit | `python -m pytest tests/test_preference_service.py::test_update_preference -x` | ✅ | ✅ green |
| 03-02-13 | 02 | 1 | PREF-05 | unit | `python -m pytest tests/test_preference_service.py::test_delete_preference -x` | ✅ | ✅ green |
| 03-02-14 | 02 | 1 | PREF-05 | unit | `python -m pytest tests/test_preference_service.py::test_bulk_delete -x` | ✅ | ✅ green |
| 03-02-15 | 02 | 1 | PREF-04 | unit | `python -m pytest tests/test_preference_service.py::test_apply_nl_delta_add -x` | ✅ | ✅ green |
| 03-02-16 | 02 | 1 | PREF-04 | unit | `python -m pytest tests/test_preference_service.py::test_apply_nl_delta_remove -x` | ✅ | ✅ green |
| 03-02-17 | 02 | 1 | PREF-04 | unit | `python -m pytest tests/test_preference_service.py::test_apply_nl_delta_replace -x` | ✅ | ✅ green |
| 03-03-01 | 03 | 1 | PREF-05 | integration | `python -m pytest tests/test_preferences_flow.py::test_preferences_page_loads -x` | ✅ | ✅ green |
| 03-03-02 | 03 | 1 | PREF-01 | integration | `python -m pytest tests/test_preferences_flow.py::test_upload_receipt -x` | ✅ | ✅ green |
| 03-03-03 | 03 | 1 | PREF-01 | integration | `python -m pytest tests/test_preferences_flow.py::test_upload_invalid_file -x` | ✅ | ✅ green |
| 03-03-04 | 03 | 1 | PREF-05 | integration | `python -m pytest tests/test_preferences_flow.py::test_preference_crud -x` | ✅ | ✅ green |
| 03-03-05 | 03 | 1 | PREF-05 | integration | `python -m pytest tests/test_preferences_flow.py::test_preference_search -x` | ✅ | ✅ green |
| 03-03-06 | 03 | 1 | PREF-05 | integration | `python -m pytest tests/test_preferences_flow.py::test_bulk_delete_preferences -x` | ✅ | ✅ green |
| 03-03-07 | 03 | 1 | PREF-04 | integration | `python -m pytest tests/test_preferences_flow.py::test_nl_chat_clarify -x` | ✅ | ✅ green |
| 03-03-08 | 03 | 1 | PREF-04 | integration | `python -m pytest tests/test_preferences_flow.py::test_nl_chat_confirm -x` | ✅ | ✅ green |
| 03-03-09 | 03 | 1 | PREF-06 | unit | `python -m pytest tests/test_preferences_flow.py::test_process_list_with_preferences -x` | ✅ | ✅ green |
| 03-03-10 | 03 | 1 | PREF-01, LLM-CONFIG | integration | `python -m pytest tests/test_preferences_flow.py::test_upload_receipt_uses_db_llm_config -x` | ✅ | ✅ green |
| 03-03-11 | 03 | 1 | PREF-04, LLM-CONFIG | integration | `python -m pytest tests/test_preferences_flow.py::test_nl_chat_uses_db_llm_config -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Test Function Reference

**tests/test_receipt_parser.py** (4 tests — PREF-01)
- `test_extract_receipt_text_valid_pdf` — Valid PDF page returns text and empty warnings (PREF-01).
- `test_extract_receipt_text_empty_pdf` — Image-based PDF page returns warning (PREF-01).
- `test_extract_receipt_text_invalid_bytes` — Non-PDF bytes returns empty string + error warning (PREF-01).
- `test_parse_receipt_with_llm` — Instructor client returns ParsedReceipt with expected items (PREF-01).

**tests/test_preference_service.py** (16 tests — PREF-03, PREF-04, PREF-05, PREF-06)
- `test_upsert_new_item` — First receipt item creates entry with purchase_count=1, source='receipt' (PREF-03).
- `test_upsert_increment` — Same item twice increments purchase_count from 1 to 2 (PREF-03).
- `test_upsert_one_time_no_increment` — is_one_time=True does not increment existing entry (PREF-03).
- `test_detect_contradictions_triggers` — Established preference (count>=2) + different brand triggers contradiction (PREF-03).
- `test_detect_contradictions_no_trigger_low_count` — count==1 entry does NOT trigger contradiction (PREF-03).
- `test_detect_contradictions_empty_brand_ignored` — Empty brand never triggers contradiction (PREF-03).
- `test_get_preferences_for_matching` — Returns only count>=2 entries, ordered by count DESC (PREF-06).
- `test_get_preferences_for_matching_cap_at_50` — Results capped at 50 entries (PREF-06).
- `test_get_preferences_empty` — Returns `{'entries': []}` when no established preferences (PREF-06).
- `test_list_preferences_with_query` — Search query filters by name/brand/category (PREF-05).
- `test_create_preference_manual` — Manual entry has source='manual', purchase_count=1 (PREF-05).
- `test_update_preference` — Updates only non-None fields, refreshes updated_at (PREF-05).
- `test_delete_preference` — Removes entry; returns True/False for exists/missing (PREF-05).
- `test_bulk_delete` — Removes all specified entries, returns deleted count (PREF-05).
- `test_apply_nl_delta_add` — action='add' creates entry with source='nl_chat' (PREF-04).
- `test_apply_nl_delta_remove` — action='remove' deletes matching entry, returns None (PREF-04).
- `test_apply_nl_delta_replace` — action='replace' updates brand, preserves purchase_count (PREF-04).

**tests/test_preferences_flow.py** (11 tests — PREF-01, PREF-04, PREF-05, PREF-06, LLM-CONFIG)
- `test_preferences_page_loads` — GET /preferences returns 200 with "Preferences" heading (PREF-05).
- `test_upload_receipt` — POST /preferences/upload with mock PDF returns receipt review HTML (PREF-01).
- `test_upload_invalid_file` — POST /preferences/upload with bad file returns error (PREF-01).
- `test_preference_crud` — Full CRUD lifecycle: create, list, update, delete (PREF-05).
- `test_preference_search` — GET /preferences/list?q=X returns only matching preference (PREF-05).
- `test_bulk_delete_preferences` — POST /preferences/bulk-delete removes all specified entries (PREF-05).
- `test_nl_chat_clarify` — POST /preferences/chat with ambiguous message returns clarification question (PREF-04).
- `test_nl_chat_confirm` — POST /preferences/chat with clear intent shows Apply; /chat/apply saves to DB (PREF-04).
- `test_process_list_with_preferences` — CartService.process_list auto-loads established preferences and passes to match_products (PREF-06).
- `test_upload_receipt_uses_db_llm_config` — Receipt upload uses DB-configured provider/model (PREF-01, LLM-CONFIG).
- `test_nl_chat_uses_db_llm_config` — NL chat uses DB-configured provider/model (PREF-04, LLM-CONFIG).

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. All three test files (`tests/test_receipt_parser.py`, `tests/test_preference_service.py`, `tests/test_preferences_flow.py`) existed and passed (31/31) at backfill time.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Parsed receipt items displayed in editable table with brand/product fields | PREF-02 | HTMX partial rendering requires browser interaction — input element layout is visual | Upload a receipt PDF, verify editable inputs appear for each parsed item in the review table |
| Preference chat conversation flow is coherent | PREF-04 | Multi-turn LLM chat quality is subjective | Type "we switched to oat milk", verify clarification or confirmation appears correctly |
| Tab switching between Upload/List/Chat modes | PREF-05 | Alpine.js tab UI interaction | Click each tab, verify correct panel shows without page reload |

**Note on PREF-02:** The `test_upload_receipt` integration test in `test_preferences_flow.py` verifies that the upload endpoint returns 200 with parsed item names in the response. The editable table UI behavior (HTMX partial rendering with `<input>` elements) cannot be verified without browser rendering and remains manual-only.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify entries
- [x] Sampling continuity: all 31 tests covered
- [x] Wave 0 requirements satisfied (all test files exist)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (backfilled 2026-04-08, Phase 09 plan 01)
