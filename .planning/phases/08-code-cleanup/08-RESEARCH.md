# Phase 8: Code Cleanup - Research

**Researched:** 2026-04-07
**Domain:** FastAPI startup error handling, Alpine.js data access patterns, dead code removal
**Confidence:** HIGH

## Summary

Phase 8 addresses four concrete, self-contained defects in the v1.0 codebase. None requires new dependencies or architectural changes — each is a targeted fix within the existing FastAPI + Jinja2 + Alpine.js stack.

The most nuanced item is the Alpine.js swap fix (QUAL-01/QUAL-02). The current code uses `el._x_dataStack[0].selectedUpc` — an undocumented internal API — to read per-card swap state from a form input sitting in the outer component scope. The correct fix is architectural: lift `selectedUpc` per card into the outer `confirmedItems` Alpine array (already present at the `#shopping-content` level), eliminating the need to reach into nested component internals at all. This architectural fix also makes the server-side `/shopping/swap` HTMX endpoint unnecessary, satisfying both QUAL-01 and QUAL-02 together.

The SESSION_SECRET_KEY crash (ERR-01) occurs at module import time on line 62 of `app/main.py` where `get_settings().session_secret_key` is passed directly to `SessionMiddleware`. Pydantic's validator raises `ValidationError` before Uvicorn can serve any response. The fix wraps the `get_settings()` call to catch the error and substitute a dummy secret, then immediately redirects all non-static requests to a `session_error.html` page that explains the setup requirement. The `missing_config.html` template is the design reference.

**Primary recommendation:** Fix QUAL-01/QUAL-02 as a single unit (Alpine state lift + swap endpoint deletion). Fix ERR-01 with a startup-guard wrapper on the SessionMiddleware secret. Fix DOC-01 as two mechanical edits to README.md plus a new LICENSE file.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** GitHub repository URL is `https://github.com/EzekielTheMad/FennCart` — replace all instances of `youruser/fenncart` in README.md
- **D-02:** License is MIT — update README line from `[Add your license here]` to reference MIT License
- **D-03:** Create a `LICENSE` file at repo root with full MIT License text AND update README to link to it

### Claude's Discretion
- **Error page design:** How the missing-SESSION_SECRET_KEY error page looks and behaves (currently raises ValueError that crash-loops Uvicorn). Claude should implement a user-friendly HTML page with setup instructions that displays instead of a stack trace.
- **Swap endpoint fate:** Success criteria says "POST /shopping/swap endpoint is absent" but the endpoint at `app/routers/shopping.py:143` is actively used by `review_card.html` for product swaps. Claude should investigate whether the swap can be handled client-side via Alpine.js (eliminating the server endpoint) or if the success criteria needs reinterpretation. The `Alpine._x_dataStack` fix (QUAL-01) and swap endpoint removal (QUAL-02) are likely related — fixing the Alpine API may enable a client-side swap that removes the need for the POST endpoint.
- **Dead code scope:** Audit all routers for unused routes and imports beyond just the swap endpoint. Remove anything confirmed dead.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ERR-01 | App shows a helpful error page when SESSION_SECRET_KEY is missing instead of crash-looping the container | Startup guard pattern in `app/main.py` line 62 — wrap `get_settings()` call, catch ValidationError, substitute dummy secret, redirect all routes to `session_error.html` |
| DOC-01 | README contains actual license (MIT) and correct GitHub repository URL | Two string replacements in README.md + new LICENSE file at repo root |
| QUAL-01 | Product swap in review screen uses stable Alpine.js API instead of Alpine._x_dataStack internal | Lift per-card `selectedUpc` into outer `confirmedItems` array using Alpine's `updateItem` method; swap clicks mutate outer state directly |
| QUAL-02 | Dead code removed (POST /shopping/swap endpoint, unused imports, stale routes across all routers) | QUAL-01 fix eliminates the need for `/shopping/swap`; `pages.py` and `auth.py` have stale Starlette `TemplateResponse` API usage; `review_card.html` becomes unused |
</phase_requirements>

## Standard Stack

No new libraries are needed for this phase. All fixes use the existing project stack.

### Core (already installed)
| Library | Version | Purpose | Used For |
|---------|---------|---------|---------|
| FastAPI | 0.135.3 | Web framework | ERR-01 startup guard, QUAL-02 route removal |
| Starlette SessionMiddleware | FastAPI dep | Session cookie signing | ERR-01 — must receive a dummy secret when key is misconfigured |
| Alpine.js | 3.x (CDN) | Client-side state | QUAL-01 — replace `_x_dataStack` with outer-scope state update |
| Jinja2 | FastAPI dep | HTML templating | ERR-01 — new `session_error.html` template |
| pydantic-settings | 2.x | Settings validation | ERR-01 — ValidationError is the exception to catch |

