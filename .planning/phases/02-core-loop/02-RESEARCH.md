# Phase 02: Core Loop - Research

**Researched:** 2026-04-03
**Domain:** Kroger Products API + Cart API, LiteLLM + Instructor structured output, HTMX multi-step flows, SQLite cart session persistence
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Smart textarea with live preview — user types or pastes free-form text in a textarea. As they type, a live preview below the textarea parses lines into structured items (name, quantity, notes) using HTMX partial updates.
- **D-02:** No list persistence — the textarea starts fresh every visit. No session storage, no database persistence of the raw list text.
- **D-03:** Hybrid cards/table layout — items needing review (low confidence) display as product cards with image, name, size, price. Auto-matched high-confidence items display as compact table rows.
- **D-04:** Confidence hidden unless low — don't show confidence scores on high-confidence matches. Only flag uncertain ones with a warning indicator.
- **D-05:** Dropdown swap for alternatives — when an item has multiple possible matches, clicking the matched product shows a dropdown of 3-5 alternatives. User picks one to swap it in. HTMX partial swap on selection.
- **D-06:** Success screen shows summary by default (item count, estimated total) with a direct link to Fry's curbside pickup. Expandable to full item list with product name, quantity, and price.
- **D-07:** Ambiguous items use preference profile if available (Phase 3 delivers this), otherwise LLM best-guesses and flags as low confidence for review. The matching function signature must accept optional preference context from the start.
- **D-08:** Results displayed all at once after the full list is processed. User waits for complete results rather than seeing streaming per-item updates.

### Claude's Discretion

- Quantity/unit parsing approach — LLM-only vs regex pre-parse. Claude picks what works best with Instructor structured output.
- Empty/short list handling — Claude picks the UX pattern (inline error vs helpful empty state).
- Cart confirmation flow details — one-click vs checkbox select, progress indicator style.
- Error handling for failed cart additions — retry vs report pattern.
- Exceptions-only vs full review toggle UX — switch vs tabs vs other.
- Number of Kroger product results per search (5 vs 10 vs dynamic).
- LLM call strategy — single batch vs per-item. Claude picks based on cost, resilience, and the all-at-once display decision.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SRCH-01 | User can input a natural language shopping list (paste, type, free-form text) | D-01 textarea with HTMX live preview; shopping.html page replacement pattern |
| SRCH-02 | App uses LLM to interpret list items and match them to Kroger Products API results | Instructor + LiteLLM async structured output; match_products() function extension of llm_service.py |
| SRCH-03 | App filters product results to items available for curbside pickup fulfillment | Kroger Products API `filter.fulfillment=csp` parameter confirmed; filter in search_products() |
| SRCH-04 | App auto-matches high-confidence items and surfaces uncertain matches for review | ProductMatch Pydantic model with confidence field; partition logic in cart service |
| SRCH-05 | User can toggle between exceptions-only and full review modes | Alpine.js toggle; HTMX swap on toggle or client-side show/hide |
| CART-01 | User can review matched products and explicitly confirm before items are added to Kroger cart | Review screen with sticky confirm bar; POST /shopping/add-to-cart endpoint |
| CART-02 | App maintains local cart state in SQLite (product, quantity, price, timestamp) | CartSession + CartItem SQLModel models; Alembic migration 0002 |
| CART-03 | User can see what was added to cart in the current session | Success screen expandable detail; CartItem query by session |
| LLM-01 | App supports multiple LLM providers (Claude, OpenAI, local via Ollama) through provider abstraction | LiteLLM model string pattern already in llm_service.py; Instructor wraps it uniformly |
</phase_requirements>

---

## Summary

Phase 2 builds the complete list-to-cart pipeline by extending three existing services (`kroger_client.py`, `llm_service.py`), adding a new `CartService`, two new SQLModel tables (`CartSession`, `CartItem`), a new Alembic migration, new router endpoints under `/shopping/`, and replacing the placeholder `shopping.html` with the full multi-screen flow.

The core architectural question for this phase is LLM call strategy. Given D-08 (all-at-once results), a single batched LLM call across all shopping list items is the correct approach — it avoids N separate API calls, reduces latency, and stays within a reasonable token budget for typical grocery lists (10-50 items). The LLM receives: (1) the parsed list items, (2) a dict of `{list_item: [candidate_products]}` from Kroger search results, and (3) optional preference context (None in Phase 2). It returns a `MatchResult` Pydantic model via Instructor with per-item selections and confidence scores.

