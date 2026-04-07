# Phase 3: Preference System - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 03-preference-system
**Areas discussed:** Receipt upload & parsing, Preference profile structure, NL preference updates, Preferences UI & management

---

## Receipt Upload & Parsing

### Upload approach

| Option | Description | Selected |
|--------|-------------|----------|
| Single file upload with instant parse | Upload one PDF at a time, immediately parse and show extracted items | |
| Batch upload with queue | Upload multiple PDFs at once, parse in background | |
| You decide | Claude picks the approach | ✓ |

**User's choice:** You decide
**Notes:** Claude's discretion on upload approach.

### Parse review display

| Option | Description | Selected |
|--------|-------------|----------|
| Editable table of extracted items | Parsed items in editable table, user can fix OCR errors before saving | ✓ |
| Read-only preview with accept/reject | Show parsed items as read-only, accept whole batch or reject | |
| You decide | Claude picks | |

**User's choice:** Editable table of extracted items
**Notes:** User wants control over parsed data before it enters the preference system.

### Bad receipt handling

| Option | Description | Selected |
|--------|-------------|----------|
| Show what parsed with warnings | Parse what you can, flag uncertain lines | |
| Reject and explain | Reject below confidence threshold | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide
**Notes:** Claude's discretion on error handling approach.

---

## Preference Profile Structure

### Frequency weighting

| Option | Description | Selected |
|--------|-------------|----------|
| Simple count-based | More purchases = stronger preference | |
| Recency-weighted | Recent purchases count more | |
| You decide | Claude picks to satisfy PREF-03 | ✓ |

**User's choice:** You decide
**Notes:** Must support distinguishing recurring preferences from one-off substitutions.

### Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Category-based grouping | Group by dairy, produce, meat, etc. | |
| Flat list by product | Each preference standalone entry | ✓ |

**User's choice:** Flat list by product
**Notes:** Simpler storage, search-based browsing.

### Contradiction handling

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-update silently | New data adjusts weights automatically | |
| Flag and ask | Detect brand switches and ask user | ✓ |
| You decide | Claude picks | |

**User's choice:** Flag and ask
**Notes:** User wants control over brand switches vs one-time substitutions.

---

## NL Preference Updates

### Input method

| Option | Description | Selected |
|--------|-------------|----------|
| Text field on preferences page | Single-purpose text input, submit | |
| Chat-style interface | Conversational back-and-forth with clarifying questions | ✓ |
| You decide | Claude picks | |

**User's choice:** Chat-style interface
**Notes:** LLM can ask follow-ups for ambiguous preference updates.

### Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Always confirm | Show interpreted change, require approval | ✓ |
| Apply immediately, undo available | Instant apply with undo toast | |
| You decide | Claude picks | |

**User's choice:** Always confirm
**Notes:** Must show the interpreted change before saving.

---

## Preferences UI & Management

### Page layout

| Option | Description | Selected |
|--------|-------------|----------|
| Two-panel: chat left, list right | Both visible at once | |
| Tabbed: Upload / Chat / List | Three tabs separating modes | |
| Single scrollable page | All stacked vertically | |
| You decide | Claude picks to fit sidebar nav pattern | ✓ |

**User's choice:** You decide
**Notes:** Must accommodate three modes: receipt upload, NL chat, manual list.

### Editing pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Inline editing | Click to edit in place | |
| Edit modal/drawer | Side drawer with all fields | |
| You decide | Claude picks | ✓ |

**User's choice:** You decide

### Bulk operations

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, with checkboxes | Checkbox per entry, select multiple, bulk delete | ✓ |
| Single delete only | Delete one at a time | |
| You decide | Claude picks | |

**User's choice:** Yes, with checkboxes
**Notes:** Useful for cleanup after bad receipt upload or starting fresh.

---

## Claude's Discretion

- Receipt upload UX approach (single vs batch)
- Bad receipt error handling pattern
- Preference weighting algorithm
- Preferences page layout
- Individual preference editing pattern
- Chat interface implementation pattern

## Deferred Ideas

None — discussion stayed within phase scope.
