---
phase: 03-preference-system
plan: 03
subsystem: ui
tags: [htmx, jinja2, instructor, litellm, preferences, chat, cart-service]

# Dependency graph
requires:
  - phase: 03-01
    provides: PreferenceService.get_preferences_for_matching(), PreferenceService.apply_nl_delta(), PreferenceDelta schema
  - phase: 03-02
    provides: preferences.html page structure with tab scaffold, receipt upload tab
  - phase: 02-03
    provides: CartService.process_list(preferences=None) hook, shopping review flow
provides:
  - NL chat endpoints (POST /preferences/chat, POST /preferences/chat/apply)
  - parse_preference_nl() Instructor helper using PreferenceDelta structured output
  - templates/partials/chat_message.html with user/assistant/system bubble variants
  - CartService auto-loads preferences when preferences=None via get_preferences_for_matching()
  - CartService.preferences_loaded property for template context
  - templates/partials/preference_indicator.html banner for shopping review
  - review_screen.html conditionally includes preference_indicator when preferences_loaded
affects: [04-multi-provider-llm-and-settings, testing]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Instructor parse_preference_nl() mirrors parse_shopping_list() pattern from llm_service.py
    - Session-backed conversation history capped at 10 messages for LLM context control
    - pending_delta session key stores PreferenceDelta awaiting user confirmation
    - Inline PreferenceService import inside CartService method to avoid circular imports
    - _preferences_loaded instance flag + property pattern for post-call state inspection

key-files:
  created:
    - templates/partials/chat_message.html
    - templates/partials/preference_indicator.html
  modified:
    - app/routers/preferences.py
    - templates/pages/preferences.html
    - app/services/cart_service.py
    - app/routers/shopping.py
    - templates/partials/review_screen.html

key-decisions:
  - "Inline PreferenceService import inside CartService.process_list() to avoid circular import between cart_service and preference_service"
  - "Session key 'pending_delta' holds PreferenceDelta dict between /chat and /chat/apply — user must explicitly POST /chat/apply to commit"
  - "Chat conversation history capped at last 10 messages before passing to LLM (Pitfall 5 cost/context control)"
  - "user_message passed as template var so chat_message.html can render both user bubble and assistant bubble in one HTMX response"

patterns-established:
  - "Instance flag + property for post-call state: _preferences_loaded / preferences_loaded — safe for single-request lifecycle"
  - "NL parse helper follows llm_service.py Instructor pattern: instructor.from_provider(litellm/{model_str}, async_client=True)"

requirements-completed: [PREF-04, PREF-06]

# Metrics
duration: 10min
completed: 2026-04-06
---

# Phase 3 Plan 03: NL Preference Chat and CartService Integration Summary

**NL chat preference updates with Instructor-parsed PreferenceDelta confirmation flow, and CartService auto-loading preferences to influence LLM product matching with a shopping review indicator**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-04-06T00:24:33Z
- **Completed:** 2026-04-06T00:34:00Z
- **Tasks:** 2
- **Files modified:** 5 (3 created, 5 modified total)

## Accomplishments

- POST /preferences/chat parses user messages into PreferenceDelta via Instructor, stores conversation history in session, returns confirmation preview with Apply/Discard buttons
- POST /preferences/chat/apply applies the confirmed delta via PreferenceService.apply_nl_delta() and clears the pending session key
- CartService.process_list() now auto-loads preferences when preferences=None, setting _preferences_loaded flag for downstream template context
- Shopping review screen conditionally displays "Matching with your preferences" indicator when preferences influenced matching

## Task Commits

1. **Task 1: Add NL chat endpoints and chat message template** - `ce73fb6` (feat)
2. **Task 2: Wire preferences into CartService and add shopping indicator** - `916b2f8` (feat)

## Files Created/Modified

- `app/routers/preferences.py` - Added parse_preference_nl(), POST /chat, POST /chat/apply endpoints
- `templates/partials/chat_message.html` - New: user/assistant/system bubble partial with confirmation preview
- `templates/pages/preferences.html` - Replaced chat tab placeholder with live HTMX chat interface
- `app/services/cart_service.py` - Added _preferences_loaded flag, preferences_loaded property, auto-load in process_list()
- `app/routers/shopping.py` - Passes preferences_loaded to review_screen.html template context
- `templates/partials/preference_indicator.html` - New: "Matching with your preferences" banner with heart icon
- `templates/partials/review_screen.html` - Added conditional preference_indicator include at top

## Decisions Made

- Inline PreferenceService import inside CartService.process_list() to avoid circular imports — both services live in the same package
- Session key `pending_delta` stores PreferenceDelta as dict between the /chat and /chat/apply round-trips
- chat_message.html renders both user bubble and assistant bubble in one HTMX response (user_message + role/message vars)
- Conversation history capped at last 10 messages before passing to LLM (Pitfall 5)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None — all preference data is wired. The chat tab renders live, CartService loads real preference entries, and the indicator reflects actual preference state.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Full preference system is complete: receipt upload (Plan 01-02), preference CRUD (Plan 01-02), NL chat updates (this plan), and CartService integration (this plan)
- Phase 4 (multi-provider LLM and settings) can reuse the same LLM config pattern; parse_preference_nl() uses get_settings() and will automatically pick up provider changes
- 116 existing tests pass, no regressions

---
*Phase: 03-preference-system*
*Completed: 2026-04-06*