The Kroger Products API fulfillment filter uses the value `csp` (curbside) — confirmed via reference implementations. The Cart API endpoint is `PUT /v1/cart/add` with JSON body `{"items": [{"upc": "...", "quantity": N}]}`. Both extend the existing `kroger_client.py` module cleanly.

**Primary recommendation:** Build in this order — (1) SQLModel models + Alembic migration, (2) `search_products()` in kroger_client, (3) `match_products()` in llm_service with Instructor, (4) CartService orchestration layer, (5) router + templates, (6) tests.

---

## Standard Stack

### Core (already installed — no new packages needed)

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| LiteLLM | 1.83.0 | Multi-provider LLM API | Already in requirements.txt; provides unified async interface |
| Instructor | 1.14.5 | Structured LLM outputs | Already in requirements.txt; wraps LiteLLM calls to return Pydantic models |
| HTTPX | 0.28.1 | Kroger API HTTP calls | Already used in kroger_client.py |
| SQLModel | 0.0.37 | ORM for cart tables | Already used; CartSession and CartItem extend existing pattern |
| aiosqlite | 0.22.1 | Async SQLite driver | Already configured |
| Alembic | 1.18.4 | Schema migration for new tables | Already configured; new migration file needed |
| HTMX | 1.9.12 (CDN) | Multi-step shopping flow UI | Already loaded in base.html |
| Alpine.js | 3.14.8 (CDN) | Review mode toggle, swap dropdown | Already loaded in base.html |
| Jinja2 | FastAPI dep | Server-side templates | All new screens are Jinja2 templates extending base.html |

**No new packages required for Phase 2.** All dependencies are already installed.

### Version verification

```bash
# Already confirmed in requirements.txt — no npm view needed (Python-only phase)
python -c "import instructor; print(instructor.__version__)"  # 1.14.4 installed (close to 1.14.5)
python -c "import litellm; print(litellm.__version__)"       # 1.83.0 target
```

Note: Instructor 1.14.4 is installed (one patch behind 1.14.5). This is not a blocking issue — the async `from_provider` pattern works identically in both.

---

## Architecture Patterns

### Recommended Project Structure (new files for Phase 2)

```
app/
├── models/
│   ├── cart_session.py     # CartSession SQLModel table
│   └── cart_item.py        # CartItem SQLModel table
├── routers/
│   └── shopping.py         # /shopping/* endpoints (list submit, match, add-to-cart)
├── services/
│   ├── kroger_client.py    # EXTEND: add search_products(), add_to_cart()
│   ├── llm_service.py      # EXTEND: add match_products() with Instructor
│   └── cart_service.py     # NEW: orchestrates the full pipeline
templates/
├── pages/
│   └── shopping.html       # REPLACE placeholder with full input form
├── partials/
│   ├── list_preview.html   # HTMX partial: parsed item pills
│   ├── review_screen.html  # HTMX partial: hybrid cards + table
│   └── success_screen.html # HTMX partial: post-add confirmation
alembic/versions/
│   └── 0002_cart_tables.py # CartSession + CartItem migration
tests/
│   ├── test_kroger_products.py   # search_products(), add_to_cart() unit tests
│   ├── test_llm_matching.py      # match_products() unit tests (mocked LLM)
│   ├── test_cart_service.py      # CartService pipeline tests
│   └── test_shopping_flow.py     # HTTP integration tests for /shopping/* routes
```

### Pattern 1: Kroger Products API — search_products()

**What:** Async function in `kroger_client.py` that searches products filtered to a store and curbside fulfillment.

**Key parameter:** `filter.fulfillment=csp` — the confirmed API value for curbside pickup. Not `curbside` (English name), not `CSP` — exactly `csp` (lowercase).

**When to use:** Once per shopping list item during the match pipeline.

**Example:**
```python
# Source: CupOfOwls/kroger-api reference implementation, jtbricker/python-kroger-client
async def search_products(
    term: str,
    location_id: str,
    limit: int = 10,
) -> list[dict]:
    """Search Kroger Products API filtered to curbside pickup.

    Uses client credentials grant (not user OAuth) per API design —
    Products API requires product.compact scope, not cart.basic:write.
    Returns raw product dicts from API; caller decides what to persist.
    DO NOT write results to SQLite (Kroger TOS — no product database).
    """
    app_token = await _get_client_credentials_token()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{KROGER_BASE}/products",
            params={
                "filter.term": term,
                "filter.locationId": location_id,
                "filter.fulfillment": "csp",  # curbside pickup
                "filter.limit": limit,
            },
            headers={"Authorization": f"Bearer {app_token}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("data", [])
```

