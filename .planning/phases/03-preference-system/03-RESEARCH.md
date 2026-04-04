# Phase 3: Preference System - Research

**Researched:** 2026-04-04
**Domain:** Receipt PDF parsing, preference profile data modeling, LLM-assisted preference extraction, HTMX multi-step UI patterns
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Upload approach is Claude's discretion — single or batch, Claude picks what fits the HTMX/SSR pattern best.
- **D-02:** Editable table after parsing — show parsed items (name, brand, size, qty, price) in an editable table. User can fix OCR errors, remove unwanted items, then confirm to save to preference history.
- **D-03:** Bad receipt handling is Claude's discretion — show partial results with warnings, reject, or hybrid approach.
- **D-04:** Preference weighting approach is Claude's discretion — simple count-based, recency-weighted, or hybrid. Must support PREF-03 (distinguish recurring preferences from one-off substitutions).
- **D-05:** Flat list organization — each preference is a standalone entry (e.g., "prefers Tillamook cheddar"). No category-based grouping. Search/filter for browsing.
- **D-06:** Flag-and-ask on contradictions — when a new receipt contradicts existing preferences (e.g., different brand than usual), detect the brand switch and ask the user: "New preference or one-time substitution?" Do not silently auto-update.
- **D-07:** Chat-style interface — conversational back-and-forth for natural language preference updates. LLM can ask clarifying questions.
- **D-08:** Always confirm before applying — show the interpreted change and require explicit user approval before saving to the profile.
- **D-09:** Page layout is Claude's discretion — must accommodate three modes: receipt upload, NL chat, and manual preference list.
- **D-10:** Editing pattern is Claude's discretion — inline editing vs drawer/modal, Claude picks what works.
- **D-11:** Bulk delete with checkboxes — checkbox per preference entry, select multiple, bulk delete button.

### Claude's Discretion

- Receipt upload UX approach (single vs batch, progress indicator style)
- Bad/partial receipt error handling pattern
- Preference weighting algorithm (must satisfy PREF-03: recurring vs one-off)
- Preferences page layout (must fit sidebar nav pattern from Phase 1)
- Individual preference editing pattern (inline vs modal/drawer)
- Chat interface implementation (HTMX polling vs SSE-like pattern for conversational flow)
- How preference data is serialized for the `preferences` parameter in `match_products()`

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PREF-01 | User can upload Fry's receipt PDFs to bootstrap their preference profile | pdfplumber 0.11.9 already in requirements.txt; `python-multipart` already present for FastAPI file upload; HTMX file upload pattern via `hx-encoding="multipart/form-data"` |
| PREF-02 | App parses receipt PDFs and extracts purchase history (items, brands, sizes, quantities, prices) | Two-stage pipeline: pdfplumber extracts raw text from tabular receipt layout, then Instructor+LLM normalizes abbreviations into structured `ReceiptLineItem` objects |
| PREF-03 | App builds a living preference profile weighted by purchase frequency, distinguishing recurring preferences from one-off substitutions | `purchase_count` + `last_seen` columns on `PreferenceEntry`; count >= 2 is "recurring"; count == 1 is "observed once"; D-06 flag-and-ask when new receipt contradicts an established preference |
| PREF-04 | User can update preferences via natural language ("we switched to oat milk", "stop buying Kroger brand yogurt") | Instructor structured output for `PreferenceDelta` schema; chat-style HTMX partial swaps; multi-turn via session state or conversation array; always confirm before write |
| PREF-05 | User can manually view, add, edit, and delete preference entries | SQLModel CRUD on `PreferenceEntry`; flat list with search/filter; bulk delete via checkbox form; inline edit or modal — Claude's discretion (D-10, D-11) |
| PREF-06 | LLM product matching uses the preference profile to re-rank Kroger API results | `match_products()` already accepts `preferences: Optional[dict]`; Phase 3 defines the dict schema and ensures `CartService.process_list()` loads and passes it |
</phase_requirements>

---

## Summary

Phase 3 adds the preference layer that makes FennCart's product matching actually useful. Three distinct features must coexist on one page: receipt PDF upload-and-parse, natural language preference chat, and a browseable/editable preference list. All three write to the same `PreferenceEntry` table. The challenge is not the individual features — each is straightforward — but making the data model, contradiction detection (D-06), and CartService integration clean enough to not become technical debt.