**No installation required.** All fixes are code/template changes only.

## Architecture Patterns

### Pattern 1: Startup Guard for Missing Configuration (ERR-01)

**What:** Catch Pydantic `ValidationError` at module level in `app/main.py` when `get_settings()` is called to initialize `SessionMiddleware`. Substitute a dummy secret so the app starts, then redirect all meaningful requests to a static error page.

**When to use:** Configuration errors that are discovered at startup before any request handler runs.

**How the current crash happens:**
```python
# app/main.py line 62 — called at module import time
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret_key)
# If SESSION_SECRET_KEY == "change-me-in-production", Pydantic raises ValidationError here.
# Uvicorn catches the import error and crash-loops the worker.
```

**The fix pattern:**
```python
# app/main.py — wrap the get_settings() call
from pydantic import ValidationError

SESSION_KEY_MISSING = False
try:
    _settings = get_settings()
    _session_secret = _settings.session_secret_key
except ValidationError:
    SESSION_KEY_MISSING = True
    _session_secret = "startup-error-placeholder-not-used-for-real-sessions"

app.add_middleware(SessionMiddleware, secret_key=_session_secret)
```

**Then add a guard in SetupGuardMiddleware or a dedicated middleware:**
```python
class SessionKeyGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        exempt_prefixes = ("/static",)
        if SESSION_KEY_MISSING and not any(request.url.path.startswith(p) for p in exempt_prefixes):
            return templates.TemplateResponse(
                request,
                "session_error.html",
                status_code=500,
            )
        return await call_next(request)
```

**Important:** `SESSION_KEY_MISSING` must be a module-level flag set during import, not re-evaluated on each request. `get_settings()` uses `lru_cache` — calling it again after the first ValidationError would raise again.

**Existing design reference:** `missing_config.html` — standalone HTML with Tailwind CDN, dark slate theme, clear setup instructions. The `session_error.html` should match this pattern exactly.

**Template pattern from `missing_config.html`:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>FennCart -- Setup Required</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center py-16">
    <div class="max-w-lg w-full px-6">
        <h1 class="text-3xl font-semibold text-slate-100 mb-4">SESSION_SECRET_KEY not set</h1>
        <p class="text-base text-slate-400 mb-8">...</p>
        <div class="bg-slate-800 rounded-md p-4 mb-8">
            <code>python -c "import secrets; print(secrets.token_urlsafe(32))"</code>
        </div>
    </div>
</body>
</html>
```

### Pattern 2: Alpine.js State Lift to Eliminate _x_dataStack (QUAL-01)

**What:** The hidden form input at lines 209-238 of `review_screen.html` tries to collect the current `selectedUpc` from each card by reaching into the card's nested `x-data` scope via `el._x_dataStack[0].selectedUpc`. This is an undocumented internal API.

**Root cause:** The `confirmedItems` array in the outer `x-data` scope (line 7-16) already tracks items, but the `updateItem` method on line 10-14 is only called with `description` as the lookup key — it never gets called because the card swap `@click` handler updates only card-local state (`selectedUpc`, `selectedDesc`, etc.) without dispatching upward.

**The correct fix:** Make the card swap `@click` also call `$root.updateItem(...)` (or a renamed method) to propagate the new UPC into the outer `confirmedItems` array. The hidden input can then reference `confirmedItems[idx].upc` directly — no DOM traversal, no internal API.

**Key insight:** `$root` in Alpine.js 3 refers to the closest ancestor element with `x-data`. Since the cards are rendered inside `#shopping-content` which has `x-data`, `$root` from within a card's `x-data` refers to `#shopping-content`. This gives a clean, stable cross-scope communication path.

**Before (fragile):**
```javascript
// In the hidden input :value binding — reads internal Alpine property
upc: (function() {
    for (let el of document.querySelectorAll('#card-{{ loop.index }}')) {
        if (el._x_dataStack) {
            return el._x_dataStack[0].selectedUpc || '{{ item.selected_upc }}';
        }
    }
    return '{{ item.selected_upc }}';
})(),
```