**Product response shape** (confirmed via jtbricker/python-kroger-client sample data):
```python
{
    "productId": "0001111041600",
    "upc": "0001111041600",
    "brand": "Kroger",
    "description": "Kroger Whole Milk",
    "categories": ["Dairy"],
    "items": [
        {
            "itemId": "...",
            "size": "1/2 gal",
            "soldBy": "Unit",
            "price": {
                "regular": 3.49,
                "promo": 2.99  # or null
            }
        }
    ],
    "images": [
        {
            "perspective": "front",
            "sizes": [
                {"size": "thumbnail", "url": "https://..."},
                {"size": "medium", "url": "https://..."},
            ]
        }
    ],
    "fulfillment": {
        "curbside": True,
        "delivery": True,
        "inStore": True,
        "shipToHome": False
    }
}
```

Note: The fulfillment field in the *response* uses boolean `curbside` (camelCase in the response object), while the *request* filter parameter uses `csp`. These are different representations.

### Pattern 2: Kroger Cart API — add_to_cart()

**What:** Async function in `kroger_client.py` that adds confirmed items to the user's authenticated cart.

**Endpoint:** `PUT https://api.kroger.com/v1/cart/add`
**Auth:** Requires user OAuth access token (NOT client credentials). Use `get_valid_access_token(db)` from `oauth_manager.py`.

**Example:**
```python
# Source: CupOfOwls/kroger-api cart.py
async def add_to_cart(
    items: list[dict],  # [{"upc": "...", "quantity": 1}, ...]
    access_token: str,
) -> tuple[bool, str]:
    """Add items to user's Kroger cart. Each item must have upc and quantity.

    Cart API is add-only. This function never removes or reads cart contents.
    Caller is responsible for updating local cart shadow after success.
    Handles token refresh via retry on 401 (caller should pass fresh token).
    """
    async with httpx.AsyncClient() as client:
        resp = await client.put(
            f"{KROGER_BASE}/cart/add",
            json={"items": items},
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            timeout=15.0,
        )
        if resp.status_code == 204:  # Kroger returns 204 No Content on success
            return True, "Items added"
        resp.raise_for_status()
        return True, "Items added"
```

**Important:** The Cart API returns HTTP 204 No Content on success — not 200. Raise-for-status is the right error handling pattern; successful adds produce no response body.

### Pattern 3: Instructor + LiteLLM for Product Matching

**What:** Extend `llm_service.py` with `match_products()` that uses Instructor's async `from_provider` pattern to return validated Pydantic models.

**When to use:** Once per shopping session, passing all list items and their Kroger candidates together (batched, not per-item).

**Pydantic models for structured output:**
```python
from pydantic import BaseModel, Field
from typing import Optional

class ProductCandidate(BaseModel):
    """A Kroger product candidate for an item."""
    upc: str
    description: str
    brand: str
    size: str
    price_regular: Optional[float] = None
    price_promo: Optional[float] = None
    thumbnail_url: Optional[str] = None

class ItemMatch(BaseModel):
    """LLM's match decision for one shopping list item."""
    list_item: str               # Original text from the user's list
    selected_upc: str            # UPC of best match
    selected_description: str    # Product name for display
    confidence: float            # 0.0-1.0; >= 0.8 is auto-match threshold
    reasoning: str               # Brief LLM explanation (for debugging)
    alternatives: list[str]      # UPCs of 3-5 alternatives (for swap dropdown)

class MatchResult(BaseModel):
    """Complete match result for all items in a shopping list."""
    matches: list[ItemMatch]

class ParsedListItem(BaseModel):
    """A structured item parsed from raw shopping list text."""
    name: str                          # e.g., "milk"
    quantity: int = Field(default=1)   # e.g., 2
    unit: Optional[str] = None         # e.g., "gallons"
    notes: Optional[str] = None        # e.g., "2% fat", "that pasta Jen likes"
```

**Async Instructor usage (confirmed API from useinstructor.com):**
```python
# Source: https://python.useinstructor.com/integrations/litellm/
import instructor

async def match_products(
    list_items: list[ParsedListItem],
    candidates: dict[str, list[ProductCandidate]],  # {list_item_name: [candidates]}
    preferences: Optional[dict] = None,  # Phase 3 hook — pass None in Phase 2
    model: str = "anthropic/claude-3-haiku-20240307",
    api_key: Optional[str] = None,
) -> MatchResult:
    client = instructor.from_provider(
        f"litellm/{model}",
        async_client=True,
    )
    # Build prompt condensing all items + candidates
    system = "You are a grocery product matching assistant..."
    user_msg = _build_matching_prompt(list_items, candidates, preferences)

    return await client.create(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
        response_model=MatchResult,
        max_tokens=2000,  # Sufficient for 50-item match result
        max_retries=2,    # Instructor retries on validation failure
    )
```