The core data modeling decision is a single flat `preference_entries` table with a `(product_category, brand, product_name)` key, a `purchase_count`, and `last_seen_at`. This satisfies PREF-03 because count >= 2 means recurring and count == 1 means "seen once, not yet a preference." When a new receipt shows a different brand in a category where a preference already exists with count >= 2, that triggers the flag-and-ask path (D-06) rather than silent update.

The `preferences` dict passed to `match_products()` is already plumbed (it accepts `Optional[dict]` with a comment "Phase 3 hook"). Phase 3 defines what goes in that dict: a simple list of top-N preferences per product category. The LLM system prompt already has a branch that uses it: `"User preferences: {json.dumps(preferences)}. Prefer products matching these preferences."` Phase 3 just needs to load the right data.

**Primary recommendation:** Build the data model and CRUD service first (Wave 1), then the receipt parser (Wave 2), then the NL chat (Wave 3), then wire the preferences dict into CartService and verify matching changes (Wave 4). The UI spans all waves as partials alongside each feature.

---

## Standard Stack

### Core (all already in requirements.txt)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pdfplumber | 0.11.9 | Receipt PDF text + table extraction | Already in requirements.txt; chosen for tabular machine-generated receipts; MIT license |
| Instructor | 1.14.5 | Structured LLM output for receipt parsing + NL preference parsing | Already used in `llm_service.py` for `parse_shopping_list` and `match_products` |
| SQLModel | 0.0.37 | PreferenceEntry + ReceiptUpload ORM models | Established pattern across Phase 1 and Phase 2 |
| Alembic | 1.18.4 | Schema migration for new tables | Established — two migrations already exist (0001, 0002) |
| FastAPI python-multipart | (already present) | File upload endpoint for receipt PDF | Required by FastAPI for `UploadFile`; already in requirements |
| HTMX | 1.9.12 (CDN) | Multi-step upload flow, editable review table, chat partial swaps | Established in Phase 1 and Phase 2 |

### No New Dependencies Required

Phase 3 adds no new packages to requirements.txt. All needed libraries are already installed. This is a feature-build phase, not a stack-expansion phase.

---

## Architecture Patterns

### New Files to Create

```
app/
├── models/
│   ├── preference_entry.py      # PreferenceEntry SQLModel table
│   └── receipt_upload.py        # ReceiptUpload SQLModel table (audit log)
├── services/
│   ├── preference_service.py    # CRUD + contradiction detection + preferences dict builder
│   └── receipt_parser.py        # pdfplumber + LLM extraction pipeline
├── routers/
│   └── preferences.py           # HTTP endpoints for all three preference modes
├── schemas/
│   └── preferences.py           # Pydantic request/response schemas
templates/
└── pages/
    └── preferences.html         # Replace placeholder — three-panel layout
    partials/
    ├── pref_list.html            # Preference list fragment (HTMX target)
    ├── pref_row.html             # Single editable row fragment
    ├── receipt_review.html       # Parsed receipt editable table fragment
    ├── receipt_contradictions.html  # Flag-and-ask contradiction UI fragment
    └── chat_message.html        # NL chat message fragment
alembic/versions/
└── 0003_preference_tables.py    # Migration for preference_entries + receipt_uploads
```

### Pattern 1: PreferenceEntry Data Model

**What:** Flat table. Each row is a learned preference for one product category + brand pair. `purchase_count` and `last_seen_at` drive the recurring-vs-one-off distinction (PREF-03).

**Schema:**
```python
# app/models/preference_entry.py
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class PreferenceEntry(SQLModel, table=True):
    __tablename__ = "preference_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    # Lookup key — trio must be unique together
    product_category: str          # e.g. "milk", "cheddar cheese", "pasta"
    brand: str                     # e.g. "Tillamook", "Kroger", ""
    product_name: str              # e.g. "Medium Cheddar", "2% Milk" — canonical name
    # Weighting
    purchase_count: int = Field(default=1)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    # Source tracking
    source: str = Field(default="manual")  # "receipt", "nl_chat", "manual"
    # Notes / display
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Uniqueness constraint:** Add a SQLAlchemy `UniqueConstraint("product_category", "brand", "product_name")` via table args to prevent duplicates at the DB level.

**Recurring vs one-off rule:**
- `purchase_count == 1` = "observed once" — show in list but low weight in matching
- `purchase_count >= 2` = "established preference" — high weight in matching, triggers D-06 contradiction check

### Pattern 2: ReceiptUpload Audit Table

**What:** Records each receipt upload for audit and deduplication. Does not persist Kroger product data (TOS safe — receipt data is user-provided, not from the Kroger API).

```python
# app/models/receipt_upload.py
class ReceiptUpload(SQLModel, table=True):
    __tablename__ = "receipt_uploads"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    items_extracted: int = Field(default=0)
    items_confirmed: int = Field(default=0)
    parse_status: str = Field(default="pending")  # "pending","parsed","confirmed","failed"
    parse_warnings: Optional[str] = None  # JSON list of warning strings