**After (stable):**
```javascript
// confirmedItems is pre-populated in outer x-data from Jinja2 server render
// Card swap @click handler notifies outer scope:
@click="
    selectedUpc = '{{ candidate.upc }}';
    selectedDesc = '{{ candidate.description | e }}';
    selectedPrice = {{ candidate.price_regular if candidate.price_regular is not none else 'null' }};
    open = false;
    $root.updateItem('{{ item.list_item }}', '{{ candidate.upc }}')
"

// In the outer x-data, updateItem uses list_item as key:
updateItem(listItem, newUpc) {
    const idx = this.confirmedItems.findIndex(i => i.list_item === listItem);
    if (idx >= 0) { this.confirmedItems[idx].upc = newUpc; }
}

// Hidden input reads from confirmedItems directly:
:value="JSON.stringify(confirmedItems)"
```

**Note on `confirmedItems` initialization:** The outer `x-data` already declares `confirmedItems` but receives `confirmed_items_json | default('[]')` from the template context. Since `review_screen.html` is rendered server-side by the `/shopping/match` endpoint, `confirmed_items_json` is not passed in context — it defaults to `[]`. The initialization needs to be changed to build `confirmedItems` from Jinja2 directly in the `x-data` string, pre-populated with all items' initial UPCs from `review_items` + `auto_items`.

**Confirmed Alpine.js `$root` availability:** `$root` is a documented Alpine.js 3 magic property that provides access to the root element of the component tree. It is stable and documented at `https://alpinejs.dev/magics/root`.

### Pattern 3: Dead Code Audit (QUAL-02)

**Confirmed dead code identified in audit:**

| Location | Dead Code | Reason |
|----------|-----------|--------|
| `app/routers/shopping.py:143-191` | `POST /shopping/swap` endpoint | Replaced by client-side Alpine state lift (QUAL-01 fix) |
| `app/routers/shopping.py:1` | `import json` | Still used for session JSON operations in `/match` and other endpoints — NOT dead |
| `app/routers/shopping.py:6` | `from typing import Optional` | Used by `matched_candidate: Optional[ProductCandidate]` in swap endpoint — becomes dead after swap removal |
| `templates/partials/review_card.html` | Entire file | Only ever rendered by `/shopping/swap` endpoint. After endpoint removal, file has no callers. |
| `app/routers/pages.py:17,22,30,65` | Old Starlette TemplateResponse API | Uses `{"request": request}` in context dict — deprecated API. Current pattern passes `request` as first positional arg. Functional but generates deprecation warnings. |
| `app/routers/auth.py:49-53` | Old Starlette TemplateResponse API | Same deprecated pattern in the OAuth error handler. |

**Stale API details:** The established pattern (documented in STATE.md accumulated context) is `TemplateResponse(request, "template.html", {...})`. The old pattern `TemplateResponse("template.html", {"request": request, ...})` still works but generates Starlette deprecation warnings. The `pages.py` and `auth.py` files were not updated when this convention was established.

**What is NOT dead code:**
- `json` import in `shopping.py` — used by `/match` and `/add-to-cart` endpoints
- `re` import in `shopping.py` — used by `_quick_parse`
- `from app.schemas.shopping import ConfirmedItem, MatchResult, ProductCandidate` — all used after swap removal
- `from app.schemas.shopping import ItemMatch` — only imported inside swap endpoint body; will be dead after removal

### Pattern 4: MIT LICENSE File

**Standard MIT License text with 2026 copyright year and correct name:**

```
MIT License

Copyright (c) 2026 EzekielTheMad

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**README.md changes (DOC-01):**
- Line 15: `https://github.com/youruser/fenncart.git` → `https://github.com/EzekielTheMad/FennCart.git`
- Line 93: `[Add your license here]` → `This project is licensed under the [MIT License](LICENSE).`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cross-scope Alpine state | `_x_dataStack` DOM traversal | `$root.updateItem()` | `$root` is documented, stable, and stays within Alpine's reactive system |
| Alpine global data access | `Alpine.$data(el)` | State lift into outer `x-data` | `Alpine.$data` has no official stability guarantee per GitHub discussion #3592 |
| Session key error detection | Custom exception middleware | Module-level flag at import time | `lru_cache` on `get_settings()` means only one ValidationError fires; must be caught at import time |

**Key insight:** The `_x_dataStack` property has never been documented and has no stability promise. The correct architectural response is to not need it — lift state up to the shared ancestor scope where both the card clicks and the form input live.

## Common Pitfalls

### Pitfall 1: Catching the Wrong Exception for SESSION_SECRET_KEY