**Note on `from_provider` with LiteLLM:** The model string passed to `instructor.from_provider` must include the `litellm/` prefix. The underlying model string (e.g., `anthropic/claude-3-haiku-20240307`) is passed as the second segment. The `api_key` is set via `litellm.api_key` or environment variables that LiteLLM reads automatically — this integrates with the existing `AppConfig.llm_provider` + `AppConfig.llm_model` fields.

### Pattern 4: CartService Orchestration

**What:** New `app/services/cart_service.py` orchestrates the full pipeline. Routers call CartService; CartService calls kroger_client, llm_service, and the DB.

**Design constraint from D-07:** `match_products()` accepts `preferences=None` now, ready for Phase 3.

```python
class CartService:
    def __init__(
        self,
        db: AsyncSession,
        location_id: str,
        llm_model: str,
        llm_api_key: str,
    ):
        self.db = db
        self.location_id = location_id
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

    async def process_list(
        self,
        raw_list: str,
        preferences: Optional[dict] = None,  # Phase 3 hook
    ) -> MatchResult:
        """Parse raw text → search Kroger → LLM match. Returns MatchResult for review screen."""
        parsed_items = _parse_list(raw_list)  # LLM or regex; no persistence

        # Search Kroger for each item (in-memory only — no DB write, TOS)
        candidates = {}
        for item in parsed_items:
            products = await search_products(item.name, self.location_id, limit=10)
            candidates[item.name] = [_to_candidate(p) for p in products]

        return await match_products(parsed_items, candidates, preferences, ...)

    async def add_confirmed_items(
        self,
        confirmed: list[ConfirmedItem],  # user-selected, post-review
        access_token: str,
    ) -> tuple[int, int, str]:
        """Add confirmed items to Kroger cart. Returns (success_count, fail_count, session_id)."""
        session = CartSession(...)
        self.db.add(session)
        await self.db.flush()

        cart_items = [{"upc": i.upc, "quantity": i.quantity} for i in confirmed]
        success, msg = await add_to_cart(cart_items, access_token)

        for item in confirmed:
            cart_item = CartItem(
                session_id=session.id,
                upc=item.upc,
                description=item.description,
                quantity=item.quantity,
                price_regular=item.price_regular,
            )
            self.db.add(cart_item)
        await self.db.commit()
        return len(confirmed), 0, str(session.id)
```

### Pattern 5: SQLModel Tables for Cart State

**What:** Two new tables providing the local cart shadow required by CART-02 (TOS — Cart API is add-only).

```python
# app/models/cart_session.py
class CartSession(SQLModel, table=True):
    __tablename__ = "cart_sessions"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    item_count: int = Field(default=0)
    estimated_total: Optional[float] = None

# app/models/cart_item.py
class CartItem(SQLModel, table=True):
    __tablename__ = "cart_items"
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="cart_sessions.id")
    upc: str
    description: str
    brand: Optional[str] = None
    size: Optional[str] = None
    quantity: int = Field(default=1)
    price_regular: Optional[float] = None
    price_promo: Optional[float] = None
    added_at: datetime = Field(default_factory=datetime.utcnow)
```

**No expires_at TTL needed:** Cart items are user-initiated actions (confirmed adds), not search/API cache data. User-initiated cart records are TOS-compliant for durable storage per ARCHITECTURE.md. Raw search terms are never persisted.

### Pattern 6: HTMX Multi-Screen Flow

**What:** The shopping page uses a single `#shopping-content` div that HTMX swaps through three states: input form → review screen → success screen.

**HTMX swap targets:**
- List preview partial: `hx-target="#list-preview"`, `hx-swap="innerHTML"`, triggered on textarea `hx-trigger="input delay:400ms"`
- Full match result: `hx-target="#shopping-content"`, `hx-swap="innerHTML"`, triggered on form submit
- Cart add result: `hx-target="#shopping-content"`, `hx-swap="innerHTML"`, triggered on confirm button

**Loading states:** Since D-08 requires all-at-once display, the "Matching your items..." spinner is served as the immediate HTMX response (fast template render), with the actual match result returned after the async pipeline completes. Use `hx-indicator` on the submit button for the processing state.

