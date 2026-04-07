---
phase: 03
phase_name: preference-system
status: draft
created: 2026-04-04
design_system: tailwind-cdn-play
---

# UI-SPEC: Phase 3 — Preference System

**Phase goal:** Users can bootstrap and maintain a preference profile that makes product matching accurate to their actual buying habits.

**Requirements covered:** PREF-01, PREF-02, PREF-03, PREF-04, PREF-05, PREF-06

---

## 1. Design System

**Tool:** Tailwind CSS CDN play build (no shadcn — SSR/Jinja2 project with no Node.js pipeline)
**Registry:** Not applicable
**Safety Gate:** Not applicable

All styling uses Tailwind utility classes inline in Jinja2 templates, consistent with Phase 1 and Phase 2. No `tailwind.config.js` theme extension required — use default Tailwind slate/green palette already established.

---

## 2. Spacing Scale

Standard 8-point scale. Only multiples of 4 are permitted.

| Token | px | Usage |
|-------|----|-------|
| `space-1` | 4px | Icon-to-label gaps, tight inline gaps |
| `space-2` | 8px | Compact intra-element spacing (tag padding, icon padding, form field internal vertical padding) |
| `space-4` | 16px | Standard element padding, card internal padding |
| `space-6` | 24px | Section vertical spacing between grouped elements |
| `space-8` | 32px | Major section separators |
| `py-8 px-4` | 32px / 16px | Main content area — matches shopping.html established pattern |
| `max-w-2xl mx-auto` | — | Content column width — matches shopping.html established pattern |

**Touch targets:** All interactive elements (buttons, checkboxes, tab triggers, delete icons) must have `min-h-[44px]` to meet 44px minimum touch target. Source: base.html nav items establish this pattern.

**Exception:** Inline table cells with edit icons may use `min-h-[36px]` when embedded inside a scrollable table. The containing row must be at least 36px tall; standalone action buttons remain 44px.

---

## 3. Typography

Source: base.html body uses `font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, sans-serif` — system font stack, no custom typeface.

### Font Sizes (exactly 4 in use)

| Role | Tailwind Class | px | Usage |
|------|---------------|-----|-------|
| Page heading | `text-xl font-semibold` | 20px | Page title ("Preferences") — matches shopping.html h1 |
| Body / default | `text-base` | 16px | Form labels, preference entry text, chat messages |
| Supporting / metadata | `text-sm` | 14px | Sub-labels, timestamps, item counts, parse warnings, tab labels |
| Micro / badge | `text-xs` | 12px | Confidence badges, source tags ("receipt", "manual"), bulk select count |

### Font Weights (exactly 2)

| Weight | Tailwind Class | Usage |
|--------|---------------|-------|
| Regular | `font-normal` (400) | Body text, supporting labels, preference entry notes |
| Semibold | `font-semibold` (600) | Page headings, primary values (brand name, product name), button labels |

### Line Heights

| Context | Value | Tailwind |
|---------|-------|---------|
| Body paragraphs | 1.5 | `leading-normal` (Tailwind default) |
| Headings | 1.2 | `leading-tight` |
| Table cells | 1.4 | Default — no explicit class needed |

---

## 4. Color Contract

Source: base.html and existing partials establish the slate palette. No new colors introduced in Phase 3.

### 60 / 30 / 10 Split

| Role | Color | Tailwind | Surfaces |
|------|-------|---------|---------|
| 60% dominant background | slate-950 | `bg-slate-950` | Page body, main content area |
| 30% secondary | slate-900 / slate-800 | `bg-slate-900`, `bg-slate-800` | Sidebar (slate-900), cards and panels (slate-800), table rows |
| 10% accent | green-500 / green-600 | `text-green-500`, `bg-green-600` | Reserved exclusively for: active nav indicator border, primary CTA buttons, confirmed/success states, spinner |

### Semantic Colors