**What goes wrong:** Catching `ValueError` instead of `pydantic.ValidationError`. The Pydantic v2 validator wraps the `ValueError` from `session_key_must_be_changed` in a `ValidationError`. Catching `ValueError` at the `app.add_middleware` call site would not catch `ValidationError`.

**Why it happens:** Pydantic v2 changed how validators surface errors compared to v1. In v1 a ValueError propagated directly; in v2 it is wrapped.

**How to avoid:** Catch `pydantic.ValidationError` (or the broader `Exception` with a log) at the `get_settings()` call site in `app/main.py`.

**Warning signs:** Container starts but `session_error.html` is never served — the exception type is wrong.

### Pitfall 2: lru_cache Prevents Re-calling get_settings()

**What goes wrong:** After the first `ValidationError` from `get_settings()`, the cache does not store anything (the call failed). A second call to `get_settings()` will raise again. Any middleware that tries to call `get_settings()` on each request will crash every request.

**Why it happens:** `lru_cache` only caches successful returns. A failed call leaves the cache empty.

**How to avoid:** The `SESSION_KEY_MISSING` flag must be set at import time from the one-time try/except block. The flag is then checked on each request — not `get_settings()`.

**Warning signs:** Every request to the error page itself crashes with ValidationError.

### Pitfall 3: confirmedItems Initialization with Empty Default

**What goes wrong:** The outer `x-data` in `review_screen.html` line 9 uses `confirmed_items_json | default('[]')`. The `/shopping/match` endpoint does not pass `confirmed_items_json` in context, so `confirmedItems` initializes as `[]`. The `updateItem` method then silently fails to find any items (empty array) and swaps write to nothing.

**Why it happens:** The original `confirmedItems` array was a placeholder — the swap flow relied entirely on reading live DOM state via `_x_dataStack` rather than using the array.

**How to avoid:** When rewriting to the state-lift pattern, initialize `confirmedItems` from Jinja2 data directly in the `x-data` attribute — build a JSON array from `review_items + auto_items` with initial `upc` values. Do NOT depend on the `confirmed_items_json` context variable (which is never passed).

**Warning signs:** Swap dropdown works visually but submitted `confirmed_items_json` has the old UPCs.

### Pitfall 4: review_card.html Still Referenced After Swap Endpoint Removal

**What goes wrong:** Deleting the `/shopping/swap` endpoint without removing the import of `review_card.html`. The template file has no other callers once the endpoint is gone.

**Why it happens:** Templates are not import-checked by Python — a stale template reference causes no startup error.

**How to avoid:** Delete `templates/partials/review_card.html` as part of QUAL-02 cleanup. Check git history if unsure of callers.

**Warning signs:** `review_card.html` remains in the templates directory as dead code.

### Pitfall 5: Stale TemplateResponse API Creates Deprecation Noise

**What goes wrong:** `pages.py` and `auth.py` use the old Starlette API `TemplateResponse("template.html", {"request": request, ...})`. This generates deprecation warnings on every request.

**Why it happens:** These files predate the established convention (documented in STATE.md: "Starlette 0.49.1 TemplateResponse new API: request is first param, no longer in context dict").

**How to avoid:** Fix all occurrences in `pages.py` (lines 17, 22, 30, 65) and `auth.py` (lines 49-53) to use `TemplateResponse(request, "template.html", {...})`.

### Pitfall 6: $root Scope Depends on x-data Nesting

**What goes wrong:** `$root` resolves to the closest ancestor with `x-data`. If a card's `@click` calls `$root.updateItem(...)` but the card is NOT nested inside `#shopping-content`'s `x-data` scope (e.g., if HTMX replaces it with a partial that has no outer `x-data`), `$root` would resolve to the card's own scope and `updateItem` would be undefined.

**Why it not a concern here:** The swap dropdown is rendered server-side via Jinja2 loops in `review_screen.html`, inside `#shopping-content`. No HTMX swap replaces these cards. The entire `review_screen.html` is swapped in as one unit by `/shopping/match`. The card elements always exist within the outer `x-data`.

**How to avoid:** Confirm the alpine `x-data` nesting: outer `#shopping-content` > card `x-data`. Both are in the same server-rendered template. This is safe.

## Code Examples

### ERR-01: Startup Guard in app/main.py

```python
# Source: existing SetupGuardMiddleware pattern in app/main.py
from pydantic import ValidationError

SESSION_KEY_MISSING = False
try:
    _session_secret = get_settings().session_secret_key
except (ValidationError, Exception):
    SESSION_KEY_MISSING = True
    _session_secret = "startup-error-placeholder-not-used"

app = FastAPI(title="FennCart", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=_session_secret)
app.add_middleware(SetupGuardMiddleware)
```

