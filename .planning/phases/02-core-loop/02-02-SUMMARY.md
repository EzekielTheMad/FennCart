---
phase: 02-core-loop
plan: 02
subsystem: llm-service
tags: [llm, instructor, litellm, product-matching, shopping-list-parsing, multi-provider]
dependency_graph:
  requires: []
  provides: [parse_shopping_list, match_products, _build_matching_prompt, app/schemas/shopping.py]
  affects: [app/services/llm_service.py, app/schemas/shopping.py]
tech_stack:
  added: []
  patterns: [instructor.from_provider with async_client=True, LiteLLM model string prefix routing, Pydantic structured output via Instructor]
key_files:
  created:
    - app/schemas/__init__.py
    - app/schemas/shopping.py
    - tests/test_llm_matching.py
  modified:
    - app/services/llm_service.py
decisions:
  - LiteLLM model string prefix (provider/model) enables multi-provider support with no code branches
  - Single batched LLM call for all items avoids N per-item API calls and matches D-08 all-at-once display
  - preferences parameter present but None-safe for Phase 3 integration (D-07)
  - Prompt excludes thumbnail_url and display-only fields to stay within token budget
metrics:
  duration: ~3 min
  completed: "2026-04-03"
  tasks_completed: 2
  files_created: 3
  files_modified: 1
---

# Phase 02 Plan 02: LLM Product Matching Summary

**One-liner:** Instructor+LiteLLM async structured output for shopping list parsing and batched Kroger product matching with multi-provider support (anthropic/openai/ollama).

## What Was Built

Extended `app/services/llm_service.py` with two async functions that form the intelligence layer of the core loop:

- `parse_shopping_list()` — converts raw natural language shopping list text into typed `ParsedListItem` objects using Instructor's structured output with LiteLLM.
- `match_products()` — selects the best Kroger product for each item from provided candidates, returns `MatchResult` with per-item confidence scores. Includes `preferences: Optional[dict] = None` parameter as the D-07 Phase 3 hook.
- `_build_matching_prompt()` — private helper that formats items and candidates into a compact prompt string, excluding display-only fields (thumbnail_url) to stay within token budget.

Created `app/schemas/shopping.py` (shared contract between plan 01 and plan 02, since this is a wave-1 parallel execution) with all five schema types: `ParsedListItem`, `ProductCandidate`, `ItemMatch`, `MatchResult`, `ConfirmedItem`.

## Tests

7 unit tests in `tests/test_llm_matching.py`, all passing, all using mocked `instructor.from_provider`:

| Test | What it validates |
|------|-------------------|
| test_parse_shopping_list_returns_parsed_items | Returns correct ParsedListItem list from mocked result |
| test_match_products_returns_match_result | Returns MatchResult with confidence scores |
| test_match_products_accepts_preferences_none | preferences=None accepted without error (D-07) |
| test_match_products_accepts_preferences_dict | preferences dict injected into system prompt |
| test_provider_model_strings | LLM-01: anthropic/openai/ollama model strings correct |
| test_build_matching_prompt_format | Prompt contains item/UPC/price, excludes thumbnail_url |
| test_parse_shopping_list_error_handling | LLM exceptions wrapped as RuntimeError |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — both functions accept real inputs and produce real structured outputs (LLM calls are real; no hardcoded return values in production code).

## Self-Check: PASSED

- app/services/llm_service.py: FOUND
- app/schemas/shopping.py: FOUND
- tests/test_llm_matching.py: FOUND
- Commit deb969e (Task 1): FOUND
- Commit b8048c6 (Task 2): FOUND
- All 13 tests pass (7 new + 6 existing)
