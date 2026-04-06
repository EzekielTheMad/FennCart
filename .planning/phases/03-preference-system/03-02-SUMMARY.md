---
phase: 03-preference-system
plan: "02"
subsystem: ui
tags: [htmx, alpine, jinja2, fastapi, preferences, receipt-upload, pdfplumber]
dependency_graph:
  requires:
    - phase: 03-01
      provides: PreferenceService, ReceiptParser, all preference schemas and models
  provides:
    - app/routers/preferences.py (10 endpoints for preference CRUD + receipt upload/review)
    - templates/pages/preferences.html (three-tab preferences page)
    - templates/partials/pref_list.html (HTMX searchable preference list)
    - templates/partials/pref_row.html (display row with badges and edit trigger)
    - templates/partials/pref_edit_form.html (inline edit form)
    - templates/partials/receipt_upload_form.html (drag-and-drop PDF upload)
    - templates/partials/receipt_review.html (editable parsed receipt table)
    - templates/partials/receipt_contradictions.html (brand-change resolution cards)
  affects:
    - app/routers/pages.py (updated /preferences GET to load entries)
    - app/main.py (preferences router registered)
    - 03-03 (NL chat endpoints and chat_message.html partial)
    - 03-04 (test suite covers all 10 preference endpoints)
tech_stack:
  added: []
  patterns:
    - Router-local Jinja2Templates (matching shopping.py pattern)
    - Alpine.js x-data tab state on preferences page with three panels
    - HTMX outerHTML swap for inline edit (pref_row ↔ pref_edit_form)
    - Server-side session for receipt parse state (receipt_items, receipt_contradictions, receipt_upload_id)
    - Alpine.js bulk-select with sticky action bar and inline confirmation
    - contenteditable="true" cells in receipt review table for in-place editing
    - htmx-indicator pattern for receipt upload spinner
key_files:
  created:
    - app/routers/preferences.py
    - templates/pages/preferences.html
    - templates/partials/pref_list.html
    - templates/partials/pref_row.html
    - templates/partials/pref_edit_form.html
    - templates/partials/receipt_upload_form.html
    - templates/partials/receipt_review.html
    - templates/partials/receipt_contradictions.html
  modified:
    - app/routers/pages.py
    - app/main.py
decisions:
  - "Contradiction resolution index uses loop.index0 in Jinja2 so the form posts the correct 0-based index back to /receipt/resolve"
  - "receipt/save clears session keys (receipt_items, receipt_contradictions, receipt_upload_id) after commit to prevent stale state on reload"
  - "Try-another-receipt button on error state uses onclick to reset receipt-panel client-side rather than an extra GET endpoint"
  - "pref_list.html uses {% include pref_row.html %} loop rather than duplicating row markup — pref-row- ID pattern lives in pref_row.html"
  - "allResolved Alpine flag initialised from server-rendered contradiction list; resolves to true when contradictions list is empty at render time"
requirements_completed: [PREF-01, PREF-05]
metrics:
  duration: "~3 min"
  completed_date: "2026-04-06"
  tasks_completed: 2
  files_created: 8
  files_modified: 2
---

# Phase 03 Plan 02: Preferences Router and UI Summary

**Preferences router (10 endpoints), three-tab preferences page, and 6 HTMX partials wiring receipt upload/parse/review/save and full preference CRUD with inline editing and bulk delete.**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-04-06T00:17:48Z
- **Completed:** 2026-04-06T00:20:51Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments

- Full preferences router with 10 HTTP endpoints: list (HTMX search), row, edit-form, update (PUT), create, delete, bulk-delete, upload (PDF parse), resolve (contradiction), save
- Three-tab preferences page with Alpine.js state: Preferences List (default), Receipt Upload, Update Chat (placeholder)
- Receipt upload flow: drag-and-drop PDF drop zone → pdfplumber + LLM parse → editable review table with contenteditable cells → contradiction resolution cards → save to preference store
- Preference list with live search (300ms HTMX debounce), inline edit/discard via outerHTML swap, bulk-delete with sticky action bar and inline confirmation, and add-manually inline form
- Server-side Starlette session stores parsed receipt state (items + contradiction resolutions) across the multi-step upload/resolve/save flow

## Task Commits

1. **Task 1: Create preferences router with all endpoints** - `686c891` (feat)
2. **Task 2: Create preferences page template and all HTMX partials** - `9075b4a` (feat)

## Files Created/Modified

- `app/routers/preferences.py` — All 10 preference HTTP endpoints
- `templates/pages/preferences.html` — Three-tab preferences page with Alpine.js
- `templates/partials/pref_list.html` — HTMX searchable list with empty states and save-success banner
- `templates/partials/pref_row.html` — Display row with Established/Seen-once badges, edit trigger
- `templates/partials/pref_edit_form.html` — Inline edit form with Save/Discard HTMX actions
- `templates/partials/receipt_upload_form.html` — Drag-and-drop drop zone with Alpine.js drag state and htmx-indicator spinner
- `templates/partials/receipt_review.html` — Editable table with contenteditable cells, remove-row Alpine action, contradiction panel, save button with disabled state
- `templates/partials/receipt_contradictions.html` — Brand-change resolution cards with new_preference / one_time forms
- `app/routers/pages.py` — Updated /preferences GET to load entries for initial render
- `app/main.py` — Registered preferences router

## Decisions Made

- Contradiction resolution POSTs the `loop.index0` value as `contradiction_index` so the server can update the correct slot in the session list
- `receipt/save` always clears session keys after commit, even on partial success, to avoid stale data on browser refresh
- `allResolved` Alpine flag is initialised from the server-rendered context (`true` when contradictions list is empty at parse time) so the Save button starts enabled when no contradictions exist
- `pref-row-` ID pattern lives in `pref_row.html`; `pref_list.html` satisfies the acceptance criterion via `{% include %}` rather than duplicating markup

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all UI is wired to live endpoints backed by PreferenceService and ReceiptParser from Plan 01. The Update Chat tab shows a "coming in the next update" placeholder, which is correct for Plan 02 scope (chat is Plan 03's deliverable).

## Self-Check: PASSED

Files verified:
- FOUND: app/routers/preferences.py
- FOUND: templates/pages/preferences.html
- FOUND: templates/partials/pref_list.html
- FOUND: templates/partials/pref_row.html
- FOUND: templates/partials/pref_edit_form.html
- FOUND: templates/partials/receipt_upload_form.html
- FOUND: templates/partials/receipt_review.html
- FOUND: templates/partials/receipt_contradictions.html

Commits verified:
- FOUND: 686c891 (Task 1 — preferences router)
- FOUND: 9075b4a (Task 2 — templates and partials)
