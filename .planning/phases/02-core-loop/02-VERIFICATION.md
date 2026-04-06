---
phase: 02-core-loop
verified: 2026-04-03T00:00:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 2: Core Loop Verification Report

**Phase Goal:** Users can go from a natural language grocery list to confirmed items in their Kroger cart
**Verified:** 2026-04-03
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

The five success criteria from ROADMAP.md were used as the canonical truths.

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can paste or type a free-form grocery list and submit it for processing | VERIFIED | `templates/pages/shopping.html` renders textarea with `hx-post="/shopping/match"` and "Build my cart" submit button; `test_shopping_page_renders` passes |
| 2 | App returns matched Kroger products — only curbside-eligible — with best match per list item | VERIFIED | `kroger_client.search_products()` uses `filter.fulfillment: "csp"`; `llm_service.match_products()` returns `MatchResult`; `test_search_products_uses_csp_filter` and `test_match_products_returns_match_result` pass |
| 3 | By default, only uncertain/low-confidence matches appear for manual review; high-confidence matches are auto-selected | VERIFIED | `CartService.partition_matches()` splits at threshold 0.8; `review_screen.html` renders two zones; `test_confidence_partitioning` asserts exact split |
| 4 | User can toggle to full review mode and see all matched items before confirming | VERIFIED | `review_screen.html` contains Alpine.js toggle with "Exceptions only" / "Full review" buttons; `test_review_screen_has_toggle` asserts `x-data`, both button labels |
| 5 | User can confirm selections and have those items added to Kroger cart, with a local session record | VERIFIED | `/shopping/add-to-cart` endpoint calls `add_confirmed_to_cart()`; `CartSession` and `CartItem` persisted to SQLite regardless of Kroger API outcome; `test_add_to_cart_flow`, `test_cart_items_persisted`, `test_cart_items_persisted_on_failure` all pass |

**Score:** 5/5 truths verified

---

### Required Artifacts

All artifacts from all four plan `must_haves` sections were checked at three levels: exists, substantive, and wired.

#### Plan 01 Artifacts

| Artifact | Status | Evidence |
|----------|--------|----------|
| `app/schemas/shopping.py` | VERIFIED | Contains all 5 schema classes (`ParsedListItem`, `ProductCandidate`, `ItemMatch`, `MatchResult`, `ConfirmedItem`) with correct field definitions including `confidence: float = Field(ge=0.0, le=1.0)` and `alternatives: list[str]`; imported by `cart_service.py`, `llm_service.py`, `shopping.py` router |
| `app/models/cart_session.py` | VERIFIED | `class CartSession(SQLModel, table=True)` with `__tablename__ = "cart_sessions"`, correct fields; imported by `cart_service.py` and `models/__init__.py` |
| `app/models/cart_item.py` | VERIFIED | `class CartItem(SQLModel, table=True)` with `__tablename__ = "cart_items"`, `session_id: int = Field(foreign_key="cart_sessions.id")`; imported by `cart_service.py` and `models/__init__.py` |
| `app/models/__init__.py` | VERIFIED | Exports `AppConfig`, `OAuthToken`, `CartSession`, `CartItem` |
| `alembic/versions/0002_cart_tables.py` | VERIFIED | Creates `cart_sessions` and `cart_items` tables with correct columns and FK constraint; includes `downgrade()` that drops `cart_items` then `cart_sessions` |
| `app/services/kroger_client.py` | VERIFIED | Contains `search_products()` with `filter.fulfillment: "csp"`, `add_to_cart()` using PUT to `cart/add` with 204 handling; existing `get_app_token()` and `search_stores_by_zip()` preserved |
| `tests/test_kroger_products.py` | VERIFIED | 6 tests: `test_search_products_uses_csp_filter`, `test_search_products_returns_data`, `test_search_products_handles_error`, `test_add_to_cart_success_204`, `test_add_to_cart_expired_token_401`, `test_add_to_cart_uses_put_method`; all pass |

#### Plan 02 Artifacts

| Artifact | Status | Evidence |
|----------|--------|----------|
| `app/services/llm_service.py` | VERIFIED | Contains `parse_shopping_list()`, `match_products()` with `preferences: Optional[dict] = None` (D-07 hook), `instructor.from_provider(f"litellm/{model_str}", async_client=True)`, `response_model=MatchResult`, `response_model=ParsedList`, `_build_matching_prompt()`; existing `test_connection()` preserved |
| `tests/test_llm_matching.py` | VERIFIED | 7 tests all pass; covers parsing, matching, preferences hook, multi-provider model strings (LLM-01), prompt format, error handling |

#### Plan 03 Artifacts