**Review mode toggle (SRCH-05):** Implement client-side with Alpine.js `x-data="{ mode: 'exceptions' }"` — toggling mode just shows/hides the pre-rendered zones, no HTMX round-trip needed. Both zones are rendered server-side in the initial response; Alpine.js controls visibility.

### Anti-Patterns to Avoid

- **LLM generating product names instead of ranking real results:** The LLM receives actual Kroger API candidates and selects/ranks among them. It never invents product UPCs or names. This is Pitfall 13 from PITFALLS.md.
- **Persisting raw search queries to SQLite:** Raw shopping list text must NOT be written to the DB. In-memory only during the request. Only confirmed `CartItem` records (user-initiated) are persisted. This is Pitfall 3 / ARCHITECTURE.md anti-pattern 1.
- **Per-item LLM calls:** Batching all items in one call is required by D-08 and confirmed by ARCHITECTURE.md anti-pattern 3. Do not call the LLM once per list item.
- **Re-using client credentials token for Cart API:** The Cart API requires user OAuth access token (cart.basic:write scope). Client credentials token (product.compact scope) will return 401 on cart operations. Always call `get_valid_access_token(db)` from `oauth_manager.py` for cart adds.
- **Not handling Kroger 204 as success:** Cart API returns 204 No Content on success. Do not interpret absence of a JSON body as an error.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Structured LLM output validation | Custom JSON parsing + retry logic | Instructor `client.create(response_model=...)` | Instructor handles schema validation, automatic retry on parse failure, provider normalization |
| Multi-provider LLM switching | Provider-specific if/else branches | LiteLLM model string `"anthropic/claude-3-haiku-20240307"` | One unified API; provider is config, not code |
| OAuth token lifecycle | Manual expiry check + refresh | `get_valid_access_token(db)` from oauth_manager.py | Already built in Phase 1; proactive 60s-before-expiry refresh |
| Kroger Auth (client credentials) | Raw HTTPX auth calls | `get_app_token()` in kroger_client.py | Already built in Phase 1 |
| DB migrations | Manual ALTER TABLE | Alembic `alembic revision --autogenerate` | Already configured; autogenerates from SQLModel metadata |
| Async SQLite | Bare sqlite3 in async context | aiosqlite + SQLModel async session | Already wired in database.py with WAL mode |

**Key insight:** Phase 1 built substantial infrastructure (auth, DB, token management) that Phase 2 extends. New code is the Kroger product search, LLM matching, and cart session persistence — not rebuilding infrastructure.

---

## Common Pitfalls

### Pitfall 1: Wrong Fulfillment Filter Value

**What goes wrong:** Using `"curbside"` (English label from FennCartPitch.md) instead of `"csp"` as the `filter.fulfillment` parameter value. The Kroger API silently returns all products without filtering, so tests may still pass but curbside filtering is broken.

**Why it happens:** FennCartPitch.md describes the field as "curbside" in human-readable terms, but the API accepts the code `csp`.

**How to avoid:** Use `"filter.fulfillment": "csp"` in the httpx params dict. Verify in tests by asserting the mock was called with `csp`.

**Warning signs:** Products with `fulfillment.curbside: False` appearing in results.

**Confidence:** HIGH — confirmed via jtbricker/python-kroger-client README (default=`'csp'`) and multiple reference implementations.

### Pitfall 2: Client Credentials vs. User OAuth Token Scope Confusion

**What goes wrong:** Calling the Cart API with the client credentials token (product.compact scope). Returns 401. Alternatively, calling the Products API with the user OAuth token — this works but is unnecessary and risks leaking the user token.

**Why it happens:** Two different auth flows exist and both produce access tokens.

**How to avoid:**
- Products API: use `get_app_token()` (client credentials, `product.compact` scope)
- Cart API: use `get_valid_access_token(db)` (user OAuth, `cart.basic:write` scope)
- Never swap these.

### Pitfall 3: Cart API Returns 204 — Don't Treat as Error

**What goes wrong:** Code calls `resp.raise_for_status()` after a successful cart add, which does not raise (204 is not an error). But if code checks `resp.json()` expecting a confirmation body, it throws `JSONDecodeError` or similar.

**How to avoid:** Check `resp.status_code == 204` as the success condition. Do not parse a response body from cart add calls.

### Pitfall 4: Instructor `from_provider` Model String Format

**What goes wrong:** Passing `"anthropic/claude-3-haiku-20240307"` directly to `instructor.from_provider` instead of `"litellm/anthropic/claude-3-haiku-20240307"`. Results in a provider not found error.