| Semantic | Color | Tailwind | Reserved For |
|---------|-------|---------|-------------|
| Destructive | red-400 text / red-950 bg / red-800 border | `text-red-400 bg-red-950 border-red-800` | Delete confirmation dialogs, parse error blocks, bulk delete button in active state — matches error_block.html |
| Warning / uncertain | amber-400 | `text-amber-400` | Contradiction detection flag ("Different brand detected"), low-confidence parse items, partial receipt warning — matches review_card.html "Uncertain match" badge |
| Muted / inactive | slate-400 | `text-slate-400` | Secondary labels, empty state text, inactive tab text, placeholder text — matches shopping.html |
| Borders | slate-700 | `border-slate-700` | All card borders, table borders, form input borders — established across Phase 1 and Phase 2 |

### Contradiction Flag Color

Contradiction cards (D-06) use amber-400 to match the "Uncertain match" badge established in review_card.html. This reuses an existing semantic color rather than introducing a new one.

---

## 5. Page Layout

**Container:** Extends `base.html` with `{% set active_page = "preferences" %}`. Content area uses `max-w-2xl mx-auto py-8 px-4` matching shopping.html.

**Primary focal point:** The Preferences List tab panel is the primary visual anchor of the page. It is the default active tab and the surface where all preference data lives — receipt upload and chat are entry methods that feed into it. The list panel occupies the full content column width and should feel like the destination, not a secondary view.

### Tab Structure (D-09 — Claude's discretion resolved)

Three-tab layout using Alpine.js `x-data="{tab: 'list'}"`. Tabs sit at the top of the content area below the page heading. Default active tab: "Preferences" (list view).

```
┌─ sidebar ─┐ ┌──────────────── main content ────────────────────┐
│           │ │ Preferences                                       │
│  nav      │ │ [Preferences List] [Receipt Upload] [Update Chat] │
│  items    │ │ ─────────────────────────────────────────────────  │
│           │ │ {tab panel content}                               │
└───────────┘ └───────────────────────────────────────────────────┘
```

**Tab bar implementation:**

- Container: `border-b border-slate-700 mb-6 flex gap-1`
- Inactive tab: `px-4 py-2 text-sm text-slate-400 hover:text-slate-100 transition-colors cursor-pointer`
- Active tab: `px-4 py-2 text-sm font-semibold text-slate-100 border-b-2 border-green-500 -mb-px`
- No server round-trip on tab switch — all three panels rendered on page load, `x-show` toggles visibility
- Tab keyboard navigation: each tab is a `<button>` element, not `<div>`, for native keyboard focus

---

## 6. Component Inventory

### 6.1 Tab: Preferences List (PREF-05)

**Purpose:** Browse, search, add, edit, and delete individual preference entries.

**Empty state:**
- Text: "No preferences yet. Upload a receipt or use the chat to teach FennCart your habits."
- No illustration — text only, centered, `text-slate-400 text-sm text-center py-16`
- CTA: "Upload a receipt" link (text-green-500, switches to Receipt Upload tab)

**Search/filter bar:**
- Input: `bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-base px-4 py-2 w-full placeholder:text-slate-500 focus:outline-none focus:border-green-500`
- HTMX: `hx-get="/preferences/list" hx-trigger="input delay:300ms" hx-target="#pref-list-container" hx-swap="innerHTML"`
- Placeholder: "Search by product or brand..."

**Preference entry row (flat list, D-05):**

```
┌──────────────────────────────────────────────────────────────────┐
│ [checkbox] Tillamook Medium Cheddar    cheddar cheese   ×4   [⋯] │
│            Source: receipt · Last seen: 3 weeks ago              │
└──────────────────────────────────────────────────────────────────┘
```

- Row: `bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 flex items-start gap-3`
- Product name + brand: `text-base font-semibold text-slate-100`
- Category: `text-sm text-slate-400`
- Purchase count badge: `text-xs bg-slate-700 text-slate-300 rounded-full px-2 py-1` — e.g. "×4"
- Source + last seen: `text-xs text-slate-500 mt-1`
- Recurring badge (purchase_count >= 2): `text-xs text-green-500` — "Established"
- One-off badge (purchase_count == 1): `text-xs text-amber-400` — "Seen once"
- Edit trigger: `...` icon button (Heroicons `ellipsis-horizontal`, 20px) at row end