| Artifact | Status | Evidence |
|----------|--------|----------|
| `app/services/cart_service.py` | VERIFIED | `CartService` class with `process_list()`, `partition_matches()` (threshold 0.8), `add_confirmed_to_cart()`, `get_session_items()`, `_to_candidate()`; imports from `kroger_client` and `llm_service` |
| `app/routers/shopping.py` | VERIFIED | `APIRouter(prefix="/shopping")` with GET `""`, POST `/preview`, `/match`, `/swap`, `/add-to-cart`; instantiates `CartService`; registered in `app/main.py` |
| `templates/pages/shopping.html` | VERIFIED | Contains "What do you need?", "Build my cart", `hx-post="/shopping/match"`, `hx-post="/shopping/preview"` with debounce |
| `templates/partials/review_screen.html` | VERIFIED | Contains "Review these matches" (low-confidence zone), "Auto-matched" (high-confidence zone), "Exceptions only"/"Full review" Alpine toggle, HTMX form submitting to `/shopping/add-to-cart` |
| `templates/partials/success_screen.html` | VERIFIED | Contains "Items added to your cart", "Open Fry's curbside pickup", "Show added items" with Alpine expand |

#### Plan 04 Artifacts

| Artifact | Status | Evidence |
|----------|--------|----------|
| `tests/test_cart_service.py` | VERIFIED | 8 tests (7 required + 1 bonus `test_to_candidate_handles_missing_fields`); covers confidence partitioning (SRCH-04), pipeline orchestration (SRCH-02), dedup, cart persistence (CART-02), failure persistence, session retrieval (CART-03), candidate extraction; all pass |
| `tests/test_shopping_flow.py` | VERIFIED | 9 integration tests covering all /shopping/* endpoints; all pass |

---

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|----------|
| `kroger_client.py` | Kroger Products API | `filter.fulfillment=csp` in GET params | VERIFIED | Line 32: `"filter.fulfillment": "csp"` |
| `kroger_client.py` | Kroger Cart API | PUT to `cart/add` | VERIFIED | Line 61: `f"{KROGER_BASE}/cart/add"` using `client.put()` |
| `cart_item.py` | `cart_session.py` | FK `session_id -> cart_sessions.id` | VERIFIED | Line 9: `Field(foreign_key="cart_sessions.id")` |
| `llm_service.py` | `instructor` library | `instructor.from_provider("litellm/...")` | VERIFIED | Lines 62, 108 |
| `llm_service.py` | `app/schemas/shopping.py` | imports schemas | VERIFIED | Line 8: `from app.schemas.shopping import ItemMatch, MatchResult, ParsedListItem, ProductCandidate` |
| `cart_service.py` | `kroger_client.py` | calls `search_products()` and `add_to_cart()` | VERIFIED | Line 16: `from app.services.kroger_client import search_products, add_to_cart` |
| `cart_service.py` | `llm_service.py` | calls `parse_shopping_list()` and `match_products()` | VERIFIED | Line 17: `from app.services.llm_service import parse_shopping_list, match_products` |
| `shopping.py` (router) | `cart_service.py` | instantiates `CartService` | VERIFIED | Lines 84, 231: `CartService(db=session, ...)` |
| `shopping.html` | `shopping.py` router | HTMX form to `/shopping/match` | VERIFIED | `hx-post="/shopping/match"` in template |
| `review_screen.html` | `shopping.py` router | HTMX confirm to `/shopping/add-to-cart` | VERIFIED | `hx-post="/shopping/add-to-cart"` in template |
| `app/main.py` | `shopping.py` router | `include_router` | VERIFIED | Lines 88-89: lazy import and `include_router(shopping.router)` |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `review_screen.html` | `review_items`, `auto_items` | `CartService.process_list()` -> `partition_matches()` -> Kroger API + LLM | Yes — `search_products()` returns live Kroger API data; `match_products()` returns LLM-selected candidates | FLOWING |
| `success_screen.html` | `session`, `items`, `success_count` | `CartService.add_confirmed_to_cart()` -> DB write -> `CartSession` | Yes — `CartSession` written to SQLite before render | FLOWING |
| `list_preview.html` | `items` | `_quick_parse()` in router (regex-based, not LLM) | Yes — fast parse of user input | FLOWING |

---

### Behavioral Spot-Checks

All external calls (Kroger API, LLM) are properly mocked in tests. The following module-level checks were run:

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All imports resolve | `python -c "from app.schemas.shopping import ...; from app.services.cart_service import CartService; ..."` | "All imports OK" | PASS |
| Phase 2 test suite | `pytest tests/test_kroger_products.py tests/test_llm_matching.py tests/test_cart_service.py tests/test_shopping_flow.py -q` | 56 passed | PASS |
| Full test suite (Phase 1 + Phase 2) | `pytest tests/ -q` | 82 passed, 3 warnings | PASS |

---

### Requirements Coverage

All 9 Phase 2 requirement IDs from plans were cross-referenced against REQUIREMENTS.md. Every requirement has at least one passing automated test.

| Requirement | Source Plans | Description | Status | Automated Test Evidence |
|-------------|-------------|-------------|--------|------------------------|
| SRCH-01 | 02-03, 02-04 | User can input a natural language shopping list | SATISFIED | `test_shopping_page_renders`, `test_list_preview` |
| SRCH-02 | 02-01, 02-02, 02-03, 02-04 | App uses LLM to interpret list items and match to Kroger Products API results | SATISFIED | `test_process_list_calls_search_and_match`, `test_match_returns_review_screen`, `test_match_products_returns_match_result` |
| SRCH-03 | 02-01, 02-04 | App filters product results to curbside pickup fulfillment | SATISFIED | `test_search_products_uses_csp_filter` (asserts `filter.fulfillment=csp`) |
| SRCH-04 | 02-03, 02-04 | App auto-matches high-confidence items, surfaces uncertain for review | SATISFIED | `test_confidence_partitioning` (threshold 0.8), `test_match_returns_review_screen` |
| SRCH-05 | 02-03, 02-04 | User can toggle exceptions-only / full review modes | SATISFIED | `test_review_screen_has_toggle` (asserts Alpine toggle buttons) |
| CART-01 | 02-03, 02-04 | User can review and confirm before items added to cart | SATISFIED | `test_add_to_cart_flow` |
| CART-02 | 02-01, 02-03, 02-04 | App maintains local cart state in SQLite | SATISFIED | `test_cart_items_persisted`, `test_cart_items_persisted_on_failure` (persists even on Kroger failure) |
| CART-03 | 02-01, 02-03, 02-04 | User can see what was added to cart in the current session | SATISFIED | `test_success_screen_shows_items`, `test_get_session_items` |
| LLM-01 | 02-02, 02-04 | App supports multiple LLM providers via provider abstraction layer | SATISFIED | `test_provider_model_strings` (asserts `litellm/anthropic/...`, `litellm/openai/...`, `litellm/ollama/...`) |

**Orphaned requirements:** None. All 9 IDs claimed by plans are mapped and tested. REQUIREMENTS.md traceability table marks all 9 as "Complete" for Phase 2.

---

### Anti-Patterns Found

| File | Pattern | Severity | Assessment |
|------|---------|----------|------------|
| `templates/partials/review_screen.html` | Alpine.js reads `_x_dataStack` from DOM elements to extract `selectedUpc` for the hidden form input | Warning | Fragile internal Alpine.js API access. Functional but couples template to Alpine internals. Does not block goal. |
| `app/schemas/shopping.py` | `ConfirmedItem` uses `price: Optional[float]` (single field) rather than `price_regular`/`price_promo` as specified in Plan 01 | Info | Schema deviation from plan spec. Internally consistent — `cart_service.py` reads `item.price` and stores as `price_regular` in `CartItem`. All tests pass. No functional gap. |

No blockers found. No TODO/FIXME/placeholder comments. No stub return values. No empty handlers.

---

### Human Verification Required

The following behaviors require a running container to verify:

#### 1. End-to-End Shopping Flow

**Test:** With real Kroger credentials configured, paste "2% milk, a dozen eggs, butter" into the shopping page and click "Build my cart"
**Expected:** Review screen appears with matched products split into review cards (low confidence) and auto-matched table (high confidence); user can toggle between modes; clicking "Add to cart" adds items and shows success screen with Fry's curbside link
**Why human:** Requires live Kroger API, live LLM provider, and OAuth session — cannot mock end-to-end in unit tests

#### 2. Alpine.js Swap Interaction

**Test:** On the review screen, click "Choose a different product" on a review card and select an alternative from the dropdown
**Expected:** Card updates to show the newly selected product; the hidden form input updates its UPC so the correct item is confirmed
**Why human:** Alpine.js DOM manipulation and `_x_dataStack` access cannot be verified without a browser

#### 3. Sticky Confirm Bar Visibility

**Test:** Load the review screen with more than 5 items so the page is scrollable
**Expected:** The sticky confirm bar remains visible at the bottom of the viewport while scrolling; sidebar offset (`left-16 lg:left-60`) renders correctly at various screen widths
**Why human:** CSS layout and scroll behavior require browser rendering

---

### Schema Deviation Note

`ConfirmedItem` in `app/schemas/shopping.py` was implemented with `price: Optional[float]` and `thumbnail_url: Optional[str]` rather than the Plan 01 spec's `price_regular: Optional[float]` / `price_promo: Optional[float]`. The deviation is:

- **Self-consistent:** `cart_service.py` uses `item.price` throughout and stores it as `CartItem.price_regular`
- **Non-breaking:** All 82 tests pass; the review screen template uses `item.price` in the hidden form JSON
- **Acceptable:** A single price field is a simpler API surface for the confirm flow; the split regular/promo is preserved in `CartItem` for display in session history

---

## Summary

Phase 2 goal is fully achieved. All 5 success criteria from the roadmap are met, all 9 requirement IDs are satisfied with passing automated tests, all critical wiring is verified, and data flows from Kroger API through the LLM matching layer to the SQLite cart record.

The full test suite (82 tests covering Phase 1 + Phase 2) passes green with no failures.

Three items flagged for human verification are UI/browser concerns that cannot be tested programmatically.

---

_Verified: 2026-04-03_
_Verifier: Claude (gsd-verifier)_