**How to avoid:** The pattern is `instructor.from_provider("litellm/{full_model_string}", async_client=True)`. The `litellm/` prefix is mandatory.

**Confidence:** MEDIUM — confirmed via useinstructor.com integration docs for the `from_provider` pattern, but exact string format should be tested in Wave 0 spike.

### Pitfall 5: Token Expiry Mid-Cart-Add (Pitfall 10 from PITFALLS.md)

**What goes wrong:** User spends more than 30 minutes on the review screen. When they click "Add to cart", the access token is expired. The `get_valid_access_token(db)` call in oauth_manager.py handles proactive refresh, but if the refresh itself fails (network error, expired refresh token), cart adds fail silently.

**How to avoid:** In the cart add router, check for `None` return from `get_valid_access_token(db)` and serve the "session expired" error banner (per UI-SPEC error patterns). Never proceed to cart add with a None token.

### Pitfall 6: LLM Prompt Token Budget for Large Lists

**What goes wrong:** A 50-item list with 10 candidates per item = 500 product descriptions in the prompt. At ~30 tokens each, that's ~15,000 input tokens plus system prompt. Some models have context window limits; all models charge for input tokens.

**How to avoid:** Trim each candidate to essential fields only: `description`, `brand`, `size`, `price_regular`, `upc`. Skip full image URLs, category arrays, aisle data in the LLM prompt (keep those in memory for display). Set `max_tokens=2000` on the output (sufficient for MatchResult with 50 items). Log token counts during development.

### Pitfall 7: Products Never Persisted — No In-Memory Cache Between List Items

**What goes wrong:** search_products() is called per list item in a loop. Each call is independent (no caching). If the same search term appears twice (e.g., "milk" and "whole milk"), two API calls fire.

**How to avoid:** In CartService.process_list(), use a simple in-memory dict keyed on search term to deduplicate within a single session. This is not persistent caching (TOS-safe) — just dict deduplication within one request.

---

## Code Examples

### Async Instructor with LiteLLM (verified pattern)

```python
# Source: https://python.useinstructor.com/integrations/litellm/
import instructor

client = instructor.from_provider(
    "litellm/anthropic/claude-3-haiku-20240307",
    async_client=True,
)

match_result = await client.create(
    messages=[{"role": "user", "content": prompt}],
    response_model=MatchResult,
    max_tokens=2000,
    max_retries=2,
)
# match_result is a fully validated MatchResult Pydantic instance
```

### HTMX Debounced Live Preview

```html
<!-- In shopping.html -->
<textarea
    name="list_text"
    hx-post="/shopping/preview"
    hx-target="#list-preview"
    hx-swap="innerHTML"
    hx-trigger="input delay:400ms"
    class="bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-base p-4 w-full min-h-[160px] resize-y"
    placeholder="milk, 2%&#10;eggs, a dozen&#10;that pasta Jen likes"
></textarea>
<div id="list-preview"></div>
```

### Alpine.js Review Mode Toggle (SRCH-05)

```html
<!-- In review_screen.html partial -->
<div x-data="{ mode: 'exceptions' }">
    <!-- Toggle pill -->
    <div class="flex items-center gap-3 mb-6">
        <span class="text-sm text-slate-400">Review mode:</span>
        <div class="bg-slate-800 rounded-full p-1 flex gap-1">
            <button @click="mode = 'exceptions'"
                    :class="mode === 'exceptions' ? 'bg-slate-600 text-slate-100' : 'text-slate-400 hover:text-slate-100'"
                    class="text-sm px-3 py-1 rounded-full min-h-[44px]">Exceptions only</button>
            <button @click="mode = 'full'"
                    :class="mode === 'full' ? 'bg-slate-600 text-slate-100' : 'text-slate-400 hover:text-slate-100'"
                    class="text-sm px-3 py-1 rounded-full min-h-[44px]">Full review</button>
        </div>
    </div>
    <!-- Review cards zone (always visible unless mode=full showing only auto-matched) -->
    <div x-show="true"><!-- low confidence items --></div>
    <!-- Auto-matched zone: in exceptions mode show as compact table; in full review show as cards -->
    <div x-show="true"><!-- auto-matched items --></div>
</div>
```

### Alembic Migration for Cart Tables