```

### Pattern 3: Receipt Parser Pipeline

**What:** Two-stage pipeline — pdfplumber for raw text extraction, then Instructor+LLM for structured normalization.

**Stage 1 — pdfplumber extraction:**
```python
# app/services/receipt_parser.py
import pdfplumber
from io import BytesIO

def extract_receipt_text(pdf_bytes: bytes) -> str:
    """Extract all text from a receipt PDF using pdfplumber.

    Uses extract_text() with layout=True to preserve column positions.
    For Fry's tabular receipts, layout mode keeps item/price columns aligned.
    Falls back to extract_words() if extract_text() returns empty.
    """
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        pages_text = []
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if not text or len(text.strip()) < 10:
                # Fallback: reconstruct from word positions
                words = page.extract_words()
                text = " ".join(w["text"] for w in words)
            pages_text.append(text)
        return "\n".join(pages_text)
```

**Stage 2 — Instructor LLM normalization:**
```python
# Pydantic schema for Instructor
class ReceiptLineItem(BaseModel):
    product_name: str           # Expanded/normalized name (not the receipt abbreviation)
    brand: str                  # Inferred brand, "" if unknown
    product_category: str       # Semantic category, e.g. "milk", "cheddar cheese"
    quantity: int = 1
    size: str = ""              # e.g. "32 oz", "1 lb"
    price: Optional[float] = None
    confidence: float = Field(ge=0.0, le=1.0)  # How confident in the normalization

class ParsedReceipt(BaseModel):
    items: list[ReceiptLineItem]
    parse_warnings: list[str] = Field(default_factory=list)
```

**Key prompt guidance for LLM:** "Fry's receipts use heavy abbreviations (PRIV SEL = Private Selection, CHCKN BRST = Chicken Breast, ORG = Organic). Expand abbreviations. Infer brand from context. Set confidence < 0.7 if the description is ambiguous."

### Pattern 4: Preferences Dict for match_products()

**What:** `CartService.process_list()` must load preference data and pass it to `match_products()`. The `preferences` dict format is what Phase 2's hook expects.

**Recommended serialization:**
```python
# In PreferenceService
async def get_preferences_for_matching(self) -> dict:
    """Build the preferences dict consumed by match_products().

    Returns: {
        "entries": [
            {"category": "milk", "brand": "Organic Valley", "product": "2% Milk",
             "strength": "strong"},  # purchase_count >= 3
            {"category": "cheddar cheese", "brand": "Tillamook", "product": "Medium Cheddar",
             "strength": "moderate"},  # purchase_count == 2
            ...
        ]
    }
    Only includes entries with purchase_count >= 2 (established preferences).
    Capped at 50 entries to stay within LLM token budget (Pitfall 5).
    """
```

**Integration point in CartService.process_list():**
```python
# In CartService (Phase 3 extends this method)
async def process_list(
    self,
    raw_text: str,
    preferences: Optional[dict] = None,
) -> tuple[MatchResult, dict[str, list[ProductCandidate]]]:
    # Phase 3 adds: if preferences is None, load from DB
    # The router passes None; CartService auto-loads if available
```

The router that calls `process_list()` should inject a `PreferenceService` dependency and pass the loaded preferences dict. Keeping auto-load in CartService (rather than the router) avoids leaking DB access into routing logic.

### Pattern 5: Contradiction Detection (D-06)

**What:** When processing a receipt, check each parsed item against existing preferences with `purchase_count >= 2`. If a different brand is found for the same product category, surface a flag-and-ask UI rather than silently updating.

```python
async def detect_contradictions(
    self,
    new_items: list[ReceiptLineItem],
) -> tuple[list[ReceiptLineItem], list[ContradictionCandidate]]:
    """Separate new items into clean additions vs contradictions.

    Returns (clean_items, contradictions) where contradictions need
    user resolution before being applied to the preference profile.
    """
