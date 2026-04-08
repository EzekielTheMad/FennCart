---
phase: 2
slug: core-loop
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-03
updated: 2026-04-08
---

# Phase 2 — Validation Strategy

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
| **Quick run command** | `python -m pytest tests/test_shopping_flow.py tests/test_cart_service.py tests/test_llm_matching.py tests/test_kroger_client.py tests/test_kroger_products.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** `python -m pytest tests/test_shopping_flow.py tests/test_cart_service.py tests/test_llm_matching.py -x -q`
- **After every plan wave:** `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | SRCH-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_shopping_page_renders -x` | ✅ | ✅ green |
| 02-01-02 | 01 | 1 | SRCH-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_list_preview -x` | ✅ | ✅ green |
| 02-01-03 | 01 | 1 | SRCH-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_list_preview_empty -x` | ✅ | ✅ green |
| 02-01-04 | 01 | 1 | SRCH-02, SRCH-04 | integration | `python -m pytest tests/test_shopping_flow.py::test_match_returns_review_screen -x` | ✅ | ✅ green |
| 02-01-05 | 01 | 1 | SRCH-05 | integration | `python -m pytest tests/test_shopping_flow.py::test_review_screen_has_toggle -x` | ✅ | ✅ green |
| 02-01-06 | 01 | 1 | SRCH-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_match_empty_list_returns_error -x` | ✅ | ✅ green |
| 02-01-07 | 01 | 1 | CART-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_add_to_cart_flow -x` | ✅ | ✅ green |
| 02-01-08 | 01 | 1 | CART-01, CART-03 | integration | `python -m pytest tests/test_shopping_flow.py::test_success_screen_shows_items -x` | ✅ | ✅ green |
| 02-01-09 | 01 | 1 | CART-01 | integration | `python -m pytest tests/test_shopping_flow.py::test_add_to_cart_expired_token -x` | ✅ | ✅ green |
| 02-01-10 | 01 | 1 | QUAL-02 | integration | `python -m pytest tests/test_shopping_flow.py::test_swap_endpoint_removed -x` | ✅ | ✅ green |
| 02-01-11 | 01 | 1 | QUAL-01 | static | `python -m pytest tests/test_shopping_flow.py::test_review_screen_no_x_datastack -x` | ✅ | ✅ green |
| 02-02-01 | 02 | 1 | SRCH-04 | unit | `python -m pytest tests/test_cart_service.py::test_confidence_partitioning -x` | ✅ | ✅ green |
| 02-02-02 | 02 | 1 | SRCH-02 | unit | `python -m pytest tests/test_cart_service.py::test_process_list_calls_search_and_match -x` | ✅ | ✅ green |
| 02-02-03 | 02 | 1 | SRCH-02 | unit | `python -m pytest tests/test_cart_service.py::test_search_deduplication -x` | ✅ | ✅ green |
| 02-02-04 | 02 | 1 | CART-02 | unit | `python -m pytest tests/test_cart_service.py::test_cart_items_persisted -x` | ✅ | ✅ green |
| 02-02-05 | 02 | 1 | CART-02 | unit | `python -m pytest tests/test_cart_service.py::test_cart_items_persisted_on_failure -x` | ✅ | ✅ green |
| 02-02-06 | 02 | 1 | CART-03 | unit | `python -m pytest tests/test_cart_service.py::test_get_session_items -x` | ✅ | ✅ green |
| 02-02-07 | 02 | 1 | SRCH-02 | unit | `python -m pytest tests/test_cart_service.py::test_to_candidate_extracts_fields -x` | ✅ | ✅ green |
| 02-02-08 | 02 | 1 | SRCH-02 | unit | `python -m pytest tests/test_cart_service.py::test_to_candidate_handles_missing_fields -x` | ✅ | ✅ green |
| 02-03-01 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_parse_shopping_list_returns_parsed_items -x` | ✅ | ✅ green |
| 02-03-02 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_match_products_returns_match_result -x` | ✅ | ✅ green |
| 02-03-03 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_match_products_accepts_preferences_none -x` | ✅ | ✅ green |
| 02-03-04 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_match_products_accepts_preferences_dict -x` | ✅ | ✅ green |
| 02-03-05 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_provider_model_strings -x` | ✅ | ✅ green |
| 02-03-06 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_build_matching_prompt_format -x` | ✅ | ✅ green |
| 02-03-07 | 03 | 1 | LLM-01 | unit | `python -m pytest tests/test_llm_matching.py::test_parse_shopping_list_error_handling -x` | ✅ | ✅ green |
| 02-04-01 | 04 | 1 | SRCH-02 | unit | `python -m pytest tests/test_kroger_client.py::test_get_app_token_success -x` | ✅ | ✅ green |
| 02-04-02 | 04 | 1 | SRCH-02 | unit | `python -m pytest tests/test_kroger_client.py::test_get_app_token_invalid_creds -x` | ✅ | ✅ green |
| 02-04-03 | 04 | 1 | SRCH-02 | unit | `python -m pytest tests/test_kroger_client.py::test_search_stores_returns_formatted -x` | ✅ | ✅ green |
| 02-05-01 | 05 | 1 | SRCH-02, SRCH-03 | unit | `python -m pytest tests/test_kroger_products.py::test_search_products_uses_csp_filter -x` | ✅ | ✅ green |
| 02-05-02 | 05 | 1 | SRCH-02 | unit | `python -m pytest tests/test_kroger_products.py::test_search_products_returns_data -x` | ✅ | ✅ green |
| 02-05-03 | 05 | 1 | SRCH-02 | unit | `python -m pytest tests/test_kroger_products.py::test_search_products_handles_error -x` | ✅ | ✅ green |
| 02-05-04 | 05 | 1 | CART-01 | unit | `python -m pytest tests/test_kroger_products.py::test_add_to_cart_success_204 -x` | ✅ | ✅ green |
| 02-05-05 | 05 | 1 | CART-01 | unit | `python -m pytest tests/test_kroger_products.py::test_add_to_cart_expired_token_401 -x` | ✅ | ✅ green |
| 02-05-06 | 05 | 1 | CART-01 | unit | `python -m pytest tests/test_kroger_products.py::test_add_to_cart_uses_put_method -x` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

### Test Function Reference

**tests/test_shopping_flow.py** (11 tests — SRCH-01, SRCH-02, SRCH-04, SRCH-05, CART-01, CART-03)
- `test_shopping_page_renders` — GET /shopping returns 200 with heading and form (SRCH-01).
- `test_list_preview` — POST /shopping/preview with items returns "Parsed items" partial (SRCH-01).
- `test_list_preview_empty` — POST /shopping/preview with empty text returns empty HTML (SRCH-01).
- `test_match_returns_review_screen` — POST /shopping/match returns review_screen with both zones (SRCH-02, SRCH-04).
- `test_review_screen_has_toggle` — Review screen shows "Exceptions only / Full review" toggle with Alpine x-data (SRCH-05).
- `test_match_empty_list_returns_error` — POST /shopping/match with whitespace returns "Your list is empty" (SRCH-01).
- `test_add_to_cart_flow` — POST /shopping/add-to-cart returns "Items added to your cart" (CART-01).
- `test_success_screen_shows_items` — Success screen shows Fry's link and "Show added items" (CART-01, CART-03).
- `test_add_to_cart_expired_token` — None token returns "Session expired / Reconnect" error block (CART-01).
- `test_swap_endpoint_removed` — POST /shopping/swap returns 404/405 (QUAL-02).
- `test_review_screen_no_x_datastack` — review_screen.html has no `_x_dataStack`, has `$root.updateItem` (QUAL-01).

**tests/test_cart_service.py** (9 tests — SRCH-02, SRCH-04, CART-02, CART-03)
- `test_confidence_partitioning` — partition_matches splits at 0.8 threshold (SRCH-04).
- `test_process_list_calls_search_and_match` — process_list calls parse/search/match exactly once (SRCH-02).
- `test_search_deduplication` — Duplicate list items trigger only one search_products call (SRCH-02).
- `test_cart_items_persisted` — CartSession + CartItems saved to SQLite on Kroger success (CART-02).
- `test_cart_items_persisted_on_failure` — CartItems persisted locally even when Kroger API fails (CART-02).
- `test_get_session_items` — get_session_items returns CartSession and its CartItems (CART-03).
- `test_to_candidate_extracts_fields` — _to_candidate maps all Kroger product dict fields (SRCH-02).
- `test_to_candidate_handles_missing_fields` — _to_candidate is defensive with sparse product dicts (SRCH-02).

**tests/test_llm_matching.py** (7 tests — LLM-01)
- `test_parse_shopping_list_returns_parsed_items` — parse_shopping_list() returns typed ParsedListItems (LLM-01).
- `test_match_products_returns_match_result` — match_products() returns MatchResult with confidence scores (LLM-01).
- `test_match_products_accepts_preferences_none` — preferences=None does not error (LLM-01).
- `test_match_products_accepts_preferences_dict` — preferences dict included in system prompt (LLM-01).
- `test_provider_model_strings` — Correct litellm/ provider strings for anthropic/openai/ollama (LLM-01).
- `test_build_matching_prompt_format` — Prompt formats items/candidates, excludes thumbnail_url (LLM-01).
- `test_parse_shopping_list_error_handling` — LLM exceptions wrapped as RuntimeError (LLM-01).

**tests/test_kroger_client.py** (3 tests — SRCH-02 infrastructure)
- `test_get_app_token_success` — Client credentials grant returns token on valid credentials (SRCH-02).
- `test_get_app_token_invalid_creds` — 401 response returns error message (SRCH-02).
- `test_search_stores_returns_formatted` — Store search returns formatted store list (SRCH-02).

**tests/test_kroger_products.py** (6 tests — SRCH-02, SRCH-03, CART-01)
- `test_search_products_uses_csp_filter` — search_products passes `filter.fulfillment=csp` (SRCH-02, SRCH-03).
- `test_search_products_returns_data` — search_products returns the data array (SRCH-02).
- `test_search_products_handles_error` — HTTP 500 raises RuntimeError (SRCH-02).
- `test_add_to_cart_success_204` — add_to_cart returns (True, "Items added") on 204 (CART-01).
- `test_add_to_cart_expired_token_401` — 401 returns (False, ...) with "expired" message (CART-01).
- `test_add_to_cart_uses_put_method` — add_to_cart uses HTTP PUT to cart/add endpoint (CART-01).

---

## Wave 0 Requirements

None — existing infrastructure covers all phase requirements. All five test files (`tests/test_shopping_flow.py`, `tests/test_cart_service.py`, `tests/test_llm_matching.py`, `tests/test_kroger_client.py`, `tests/test_kroger_products.py`) existed and passed at backfill time. `tests/conftest.py` provides the async DB session, DI overrides, and ASGI test client.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Kroger cart items visible in Fry's app | CART-01 | Requires live Kroger account | Submit list, confirm adds, check Fry's curbside pickup in browser |
| LLM match quality subjective assessment | LLM-01 | Match quality is subjective | Review 5+ matched items for reasonableness of brand/size selection |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify entries
- [x] Sampling continuity: all 36 tests covered
- [x] Wave 0 requirements satisfied (all test files exist)
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (backfilled 2026-04-08, Phase 09 plan 01)