```python
# alembic/versions/0002_cart_tables.py
def upgrade() -> None:
    op.create_table(
        "cart_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estimated_total", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("upc", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("size", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price_regular", sa.Float(), nullable=True),
        sa.Column("price_promo", sa.Float(), nullable=True),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["cart_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `instructor.patch(client)` | `instructor.from_provider("litellm/...", async_client=True)` | Instructor 1.x migration | The `patch()` API is deprecated; `from_provider` is the current async pattern |
| Manual JSON parsing of LLM output | `response_model=PydanticModel` via Instructor | Instructor 0.x → 1.x | Eliminates fragile json.loads(); automatic validation + retry |
| Raw `litellm.acompletion()` for structured output | Instructor-wrapped | Ongoing | LiteLLM `response_format` works but lacks retry-on-validation-failure |

**Deprecated/outdated:**
- `instructor.patch()`: Replaced by `instructor.from_provider()` in Instructor 1.x. Do not use.
- `litellm.completion()` (sync): All Phase 2 code is async; use `litellm.acompletion()` or Instructor's async client.

---

## Open Questions

1. **Instructor `from_provider` model string format with LiteLLM**
   - What we know: Pattern is `"litellm/{model_string}"` per official docs
   - What's unclear: Whether the full LiteLLM model string (e.g., `litellm/anthropic/claude-3-haiku-20240307`) works correctly with the locally installed Instructor 1.14.4
   - Recommendation: Include a Wave 0 integration spike test — `test_instructor_litellm_async.py` — that makes a real or mocked call to verify the string format before building the full matching pipeline.

2. **Kroger Products API `filter.limit` max value**
   - What we know: Default in reference implementations is 5; 10 is commonly used
   - What's unclear: Whether the API enforces a hard cap (some Kroger endpoints cap at 10, others at 50)
   - Recommendation: Default to 10 in code; handle gracefully if fewer are returned. The Kroger API docs are JS-rendered and not fully accessible.

3. **LLM parsing vs. regex for shopping list items**
   - What we know: This is Claude's discretion per CONTEXT.md
   - Recommendation: Use LLM (Instructor) for parsing too — a single pre-pass `ParsedListItem` extraction before searching. This handles "that pasta Jen likes", "a dozen eggs", "the same coffee as last time" far better than regex. Cost is negligible (one small call per session for just the parsing step). Build `ParsedListItem` as a separate Instructor call with a lightweight model.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|---------|
| Python 3.12 | Runtime | Check env | — | — |
| pytest + anyio | Test suite | Via requirements.txt | — | — |
| instructor | LLM matching | Installed (1.14.4) | 1.14.4 | None needed — 1.14.4 is functionally identical to 1.14.5 for this use case |
| litellm | LLM calls | In requirements.txt | 1.83.0 target | — |
| Kroger API | Products + Cart | BYO credentials | — | Mocked in tests |
| LLM provider | Product matching | BYO API key | — | Mocked in tests (Instructor supports mock injection) |

**Missing dependencies with no fallback:** None — all runtime dependencies are already in requirements.txt. LLM provider and Kroger credentials are BYO per project design; tests mock these.

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 2 |
|-----------|------------------|
| FastAPI 0.135.3 + HTMX + Jinja2 SSR | All new routes are FastAPI routers; all UI is Jinja2 templates extending base.html |
| LiteLLM 1.83.0 + Instructor 1.14.5 | Product matching uses Instructor `from_provider("litellm/...", async_client=True)` |
| SQLModel + aiosqlite + Alembic | New CartSession + CartItem tables need Alembic migration 0002 |
| `--workers 1` for Uvicorn | No change; already enforced |
| `PRAGMA journal_mode=WAL` + `PRAGMA busy_timeout=5000` | Already configured in database.py init_db(); no action needed |
| Customer search data must not be persisted | Raw shopping list text stays in-memory only; only CartItem records (confirmed user actions) go to SQLite |
| Products API results must never be written to a durable SQLite table | Candidates dict is in-memory only during the request-response cycle |
| Cart API is add-only; maintain local SQLite shadow | CartSession + CartItem tables fulfill this requirement |
| No default values for Kroger credentials | Already enforced in Phase 1 config |
| All new templates extend base.html | shopping.html and all partials use `{% extends "base.html" %}` |
| Tailwind via CDN (development) | Use only declared token classes from 02-UI-SPEC.md |
| Heroicons via inline SVG | Use for any icons in new templates |
| GSD workflow enforcement | Phase work runs through /gsd:execute-phase |

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest with anyio (async support) |
| Config file | `pytest.ini` — `asyncio_mode = auto`, `anyio_backends = asyncio` |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRCH-01 | Textarea submit sends list to /shopping/preview and /shopping/match | integration | `pytest tests/test_shopping_flow.py::test_list_preview -x` | Wave 0 |
| SRCH-02 | match_products() returns MatchResult with correct ItemMatch objects | unit | `pytest tests/test_llm_matching.py::test_match_products_returns_match_result -x` | Wave 0 |
| SRCH-03 | search_products() calls API with filter.fulfillment=csp | unit | `pytest tests/test_kroger_products.py::test_search_uses_csp_filter -x` | Wave 0 |
| SRCH-04 | Items with confidence >= 0.8 go to auto_items; others to review_items | unit | `pytest tests/test_cart_service.py::test_confidence_partitioning -x` | Wave 0 |
| SRCH-05 | Review mode toggle renders both zones; Alpine.js x-data present | integration | `pytest tests/test_shopping_flow.py::test_review_screen_has_toggle -x` | Wave 0 |
| CART-01 | Confirm button sends POST /shopping/add-to-cart; items added | integration | `pytest tests/test_shopping_flow.py::test_add_to_cart_flow -x` | Wave 0 |
| CART-02 | CartItem records created in SQLite after successful add | unit | `pytest tests/test_cart_service.py::test_cart_items_persisted -x` | Wave 0 |
| CART-03 | Success screen renders item list from CartItem query | integration | `pytest tests/test_shopping_flow.py::test_success_screen_shows_items -x` | Wave 0 |
| LLM-01 | Instructor client accepts anthropic, openai, and ollama model strings | unit | `pytest tests/test_llm_matching.py::test_provider_model_strings -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_kroger_products.py` — covers SRCH-02, SRCH-03 (new service functions)
- [ ] `tests/test_llm_matching.py` — covers SRCH-02, LLM-01 (mock Instructor client)
- [ ] `tests/test_cart_service.py` — covers SRCH-04, CART-02 (CartService orchestration + DB writes)
- [ ] `tests/test_shopping_flow.py` — covers SRCH-01, SRCH-05, CART-01, CART-03 (HTTP integration)

Existing test infrastructure (`conftest.py` with in-memory SQLite, `test_kroger_client.py` mock pattern) covers the scaffolding — new test files follow the same patterns.

---

## Sources

### Primary (HIGH confidence)

- jtbricker/python-kroger-client README + products.json — Kroger Products API response shape, `fulfillment='csp'` default
- CupOfOwls/kroger-api cart.py — Cart API `PUT /v1/cart/add` endpoint, `{"items": [{"upc": "...", "quantity": N}]}` body, 204 success response
- https://python.useinstructor.com/integrations/litellm/ — `instructor.from_provider("litellm/...", async_client=True)` async pattern, `client.create(response_model=...)` usage
- `app/services/kroger_client.py` (Phase 1) — established HTTP client pattern, client credentials flow
- `app/services/oauth_manager.py` (Phase 1) — `get_valid_access_token(db)` for user-authenticated calls
- `app/services/llm_service.py` (Phase 1) — existing LiteLLM usage pattern to extend
- `.planning/research/PITFALLS.md` — 14 specific pitfalls; Pitfalls 4, 5, 6, 11, 12, 13 directly apply to Phase 2

### Secondary (MEDIUM confidence)

- `.planning/research/ARCHITECTURE.md` — CartService as the orchestration layer, data flow patterns for the shopping pipeline
- `.planning/research/STACK.md` — verified stack versions; Instructor 1.14.5 (installed: 1.14.4)
- WebSearch results for Kroger API fulfillment filter `csp` value — corroborated across multiple reference implementations

### Tertiary (LOW confidence)

- Exact Kroger Products API `filter.limit` maximum — not verifiable without authenticated API access; using 10 as safe default

---

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH — all dependencies already in requirements.txt; no new packages
- Kroger Products API parameters: HIGH — `filter.fulfillment=csp` confirmed via 3 reference implementations
- Kroger Cart API format: HIGH — `PUT /v1/cart/add`, `{"items": [{"upc", "quantity"}]}`, 204 success confirmed via CupOfOwls/kroger-api source
- Instructor async pattern: HIGH — `from_provider` with `async_client=True` confirmed via official docs
- Architecture/service design: HIGH — extends Phase 1 patterns directly
- LLM prompt strategy: MEDIUM — batched approach is the correct architectural choice but prompt engineering will require iteration

**Research date:** 2026-04-03
**Valid until:** 2026-05-03 (stable ecosystem — LiteLLM/Instructor update frequently but API patterns are stable)