```

**ContradictionCandidate schema:**
```python
class ContradictionCandidate(BaseModel):
    category: str
    existing_brand: str
    existing_count: int
    new_brand: str
    product_name: str
    # User resolution choices
    resolution: Optional[str] = None  # "new_preference" | "one_time" | "skip"
```

### Pattern 6: NL Preference Chat (D-07, D-08)

**What:** Stateless request-response pattern using Starlette session for conversation history. Each user message + LLM response is appended to a session list. HTMX posts to `/preferences/chat` and swaps in a new partial response.

**Instructor schema for NL parsing:**
```python
class PreferenceDelta(BaseModel):
    """Structured interpretation of a natural language preference update."""
    action: str        # "replace" | "add" | "remove" | "clarify"
    category: str      # e.g. "milk"
    old_brand: Optional[str] = None    # For "replace" action
    new_brand: Optional[str] = None
    product_name: Optional[str] = None
    clarification_question: Optional[str] = None  # Set when action=="clarify"
    human_summary: str  # e.g. "Replace whole milk with oat milk for all milk preferences"
```

When `action == "clarify"`, the LLM response shows a clarification question and the chat continues. When `action != "clarify"`, the response shows a confirmation preview (D-08) and requires user approval before writing to DB.

**HTMX flow for chat:**
- Form `hx-post="/preferences/chat"` with `hx-swap="beforeend"` on the chat history container
- No SSE or WebSockets needed — the round-trip is synchronous (user sends message, gets one response)
- Multi-turn is implemented by carrying conversation history in the Starlette session

### Pattern 7: Preferences Page Layout (D-09)

**What:** Three-panel tab layout within the existing dark sidebar shell. Tabs: "Receipt Upload", "Preferences List", "Update via Chat". Each tab's content is a separate HTMX partial loaded on tab click.

**Why tabs over a single scrolling page:** Three distinct interaction modes with very different UI states (file upload + review table vs flat list vs chat). Tabs keep them isolated so HTMX swaps don't clobber each other's state.

**Tab implementation:** Alpine.js `x-data="{tab: 'list'}"` with `@click` to switch tabs and `x-show` to toggle visibility. No server round-trip needed for tab switching since all three panels can be rendered on page load.

### Anti-Patterns to Avoid

- **Storing Kroger Products API data in preference_entries:** Preference data comes from user-uploaded receipts (user-provided data), not from the Kroger API. Never write API response product data to `preference_entries`. This is the TOS distinction.
- **Silent preference overwrites:** D-06 is a hard requirement. Any code path that updates `purchase_count` or changes `brand` on an existing established preference without user confirmation violates the spec.
- **Loading the full preference table into the LLM prompt:** Cap the preferences dict at 50 entries, ordered by purchase_count DESC. Sending 500 preferences wastes tokens and degrades match quality.
- **Making Kroger API calls during receipt processing:** The receipt parsing pipeline should never call the Kroger Products API. Receipt processing is offline — pdfplumber + LLM only. Kroger API calls happen only during the shopping flow.
- **Storing raw receipt PDF bytes in SQLite:** The `receipt_uploads` table should store metadata only. If PDF storage is needed for reprocessing, use a file on the Docker volume, not a BLOB in the DB.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Custom PDF byte parser | `pdfplumber.open(BytesIO(bytes)).pages[n].extract_text(layout=True)` | Handles coordinate-based layout, column detection, character-level access |
| Receipt abbreviation expansion | Regex lookup tables | Instructor+LLM with `ParsedReceipt` schema | Fry's abbreviations are inconsistent; LLM handles "PRIV SEL", "ORG", "BN FREE" gracefully |
| LLM structured output parsing | Manual JSON extraction + try/except | Instructor `client.create(response_model=ParsedReceipt, max_retries=2)` | Retry-on-validation-failure, Pydantic type coercion, already established pattern |
| Multi-turn chat state | Server-side session table | Starlette session middleware (already configured) | No new infrastructure; conversation history as `request.session["pref_chat_history"]` |
| Contradiction detection heuristics | Fuzzy string matching | Exact `product_category` match + different `brand` match against `purchase_count >= 2` entries | Simple and deterministic; avoids false positives from fuzzy matching |
| File upload progress | Custom XHR polling | HTMX `hx-encoding="multipart/form-data"` + `htmx:xhr:progress` event handler | One-liner; already in HTMX docs |

**Key insight:** The LLM does the messy NLP work (abbreviation expansion, brand inference, intent parsing). The application code only needs to store and query clean structured data.

---

## Runtime State Inventory

Step 2.5 applies minimally here — this is a greenfield feature addition, not a rename/refactor.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — `preference_entries` and `receipt_uploads` tables do not yet exist | Wave 1: Alembic migration 0003 creates them |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | None — preference system requires no new credentials | None |
| Build artifacts | None | None |

The Alembic migration (0003) is the only state change. `app/models/__init__.py` must import new models so Alembic autodiscovery registers them with `SQLModel.metadata`.

---

## Common Pitfalls

### Pitfall 1: Silent Parse Failures on Non-Standard Receipt Formats (from PITFALLS.md #7)

**What goes wrong:** Emailed PDF receipts, app-downloaded PDFs, and older Fry's receipt formats have different layouts. A parser tuned on one format produces empty output on another without raising an error.

**Why it happens:** pdfplumber returns empty string if the PDF has unusual encoding or is image-based. The LLM receives blank context and produces a plausible-but-wrong `ParsedReceipt`.

**How to avoid:**
- Check `len(extracted_text.strip()) < 50` after pdfplumber extraction and return a clear error before calling the LLM
- Include `parse_warnings` in `ParsedReceipt` — surface them in the review UI
- Always show the user a count: "Found 23 items — please review before saving"
- Never silently save parsed items; the user confirmation step (D-02) is mandatory

**Warning signs:** Parser returns 0 items with no user-visible error; `parse_warnings` list is always empty even on bad input.

### Pitfall 2: TOS Violation — Mixing Receipt Data with Kroger API Response Data

**What goes wrong:** A developer sees `brand` and `description` in both `ProductCandidate` (from Kroger API) and `ReceiptLineItem` (from user receipt) and decides to use confirmed cart items from `cart_items` table as a preference signal.

**Why it happens:** Cart items are already in the DB; it seems efficient to "learn" from them.

**How to avoid:** Preference signals come ONLY from user-uploaded receipts and manual entries. `cart_items` represents what was searched from the Kroger API — using it as a preference signal would constitute building a derived database from Kroger API responses. Add a comment to `PreferenceService` explicitly stating this constraint.

**Warning signs:** Any code path that reads from `cart_items` or `cart_sessions` and writes to `preference_entries`.

### Pitfall 3: Preference Dict Too Large for LLM Prompt

**What goes wrong:** A user uploads 20 receipts and accumulates 200+ preference entries. The full dict is serialized into `match_products()` system prompt, adding 3,000+ tokens per shopping run. Cost spikes.

**How to avoid:**
- `get_preferences_for_matching()` returns at most 50 entries, ordered by `purchase_count DESC, last_seen_at DESC`
- Only include entries with `purchase_count >= 2` (established preferences only)
- Future optimization: filter by relevance to items in the current shopping list (Phase 4+ concern)

### Pitfall 4: Contradiction Detection False Positives

**What goes wrong:** User buys "Kroger Brand Milk" once and "Organic Valley Milk" once. Second purchase triggers a "contradiction" alert even though neither is an established preference.

**How to avoid:** D-06 contradiction check requires `purchase_count >= 2` on the existing entry. A single prior purchase is "observed once" and does not trigger the flag. Only established preferences (count >= 2) trigger D-06.

### Pitfall 5: Chat History Growing Without Bound

**What goes wrong:** User has a long NL chat conversation. Session stores the full history. After 30 messages, the conversation history passed to the LLM exceeds context limits.

**How to avoid:** Cap conversation history at last 10 messages for LLM context. Store full history in session for display, but only send the last 10 turns to the LLM.

### Pitfall 6: Alembic Model Import Gap

**What goes wrong:** New `PreferenceEntry` and `ReceiptUpload` SQLModel classes exist in `app/models/` but are not imported in `app/models/__init__.py`. Alembic autogenerate runs on an empty metadata and generates no migration columns.

**How to avoid:** Every new model file must be added to `app/models/__init__.py`. The existing `alembic/env.py` already imports `app.models` — this is only effective if `__init__.py` imports all table classes.

---

## Code Examples

Verified patterns from established codebase + official sources:

### File Upload Endpoint (FastAPI + HTMX)

```python
# app/routers/preferences.py
from fastapi import APIRouter, UploadFile, File, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session