**Inline edit (D-10 — Claude's discretion resolved to inline):**

On edit trigger click, the row transforms into an editable form in-place via HTMX:
- `hx-get="/preferences/{id}/edit-form"` swaps the row with an edit form partial
- Edit form shows: product name input, brand input, category input, notes textarea
- Actions: "Save changes" (green button) + "Discard changes" (slate ghost button) in a `flex gap-2 mt-3`
- On save: `hx-put="/preferences/{id}"` swaps back to the display row
- On cancel: `hx-get="/preferences/{id}/row"` swaps back to the display row
- Reason for inline over modal: fits the single-column narrow layout; modals add overlay complexity HTMX doesn't manage well

**Bulk delete (D-11):**

- Checkbox: `w-4 h-4 accent-green-500 rounded cursor-pointer` (CSS accent-color for checkbox theming)
- Bulk action bar appears when any checkbox is selected (Alpine.js `x-show="selectedCount > 0"`):
  - Position: sticky at bottom of list panel, `bg-slate-900 border-t border-slate-700 px-4 py-2 flex items-center gap-4`
  - Text: `text-sm text-slate-400` — "{N} selected"
  - Delete button: `bg-red-900 hover:bg-red-800 text-red-400 font-semibold py-2 px-4 rounded-lg text-sm min-h-[44px]` — "Delete selected"
  - Confirmation: inline confirmation text replaces button text — "Delete {N} preferences? This cannot be undone. [Confirm] [Cancel]"

**Add new entry button:**

- `bg-slate-800 border border-slate-700 border-dashed rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-slate-100 hover:border-slate-500 w-full text-left transition-colors`
- Label: "+ Add preference manually"
- Clicking expands an inline add form (same field set as edit form, but blank)

---

### 6.2 Tab: Receipt Upload (PREF-01, PREF-02, PREF-03)

**Purpose:** Upload a Fry's receipt PDF, review parsed items, resolve contradictions, save to preference history.

**Upload approach (D-01 — Claude's discretion resolved to single-file with progress):**

Single file upload per session. Batch upload adds complexity to the contradiction resolution flow (multiple receipts could create overlapping contradictions). Single file keeps the review step linear.

**Upload drop zone:**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│          [PDF icon]  Drop your Fry's receipt PDF here           │
│                 or click to choose a file                       │
│                                                                 │
│                 Accepts: PDF files only                         │
└─────────────────────────────────────────────────────────────────┘
```

- Container: `border-2 border-dashed border-slate-700 rounded-lg p-12 text-center bg-slate-800 hover:border-green-500 transition-colors cursor-pointer`
- Active drag state (Alpine.js `@dragover` / `@dragleave`): `border-green-500 bg-slate-700`
- Icon: Heroicons `document` (24px, `text-slate-400`)
- Heading: `text-base font-semibold text-slate-100 mt-4`
- Sub-text: `text-sm text-slate-400 mt-1`
- Hidden file input: `accept=".pdf"` — triggered by clicking the drop zone
- Submit form: `hx-post="/preferences/upload" hx-encoding="multipart/form-data" hx-target="#receipt-panel" hx-swap="innerHTML" hx-indicator="#upload-spinner"`

**Upload progress indicator:**

- HTMX spinner identical to loading_spinner.html: `animate-spin w-8 h-8 text-green-500`
- Text: "Parsing your receipt..." (sub-text: "This takes a few seconds while FennCart reads your PDF.")

**Bad receipt handling (D-03 — Claude's discretion resolved to partial results with warnings):**

Show whatever was parsed with inline warnings rather than rejecting. Zero-item results get a clear error; partial results get a yellow warning banner.

- Warning banner: `bg-amber-950 border border-amber-800 rounded-lg px-4 py-2 text-sm text-amber-400 mb-4`
- Warning text: "Some items could not be read. Review carefully before saving."
- Zero items error: reuses error_block.html with `error_heading="Could not read this receipt"` and `error_body="FennCart couldn't extract items from this PDF. Try a different receipt format, or add preferences manually."`

**Parsed receipt review table (D-02):**

```
┌────────────────────────────────────────────────────────────────────────┐
│ Found 23 items from your receipt. Review and correct before saving.    │
│                                                                        │
│  Product                Brand          Size    Qty   Price    [✕]     │
│ ┌──────────────────────────────────────────────────────────────────┐   │
│ │ 2% Milk               Organic Valley  1 gal   1   $4.99    [✕]  │   │
│ │ Medium Cheddar        Tillamook       32 oz   1   $8.49    [✕]  │   │
│ │ ?Chicken Brst (low ⚠) [unknown]       2 lb    1   $6.99    [✕]  │   │
│ └──────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│                                          [Save preferences]            │
└────────────────────────────────────────────────────────────────────────┘
```

- Item count header: `text-sm text-slate-400 mb-4` — "Found {N} items from your receipt. Review and correct before saving."
- Table container: `overflow-x-auto`
- Table: `w-full text-sm border-collapse`
- Header row: `text-xs text-slate-500 uppercase tracking-wide border-b border-slate-700`
- Data row: `border-b border-slate-800 hover:bg-slate-750` (use `hover:bg-slate-800/50`)
- Editable cells: `contenteditable="true"` on product name, brand, size fields — styled with `focus:outline-none focus:bg-slate-700 rounded px-1`
- Low-confidence row: `text-amber-400` for cells where confidence < 0.7 — amber color signals "please verify"
- Remove row button: `text-slate-500 hover:text-red-400 transition-colors` — Heroicons `x-mark` (16px)
- Save button: `bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg min-h-[44px]` — "Save {N} preferences"
- Save button disabled state: `opacity-60 cursor-not-allowed` when 0 items remain in table

**Contradiction detection panel (D-06):**

Appears between the review table and the Save button when contradictions are detected. Never skippable — user must resolve each before saving.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Brand change detected                                                 │
│                                                                        │
│  You usually buy Tillamook cheddar (4 purchases).                      │
│  This receipt shows Kroger Private Selection cheddar.                  │
│                                                                        │
│  [New preference — switch to Kroger]  [One-time substitution — keep Tillamook] │
└────────────────────────────────────────────────────────────────────────┘
```

- Container: `bg-amber-950 border border-amber-800 rounded-lg px-4 py-4 mb-4`
- Heading: `text-sm font-semibold text-amber-400 mb-2` — "Brand change detected"
- Body: `text-sm text-slate-300`
- "New preference" button: `bg-slate-700 hover:bg-slate-600 text-slate-100 font-semibold py-2 px-4 rounded-lg text-sm min-h-[44px]`
- "One-time substitution" button: `bg-slate-800 hover:bg-slate-700 text-slate-400 font-semibold py-2 px-4 rounded-lg text-sm border border-slate-700 min-h-[44px]`
- Multiple contradictions: each card stacked vertically with `space-y-3`, must resolve all before Save becomes active

---

### 6.3 Tab: Update via Chat (PREF-04)

**Purpose:** Natural language preference updates via conversational HTMX interface.

**Chat container:**

- Outer: `flex flex-col gap-4` within tab panel
- Intro text (shown when no conversation): `text-sm text-slate-400 mb-4` — "Tell FennCart about your preferences in plain language. For example: 'we switched to oat milk' or 'stop buying Kroger brand yogurt'."
- Chat history: `space-y-3 mb-4` — id="chat-history", HTMX `hx-swap="beforeend"` appends new messages

**User message bubble:**

```
                                           ┌─────────────────────────┐
                                           │ we switched to oat milk │
                                           └─────────────────────────┘
```

- Wrapper: `flex justify-end`
- Bubble: `bg-green-600 text-white rounded-lg rounded-br-sm px-4 py-2 text-sm max-w-[75%]`

**Assistant message bubble:**

```
┌──────────────────────────────────────────┐
│ Got it. I'll update your milk preference │
│ from whole milk to oat milk.             │
│                                          │
│ Interpreted as:                          │
│ Replace "whole milk" with "oat milk"     │
│ in the milk category.                    │
│                                          │
│ [Apply this change]  [Discard change]    │
└──────────────────────────────────────────┘
```

- Wrapper: `flex justify-start`
- Bubble: `bg-slate-800 border border-slate-700 text-slate-100 rounded-lg rounded-bl-sm px-4 py-2 text-sm max-w-[85%]`
- Clarification question (action=="clarify"): bubble without action buttons — just shows the question, then scrolls to input
- Confirmation preview (action != "clarify"): includes a highlighted `Interpreted as:` block:
  - Block: `bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm text-slate-300 mt-2 mb-3`
  - `text-slate-500 text-xs uppercase tracking-wide mb-1` — "Interpreted as:"
  - `font-semibold text-slate-100` for the human_summary value

**Confirmation action buttons (D-08):**

- Container: `flex gap-2 mt-3`
- Apply button: `bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-4 rounded-lg text-sm min-h-[44px]` — "Apply this change"
- Discard button: `bg-slate-700 hover:bg-slate-600 text-slate-100 font-semibold py-2 px-4 rounded-lg text-sm min-h-[44px] border border-slate-600` — "Discard change"

**Chat input form:**

- Container: `flex gap-2 mt-2`
- Input: `flex-1 bg-slate-800 border border-slate-700 rounded-lg text-slate-100 text-base px-4 py-2 placeholder:text-slate-500 focus:outline-none focus:border-green-500`
- Placeholder: "Type a preference update..."
- Submit button: `bg-green-600 hover:bg-green-700 disabled:opacity-60 text-white font-semibold px-6 rounded-lg min-h-[44px]` — "Send message"
- Button disabled when input is empty (Alpine.js `:disabled="chatInput.trim().length === 0"`)
- HTMX: `hx-post="/preferences/chat" hx-target="#chat-history" hx-swap="beforeend" hx-indicator="#chat-spinner"`
- After submit: clear input field, scroll chat history to bottom via Alpine.js `$nextTick`

**Chat loading indicator:**

- Inline typing indicator appended to chat history during HTMX request
- Three dots animation: `flex gap-1` with three `w-2 h-2 bg-slate-500 rounded-full animate-pulse` at staggered delays
- Wrapper matches assistant bubble style: `bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 max-w-[85%]`

---

### 6.4 Preference Active Indicator in Shopping Flow (PREF-06)

When preferences are loaded and passed to `match_products()`, the shopping review screen should display a subtle indicator that preferences influenced the results.

- Banner: `bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-sm text-slate-400 flex items-center gap-2 mb-4`
- Icon: Heroicons `heart` (16px, `text-green-500`)
- Text: "Matching with your preferences" — no count, no link (keeps it minimal)
- This is a new partial added to the shopping review template in Phase 3 — only rendered when `preferences_loaded == True` in template context

---

## 7. Interaction States

### Loading States

| Trigger | Indicator | Location |
|---------|-----------|---------|
| Receipt PDF upload + parse | Full-panel spinner (loading_spinner.html pattern) | Replaces upload drop zone via `hx-target="#receipt-panel" hx-swap="innerHTML"` |
| NL chat LLM response | Typing indicator bubble appended to chat history | `hx-target="#chat-history" hx-swap="beforeend"` |
| Preference list search filter | None (300ms debounce makes it feel instant) | In-place list refresh |
| Save preferences (post review) | Button text changes to "Saving..." + disabled state | Submit button itself |

### Error States

| Error | Copy | Treatment |
|-------|------|-----------|
| Receipt PDF parse failure (0 items) | "Could not read this receipt" / "FennCart couldn't extract items from this PDF. Try a different receipt format, or add preferences manually." | Reuses `error_block.html` with `show_retry=True` |
| Receipt PDF parse partial (< 50% confidence average) | "Some items could not be read. Review carefully before saving." | Amber warning banner above review table |
| Chat LLM failure | "Something went wrong. Try again or edit your preferences directly in the list." | Inline error bubble in chat history (matches assistant bubble style but with red-400 text) |
| Inline edit save failure | "Could not save. Try again." | Inline `text-red-400 text-xs` below edit form |
| Bulk delete failure | "Delete failed. Try again." | Bulk action bar text, `text-red-400` |

### Empty States

| Surface | Copy | Treatment |
|---------|------|-----------|
| Preferences list (no entries) | "No preferences yet. Upload a receipt or use the chat to teach FennCart your habits." | Centered in list panel, `text-slate-400 text-sm text-center py-16` + "Upload a receipt" link |
| Chat (no conversation) | "Tell FennCart about your preferences in plain language. For example: 'we switched to oat milk' or 'stop buying Kroger brand yogurt'." | `text-sm text-slate-400` intro above input form |
| Preference search (no results) | "No preferences match '{query}'." | Inline in list container, `text-slate-400 text-sm text-center py-8` |

### Destructive Actions

| Action | Confirmation Pattern |
|--------|---------------------|
| Delete single preference | No pre-confirmation modal — single entry deletion is low-stakes. Row is removed immediately. Undo is not available (inform user upfront in tooltip: "Deletes immediately"). |
| Bulk delete preferences | Inline confirmation replaces the "Delete selected" button: "Delete {N} preferences? This cannot be undone. [Confirm] [Cancel]" |
| Discard parsed receipt (abandon review) | No confirmation — navigating away from the receipt review via tab switch or browser back simply discards the unsaved parse result. The upload was not saved; no confirmation needed. |

---

## 8. Copywriting Contract

### Primary CTAs

| Surface | Label | Verb rationale |
|---------|-------|---------------|
| Receipt upload submit | "Parse receipt" | Describes what happens (not "Upload" which is the action already taken) |
| Receipt review save | "Save {N} preferences" | Specific count creates transparency about what is being committed |
| Chat preference apply | "Apply this change" | Explicit about the action being irreversible without a separate delete |
| Chat preference discard | "Discard change" | Parallel structure with "Apply this change"; noun makes the scope explicit |
| Chat submit button | "Send message" | Verb + noun; distinguishes from other send actions in the app |
| Add manual preference | "+ Add preference manually" | Verb-first; "manually" distinguishes from other entry methods |
| Bulk delete (confirm) | "Delete {N} preferences? This cannot be undone." | Irreversibility is stated clearly rather than implied |
| Inline edit confirm | "Save changes" | Scoped verb + noun distinguishes from page-level save actions |
| Inline edit abandon | "Discard changes" | Mirrors "Save changes" structurally; makes the consequence explicit |

### Status Labels

| State | Label |
|-------|-------|
| Established preference (count >= 2) | "Established" (green-500) |
| Observed once (count == 1) | "Seen once" (amber-400) |
| Preference source: receipt | "receipt" |
| Preference source: NL chat | "chat" |
| Preference source: manual | "manual" |

### Preference Badge Tooltip Text (on hover, Alpine.js `x-tooltip` or `title` attribute)

| Badge | Title text |
|-------|-----------|
| "Established" | "Seen {N} times across your receipts" |
| "Seen once" | "Only seen once — will not influence matching until seen again" |

---

## 9. HTMX Partial Map

| Partial Template | Endpoint | Target | Trigger |
|-----------------|----------|--------|---------|
| `partials/pref_list.html` | `GET /preferences/list?q=` | `#pref-list-container` | Search input 300ms debounce |
| `partials/pref_row.html` | `GET /preferences/{id}/row` | `#pref-row-{id}` | Discard inline edit |
| `partials/pref_edit_form.html` | `GET /preferences/{id}/edit-form` | `#pref-row-{id}` | Edit trigger click |
| `partials/pref_row.html` | `PUT /preferences/{id}` | `#pref-row-{id}` | Edit form save changes |
| `partials/receipt_upload_form.html` | N/A — initial render | N/A | Tab switch to Receipt Upload |
| `partials/receipt_review.html` | `POST /preferences/upload` | `#receipt-panel` | File form submit |
| `partials/receipt_contradictions.html` | Embedded in receipt_review.html | N/A | Rendered inline when contradictions exist |
| `partials/chat_message.html` | `POST /preferences/chat` | `#chat-history` | Chat send (beforeend swap) |

---

## 10. Accessibility Contract

- All icon-only buttons (edit trigger, row delete, close) must have `aria-label` with a descriptive label (e.g., `aria-label="Edit Tillamook Medium Cheddar preference"`)
- Tab triggers are `<button>` elements, not `<div>` — native keyboard focus
- Active tab: `aria-selected="true"` on the active tab button
- Editable table cells: `contenteditable="true"` cells must also have `aria-label` describing the field (e.g., `aria-label="Edit brand name"`)
- Chat loading indicator: `aria-live="polite"` on `#chat-history` container so screen readers announce new messages
- Error blocks: use `role="alert"` on error containers so errors are announced immediately
- Checkboxes: each has an `aria-label` matching the preference entry it controls (e.g., `aria-label="Select Tillamook Medium Cheddar for bulk action"`)
- Contradiction cards: `role="region"` with `aria-label="Brand change detected for {category}"`

---

## 11. Source Traceability

| Decision | Source | Field |
|----------|--------|-------|
| Tailwind slate palette, no custom tokens | `tailwind.config.js` — `theme: { extend: {} }` (no extensions) | Design system |
| System font stack | `base.html` body style | Typography |
| `max-w-2xl mx-auto py-8 px-4` layout | `shopping.html` established pattern | Spacing / layout |
| `min-h-[44px]` touch targets | `base.html` nav items | Spacing |
| slate-800 card backgrounds | `review_card.html`, `error_block.html` | Color |
| `border-slate-700` borders | All existing partials | Color |
| amber-400 for uncertainty | `review_card.html` "Uncertain match" badge | Color semantic |
| `bg-red-950 border-red-800 text-red-400` for errors | `error_block.html` | Color semantic |
| Three-tab layout | CONTEXT.md D-09, RESEARCH.md Pattern 7 | Layout |
| Inline edit (not modal) | Claude's discretion (D-10) — narrow single-column layout | Interaction |
| Single-file upload (not batch) | Claude's discretion (D-01) — linear contradiction review flow | Upload UX |
| Partial results with warnings (not reject) | Claude's discretion (D-03) | Error handling |
| `beforeend` HTMX swap for chat | RESEARCH.md Pattern 6 | Interaction |
| Contradiction amber banner | CONTEXT.md D-06 — flag-and-ask mandatory | Color / interaction |
| `space-3` (12px) removed from spacing scale | UI-SPEC revision 2026-04-05 — checker blocks non-standard spacing units; all `py-3` replaced with `py-2` | Spacing |
| "Save changes" / "Discard changes" inline edit labels | UI-SPEC revision 2026-04-04 — checker flag on generic labels | Copywriting |
| "Send message" chat submit label | UI-SPEC revision 2026-04-05 — checker flag on bare verb; added noun for clarity | Copywriting |
| "Discard change" chat discard label | UI-SPEC revision 2026-04-05 — checker flag; parallelism with "Apply this change" | Copywriting |
| Preference list as primary focal point | UI-SPEC revision 2026-04-04 — checker visual anchor recommendation | Layout |

---

*Phase: 03-preference-system*
*UI-SPEC created: 2026-04-04*
*UI-SPEC revised: 2026-04-05 — fixes: removed space-3/12px from spacing scale (checker D5 blocker), replaced all py-3 with py-2, changed "Send" to "Send message" (checker D1), changed "Discard" to "Discard change" (checker D1)*
*Status: draft — awaiting gsd-ui-checker validation*