Then in `SetupGuardMiddleware.dispatch` (or a new sibling middleware), check `SESSION_KEY_MISSING` before the Kroger credentials check:

```python
async def dispatch(self, request: Request, call_next):
    exempt_prefixes = ("/static", "/setup", "/auth", "/health")
    if any(request.url.path.startswith(p) for p in exempt_prefixes):
        return await call_next(request)

    if SESSION_KEY_MISSING:
        return templates.TemplateResponse(
            request,
            "session_error.html",
            status_code=500,
        )
    # ... rest of existing middleware
```

### QUAL-01: confirmedItems initialization in review_screen.html

```html
{# Build confirmedItems from server-rendered Jinja2 data — pre-populate initial UPCs #}
<div x-data="{
    mode: '{{ review_mode | default("exceptions") }}',
    confirmedItems: [
        {% for item in review_items %}
        {
            list_item: '{{ item.list_item | e }}',
            upc: '{{ item.selected_upc }}',
            description: '{{ item.selected_description | e }}',
            brand: '{{ item.selected_brand | e }}',
            size: '{{ item.selected_size | e }}',
            quantity: 1,
            price: {{ item.selected_price if item.selected_price is not none else 'null' }}
        }{% if not loop.last or auto_items %},{% endif %}
        {% endfor %}
        {% for item in auto_items %}
        {
            list_item: '{{ item.list_item | e }}',
            upc: '{{ item.selected_upc }}',
            description: '{{ item.selected_description | e }}',
            brand: '{{ item.selected_brand | e }}',
            size: '{{ item.selected_size | e }}',
            quantity: 1,
            price: {{ item.selected_price if item.selected_price is not none else 'null' }}
        }{% if not loop.last %},{% endif %}
        {% endfor %}
    ],
    updateItem(listItem, newUpc) {
        const idx = this.confirmedItems.findIndex(i => i.list_item === listItem);
        if (idx >= 0) { this.confirmedItems[idx].upc = newUpc; }
    }
}" id="shopping-content">
```

### QUAL-01: Card swap @click notifies outer scope

```html
{# Card swap candidate @click — notifies outer x-data via $root #}
<div class="flex items-center gap-3 p-3 hover:bg-slate-700 cursor-pointer rounded"
     @click="
        selectedUpc = '{{ candidate.upc }}';
        selectedDesc = '{{ candidate.description | e }}';
        selectedBrand = '{{ candidate.brand | e }}';
        selectedSize = '{{ candidate.size | e }}';
        selectedPrice = {{ candidate.price_regular if candidate.price_regular is not none else 'null' }};
        open = false;
        $root.updateItem('{{ item.list_item | e }}', '{{ candidate.upc }}')
     ">
```

### QUAL-01: Hidden input reads from confirmedItems directly

```html
{# Hidden input — reads from outer confirmedItems array, no DOM traversal #}
<input type="hidden"
       name="confirmed_items_json"
       :value="JSON.stringify(confirmedItems)">
```

### QUAL-02: Removing Optional import after swap endpoint deletion

After deleting the swap endpoint, `Optional` from `typing` is no longer used in `shopping.py`. Remove the import line:

```python
# Remove this line from shopping.py
from typing import Optional
```