router = APIRouter(prefix="/preferences")
templates = Jinja2Templates(directory="templates")

@router.post("/receipt/upload", response_class=HTMLResponse)
async def upload_receipt(
    request: Request,
    receipt_pdf: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    pdf_bytes = await receipt_pdf.read()
    # ... parse and return editable table partial
    return templates.TemplateResponse(
        request,
        "partials/receipt_review.html",
        {"items": parsed_items, "contradictions": contradictions},
    )
```

```html
<!-- HTMX file upload form in templates/pages/preferences.html -->
<form hx-post="/preferences/receipt/upload"
      hx-encoding="multipart/form-data"
      hx-target="#receipt-review-area"
      hx-swap="innerHTML"
      hx-indicator="#upload-spinner">
  <input type="file" name="receipt_pdf" accept=".pdf" required>
  <button type="submit">Parse Receipt</button>
  <div id="upload-spinner" class="htmx-indicator">Parsing...</div>
</form>
<div id="receipt-review-area"></div>
```

### pdfplumber Receipt Text Extraction

```python
# app/services/receipt_parser.py
import pdfplumber
from io import BytesIO

def extract_receipt_text(pdf_bytes: bytes) -> tuple[str, list[str]]:
    """Extract text from receipt PDF. Returns (text, warnings)."""
    warnings = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            all_text = []
            for i, page in enumerate(pdf.pages):
                text = page.extract_text(layout=True)
                if not text or len(text.strip()) < 10:
                    words = page.extract_words()
                    text = " ".join(w["text"] for w in words)
                    if text:
                        warnings.append(f"Page {i+1}: used fallback word extraction")
                all_text.append(text or "")
            combined = "\n".join(all_text)
            if len(combined.strip()) < 50:
                warnings.append("Very little text extracted — PDF may be image-based or encrypted")
            return combined, warnings
    except Exception as e:
        return "", [f"PDF extraction failed: {str(e)}"]
```

### Instructor Structured Receipt Parsing

```python
# app/services/receipt_parser.py (continued)
async def parse_receipt_with_llm(
    raw_text: str,
    api_key: str,
    provider: str,
    model: str,
) -> ParsedReceipt:
    """Use Instructor to normalize receipt text into structured line items."""
    model_str = f"{provider}/{model}" if "/" not in model else model
    client = instructor.from_provider(f"litellm/{model_str}", async_client=True)

    system_prompt = (
        "You are a grocery receipt parser for Fry's/Kroger receipts. "
        "Fry's uses heavy abbreviations: PRIV SEL = Private Selection, "
        "ORG = Organic, CHCKN = Chicken, BRST = Breast, BN FREE = Bone Free. "
        "For each line item: expand abbreviations, infer brand from product name, "
        "assign a semantic product_category (e.g. 'milk', 'cheddar cheese'). "
        "Set confidence < 0.7 if you are guessing the brand or category. "
        "Skip non-food items (tax lines, totals, loyalty savings). "
        "Return parse_warnings for any lines you could not interpret."
    )

    return await client.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this receipt:\n\n{raw_text}"},
        ],
        response_model=ParsedReceipt,
        max_tokens=2000,
        max_retries=2,
        api_key=api_key,
    )
