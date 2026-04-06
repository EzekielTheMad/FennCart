# Phase 2: Core Loop - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-03
**Phase:** 02-core-loop
**Areas discussed:** Shopping list input, Match review UX, Cart confirmation flow, LLM matching behavior

---

## Shopping List Input

| Option | Description | Selected |
|--------|-------------|----------|
| Simple textarea | One big text area, each line = one item | |
| Smart textarea with preview | Textarea + live preview parsing lines into structured items | ✓ |
| Structured form | Individual fields per item (name, quantity, unit) | |

**User's choice:** Smart textarea with preview
**Notes:** Live preview uses HTMX partial updates to parse lines into structured items below the textarea.

### Quantity Parsing

| Option | Description | Selected |
|--------|-------------|----------|
| LLM handles everything | Send raw text to LLM for parsing + matching | |
| Pre-parse then LLM | Regex first, then structured data to LLM | |
| You decide | Claude picks best approach | ✓ |

**User's choice:** You decide (Claude's discretion)

### Empty State

| Option | Description | Selected |
|--------|-------------|----------|
| Inline error | Error message below textarea | |
| Helpful empty state | Example lists and tips | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

### List Persistence

| Option | Description | Selected |
|--------|-------------|----------|
| No persistence | Fresh textarea every time | ✓ |
| Session only | Browser session storage | |
| Save to database | Persist in SQLite | |

**User's choice:** No persistence

---

## Match Review UX

### Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Product cards | Card grid with images, names, prices | |
| Compact table | Dense table rows | |
| Hybrid cards/table | Cards for review items, table for auto-matched | ✓ |

**User's choice:** Hybrid cards/table

### Confidence Display

| Option | Description | Selected |
|--------|-------------|----------|
| Color-coded badges | Green/yellow/red badges | |
| Percentage score | Show actual % | |
| Hidden unless low | Only flag uncertain items | ✓ |
| You decide | Claude picks | |

**User's choice:** Hidden unless low

### Alternatives

| Option | Description | Selected |
|--------|-------------|----------|
| Dropdown swap | Click product to see dropdown of alternatives | ✓ |
| Expandable row | Click to expand and see alternatives below | |
| You decide | Claude picks | |

**User's choice:** Dropdown swap

### Review Mode Toggle

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle switch at top | Switch: "Show all" vs "Exceptions only" | |
| Tab-style selector | Two tabs with counts | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

---

## Cart Confirmation Flow

### Confirm Action

| Option | Description | Selected |
|--------|-------------|----------|
| One-click confirm all | Single button adds all items | |
| Checkbox select then confirm | Checkboxes per item, then confirm selected | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

### Progress Display

| Option | Description | Selected |
|--------|-------------|----------|
| Progress bar | "Adding item 3 of 12..." | |
| Item-by-item status | Individual spinners per item | |
| Simple spinner | One spinner until done | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

### Success Screen

| Option | Description | Selected |
|--------|-------------|----------|
| Summary with link | Count, total, link to Fry's pickup | |
| Full receipt view | Detailed list of every item | |
| Both with toggle | Summary default, expandable to full list | ✓ |

**User's choice:** Both with toggle

### Failure Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Retry failed items | Show failures with retry button | |
| Report and move on | Show success count, list failures | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

---

## LLM Matching Behavior

### Ambiguity Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Best guess + flag | LLM picks most common option, flags as low confidence | |
| Ask for clarification | Prompt user before searching | |
| Search broadly, rank results | Search Kroger broadly, LLM ranks | |
| Preference-driven | Use preference profile if available, otherwise best guess + flag | ✓ |

**User's choice:** Custom — "Can we capture this in user trends and preferences and go off that unless the user specifies otherwise?"
**Notes:** User wants ambiguity resolution tied to the preference system (Phase 3). For Phase 2, this means LLM best-guesses and flags for review. The matching interface is designed to accept preference context from day one.

### Result Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Top 5 | Fast, focused | |
| Top 10 | More options for LLM | |
| You decide | Claude picks based on rate limits and token costs | ✓ |

**User's choice:** You decide (Claude's discretion)

### Streaming

| Option | Description | Selected |
|--------|-------------|----------|
| All at once | Process full list, show all results together | ✓ |
| Stream item by item | Show each match as it completes | |
| You decide | Claude picks | |

**User's choice:** All at once

### LLM Call Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| One batch call | Entire list to LLM at once | |
| Per-item calls | One LLM call per item | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide (Claude's discretion)

---

## Claude's Discretion

- Quantity/unit parsing approach (LLM-only vs regex pre-parse)
- Empty/short list handling UX
- Cart confirmation flow (one-click vs checkbox)
- Progress indicator style during cart addition
- Error handling for failed cart additions
- Exceptions-only vs full review toggle UX
- Number of Kroger product results per search
- LLM call strategy (batch vs per-item)

## Deferred Ideas

None — discussion stayed within phase scope.