Also remove the inline import inside the now-deleted endpoint body:
```python
# This was inside shopping_swap — deletes with endpoint
from app.schemas.shopping import ItemMatch
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `TemplateResponse("tmpl.html", {"request": request})` | `TemplateResponse(request, "tmpl.html", {})` | Starlette 0.49.1 | Old form still works but logs deprecation warning; `pages.py` and `auth.py` still use old form |
| `_x_dataStack[0].selectedUpc` | `$root.updateItem(listItem, upc)` | This phase | Eliminates undocumented internal API dependency |

## Environment Availability

Step 2.6: SKIPPED — This phase makes no changes requiring external tools, services, or runtimes beyond what is already installed. All changes are code/template/doc edits.

## Open Questions

1. **Copyright holder name for LICENSE file**
   - What we know: GitHub repo is `EzekielTheMad/FennCart`, year is 2026
   - What's unclear: Legal name vs GitHub username for copyright line
   - Recommendation: Use "EzekielTheMad" (matches repo owner) unless user specifies otherwise. This is acceptable for MIT License.

2. **SessionKeyGuard middleware placement**
   - What we know: `SetupGuardMiddleware` already handles missing Kroger credentials with a similar error page pattern; the SESSION_KEY_MISSING check could go inside it or as a separate middleware added before it.
   - What's unclear: Whether to add a new `SessionKeyGuardMiddleware` class or fold the check into the existing `SetupGuardMiddleware`.
   - Recommendation: Fold into `SetupGuardMiddleware` as the first check — it already handles "app not ready" states and has the templates instance in scope. Avoids adding another middleware class for a single `if` check.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + anyio + httpx |
| Config file | `pytest.ini` (implied by `python -m pytest tests/ -q` in README) |
| Quick run command | `python -m pytest tests/test_shopping_flow.py -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ERR-01 | App without SESSION_SECRET_KEY serves `session_error.html` instead of crashing | integration | `python -m pytest tests/test_session_key_guard.py -x` | Wave 0 gap |
| DOC-01 | README contains `https://github.com/EzekielTheMad/FennCart` and "MIT License" | manual/smoke | `grep -c "EzekielTheMad/FennCart" README.md && grep -c "MIT License" README.md` | manual |
| QUAL-01 | Swap via Alpine state lift passes correct UPC in `confirmed_items_json` | integration | `python -m pytest tests/test_shopping_flow.py::test_swap_updates_confirmed_items -x` | Wave 0 gap |
| QUAL-02 | POST /shopping/swap returns 404 after removal | integration | `python -m pytest tests/test_shopping_flow.py::test_swap_endpoint_removed -x` | Wave 0 gap |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_shopping_flow.py -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_session_key_guard.py` — covers ERR-01: tests that a missing/default SESSION_SECRET_KEY causes `session_error.html` to render (status 500) rather than crashing
- [ ] `tests/test_shopping_flow.py::test_swap_updates_confirmed_items` — covers QUAL-01: confirms that the `confirmed_items_json` hidden input value reflects the swapped UPC (requires Alpine to be tested via HTML inspection, so this may be a server-side check that the template renders without `_x_dataStack` references)
- [ ] `tests/test_shopping_flow.py::test_swap_endpoint_removed` — covers QUAL-02: simple 404/405 check that POST `/shopping/swap` is gone

*Existing `test_shopping_flow.py` tests (1-9) cover the shopping flow end-to-end. New tests should be added to that file or a new dedicated file.*

## Project Constraints (from CLAUDE.md)

All constraints are structural/architectural — none conflict with this phase's scope.

| Directive | Impact on Phase 8 |
|-----------|------------------|
| FastAPI + Jinja2 + HTMX + Alpine.js stack | All fixes use existing stack. No new libraries. |
| `replicas: 1` always | No impact — no concurrency changes. |
| Starlette SessionMiddleware for OAuth | ERR-01 fix must not break session middleware registration — dummy secret approach preserves the middleware call. |
| `lru_cache` on `get_settings()` | ERR-01: catch ValidationError at import time only; never call `get_settings()` per-request in the guard. |
| TemplateResponse new API: request as first param | QUAL-02: `pages.py` and `auth.py` stale API calls must be updated to new pattern. |
| Customer search data must not be persisted | No impact — no persistence changes. |

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `app/main.py`, `app/config.py`, `app/routers/shopping.py`, `templates/partials/review_screen.html`, `templates/partials/review_card.html`, `app/routers/pages.py`, `app/routers/auth.py`, `README.md`
- Alpine.js `$root` magic: documented at https://alpinejs.dev/magics/root (stable documented API)
- STATE.md accumulated context — confirmed `lru_cache` on `get_settings()`, Starlette 0.49.1 new TemplateResponse API convention

### Secondary (MEDIUM confidence)
- Alpine.js `$data(element)` stability: GitHub discussion #3592 confirms it is NOT officially documented and stability is uncertain — this is why state-lift pattern is preferred over `Alpine.$data()`
- WebSearch: Alpine.js `_x_dataStack` is an internal undocumented property (consistent across multiple sources: blog posts, GitHub discussions)

### Tertiary (LOW confidence)
- None — all findings verified against source code or official docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all fixes in existing code
- Architecture patterns: HIGH — verified against actual source files; fix patterns derived from existing code conventions
- Pitfalls: HIGH — derived from direct code reading; `lru_cache` behavior and Pydantic v2 ValidationError wrapping are well-established

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (stable domain — Alpine.js 3.x, FastAPI, Pydantic v2 conventions)