```

### Preference Upsert in PreferenceService

```python
# app/services/preference_service.py
from sqlalchemy import select, and_
from app.models.preference_entry import PreferenceEntry
from datetime import datetime

class PreferenceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_from_receipt_item(
        self,
        item: ReceiptLineItem,
        is_one_time: bool = False,
    ) -> PreferenceEntry:
        """Insert or increment purchase count for a receipt line item.

        is_one_time=True means the user chose 'one-time substitution' at D-06 prompt.
        For one-time items, we still record the entry (purchase_count stays 1) but
        do not increment an existing established preference.
        """
        result = await self.db.execute(
            select(PreferenceEntry).where(
                and_(
                    PreferenceEntry.product_category == item.product_category,
                    PreferenceEntry.brand == item.brand,
                    PreferenceEntry.product_name == item.product_name,
                )
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            if not is_one_time:
                existing.purchase_count += 1
                existing.last_seen_at = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
            self.db.add(existing)
            return existing
        else:
            entry = PreferenceEntry(
                product_category=item.product_category,
                brand=item.brand,
                product_name=item.product_name,
                purchase_count=1,
                source="receipt",
            )
            self.db.add(entry)
            await self.db.flush()
            return entry
```

### NL Chat Endpoint (HTMX partial swap pattern)

```python
# app/routers/preferences.py
@router.post("/chat", response_class=HTMLResponse)
async def preference_chat(
    request: Request,
    message: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    # Load or initialize conversation history from Starlette session
    history = request.session.get("pref_chat_history", [])
    history.append({"role": "user", "content": message})

    # Cap history sent to LLM at last 10 messages (Pitfall 5)
    llm_history = history[-10:]

    delta = await parse_preference_nl(llm_history, api_key, provider, model)
    history.append({"role": "assistant", "content": delta.human_summary})
    request.session["pref_chat_history"] = history

    if delta.action == "clarify":
        # Return clarification question as partial
        return templates.TemplateResponse(
            request,
            "partials/chat_message.html",
            {"message": delta.clarification_question, "role": "assistant", "needs_confirm": False},
        )
    else:
        # Return confirmation preview partial — user must approve before write
        return templates.TemplateResponse(
            request,
            "partials/chat_message.html",
            {"message": delta.human_summary, "role": "assistant",
             "needs_confirm": True, "delta": delta.model_dump()},
        )
```

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pdfplumber | PREF-01, PREF-02 | Already in requirements.txt | 0.11.9 | — |
| python-multipart | File upload endpoint | Already in requirements.txt | latest stable | — |
| Instructor | PREF-02, PREF-04 | Already in requirements.txt | 1.14.5 | — |
| SQLite / aiosqlite | All PREF-* | Already configured | 0.22.1 | — |
| Alembic | Migration 0003 | Already configured | 1.18.4 | — |

No new environment dependencies. Phase 3 adds no packages.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (confirmed in requirements-dev.txt and pytest.ini) |
| Config file | `pytest.ini` at project root |
| Quick run command | `pytest tests/test_preference_service.py tests/test_receipt_parser.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PREF-01 | File upload endpoint accepts PDF, returns review table HTML | integration | `pytest tests/test_preferences_flow.py::test_upload_receipt -x` | Wave 0 |
| PREF-02 | pdfplumber extracts text + LLM returns ParsedReceipt | unit | `pytest tests/test_receipt_parser.py -x` | Wave 0 |
| PREF-03 | purchase_count increments on repeat; count>=2 is "established"; D-06 triggers when brand contradicts established preference | unit | `pytest tests/test_preference_service.py::test_recurring_vs_one_time -x` | Wave 0 |
| PREF-04 | NL chat endpoint returns delta preview; confirmed delta writes to DB | integration | `pytest tests/test_preferences_flow.py::test_nl_chat_confirm -x` | Wave 0 |
| PREF-05 | CRUD endpoints: list, create, edit, delete, bulk delete | integration | `pytest tests/test_preferences_flow.py::test_preference_crud -x` | Wave 0 |
| PREF-06 | CartService.process_list() passes loaded preferences dict to match_products() | unit | `pytest tests/test_cart_service.py::test_process_list_with_preferences -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_preference_service.py tests/test_receipt_parser.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q` (full suite, currently 82 passing)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_preference_service.py` — unit tests for upsert, contradiction detection, preferences dict builder
- [ ] `tests/test_receipt_parser.py` — unit tests for pdfplumber extraction + Instructor parsing (mock LLM)
- [ ] `tests/test_preferences_flow.py` — integration tests for all preferences router endpoints

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw regex for receipt line item parsing | LLM-normalized structured output via Instructor | 2024+ (LLM cost drops made this viable) | No maintenance of abbreviation lookup tables; handles format variation automatically |
| Separate preference "category tree" UI | Flat list with search/filter (D-05) | Design decision (Phase 3 context) | Simpler to implement and browse; avoids category taxonomy maintenance |
| WebSocket for streaming chat | Stateless POST + HTMX partial swap | Current HTMX pattern | Single LLM call per message; no open connections; simpler server code |

---

## Open Questions

1. **Fry's receipt PDF format variation**
   - What we know: Three formats exist (emailed, app-downloaded, older format). pdfplumber works best on machine-generated PDFs.
   - What's unclear: Whether emailed Fry's receipts are machine-generated or image-embedded. If image-embedded, pdfplumber returns empty text.
   - Recommendation: STATE.md flags this as a research item ("Test at least three real Fry's receipt PDF formats before committing to parser design"). Wave 1 should include a spike with at least one real receipt PDF before building the full parser. If image-based receipts are encountered, the warning message should direct users to download the app-generated PDF instead.

2. **Preferences dict token budget at scale**
   - What we know: Cap at 50 entries prevents runaway costs (Pitfall 5). Current `match_products()` system prompt appends the full dict as `json.dumps(preferences)`.
   - What's unclear: At what preference count does matching quality improve meaningfully vs. adding noise?
   - Recommendation: Start with count >= 2 filter + top-50 cap. This is a tunable parameter; document it as such.

3. **UniqueConstraint on (product_category, brand, product_name)**
   - What we know: Alembic cannot always autogenerate `UniqueConstraint` from SQLModel table_args.
   - What's unclear: Whether SQLModel 0.0.37 supports `__table_args__` with `UniqueConstraint` cleanly.
   - Recommendation: Add the constraint explicitly in the Alembic migration SQL (`op.create_unique_constraint(...)`) rather than relying on SQLModel metadata autogeneration. This is safer for all versions.

---

## Project Constraints (from CLAUDE.md)

The following CLAUDE.md directives apply to Phase 3. Planner must verify compliance on each plan.

| Directive | Phase 3 Impact |
|-----------|---------------|
| Python 3.12 + FastAPI 0.135.3 | No change — existing stack |
| SQLModel 0.0.37 + aiosqlite 0.22.1 | All new models use SQLModel; no raw SQLAlchemy |
| Alembic 1.18.4 | Migration 0003 required for new tables |
| pdfplumber 0.11.9 | Already installed; use for PREF-01/02 |
| Instructor 1.14.5 | Already installed; use Instructor pattern from `llm_service.py` |
| HTMX 1.9.x CDN | File upload and chat partials use HTMX; no JS framework |
| Alpine.js 3.x CDN | Tab switching on preferences page; no React/Vue |
| Jinja2 templates (SSR) | All preference UI as server-rendered partials |
| `--workers 1` for Uvicorn | No concurrent write concern (already enforced) |
| `PRAGMA journal_mode=WAL` | Already set in `database.py` init_db() — no change needed |
| TOS: No persistent Kroger API response data | `preference_entries` source is user receipts only — never from `cart_items` or Kroger API responses |
| TOS: Customer search data not persisted | Preference data is user-provided (receipts) — not search data; compliant |
| GSD Workflow Enforcement | All edits via `/gsd:execute-phase` — no direct repo edits |

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — `app/services/llm_service.py`, `app/services/cart_service.py`, `app/schemas/shopping.py`, `tests/conftest.py`, `alembic/versions/0002_cart_tables.py` — direct inspection of established patterns
- `CLAUDE.md` — technology stack, version pins, TOS constraints
- `.planning/phases/03-preference-system/03-CONTEXT.md` — locked decisions
- `.planning/research/PITFALLS.md` — Phase 3 specific warnings (Pitfall 7: receipt format variation, Pitfall 3: TOS persistent storage)
- pdfplumber GitHub README — `extract_text(layout=True)`, `extract_words()`, `crop()` / `within_bbox()` API — fetched 2026-04-04

### Secondary (MEDIUM confidence)

- [HTMX file upload pattern](https://htmx.org/examples/file-upload/) — `hx-encoding="multipart/form-data"`, `htmx:xhr:progress` event
- [HTMX multi-step form pattern](https://medium.com/@alexander.heerens/htmx-patterns-01-how-to-build-a-multi-step-form-in-htmx-554d4c2a3f36) — partial swap approach for wizard flows
- [FastAPI SSE tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/) — SSE pattern reference (not needed for Phase 3's synchronous chat)
- [pdfplumber 2025 review](https://onlyoneaman.medium.com/i-tested-7-python-pdf-extractors-so-you-dont-have-to-2025-edition-c88013922257) — confirmed pdfplumber still recommended for tabular machine-generated PDFs in 2025

### Tertiary (LOW confidence — not needed, documented for completeness)

- None needed. Phase 3 relies entirely on established stack components.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and used in the codebase
- Architecture patterns: HIGH — directly derived from established Phase 1/2 patterns in the codebase
- Data model: HIGH — straightforward SQLModel extending existing migration chain
- Pitfalls: HIGH — directly sourced from PITFALLS.md (prior research) + TOS constraints from CLAUDE.md
- NL chat HTMX pattern: MEDIUM — derived from documented HTMX patterns, not from a production reference

**Research date:** 2026-04-04
**Valid until:** 2026-05-04 (stable stack; no fast-moving dependencies added)
