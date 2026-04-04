# Phase 4: Multi-Provider LLM and Settings - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-04
**Phase:** 04-multi-provider-llm-and-settings
**Areas discussed:** Provider config UX, Settings page scope, Validation & feedback, Hot-swap behavior, Model selection UX, Store change flow, Kroger re-auth flow, App preferences

---

## Provider Config UX

| Option | Description | Selected |
|--------|-------------|----------|
| Tabbed sections | Tabs for Claude / OpenAI / Ollama — each shows its own key/model fields | |
| Single form with dropdown | One dropdown selects provider, fields below dynamically change | ✓ |
| You decide | Claude picks whichever approach fits existing patterns | |

**User's choice:** Single form with dropdown
**Notes:** More compact, fewer clicks. Dynamic field changes via HTMX/Alpine.

---

## Ollama Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Endpoint URL + model name | User enters URL and model name, no API key | |
| Auto-detect local Ollama | App checks localhost:11434 on page load | |
| You decide | Claude picks the simpler approach | ✓ |

**User's choice:** You decide
**Notes:** Claude has discretion. Key difference: endpoint URL instead of API key.

---

## Settings Page Scope

| Option | Description | Selected |
|--------|-------------|----------|
| LLM + store + re-auth | Centralizes wizard-configured items | |
| LLM only | Focused on just the phase requirement | |
| Full settings hub | LLM, store, re-auth, plus app preferences | ✓ |

**User's choice:** Full settings hub
**Notes:** One-stop shop for all configuration.

---

## Settings Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Stacked sections | All settings in one scrollable page with section headers | |
| Sidebar sub-nav | Settings page gets its own sidebar/tab navigation | ✓ |
| You decide | Claude picks based on content amount | |

**User's choice:** Sidebar sub-nav
**Notes:** Cleaner organization for the full settings hub.

---

## Validation & Feedback

| Option | Description | Selected |
|--------|-------------|----------|
| Test before saving | Run test_connection inline before persisting | ✓ |
| Save then test | Save immediately, test in background | |
| Save only, no test | Just save, find out on next run | |

**User's choice:** Test before saving (Recommended)
**Notes:** Same pattern as wizard's LLM step. Prevents saving broken config.

---

## API Key Display

| Option | Description | Selected |
|--------|-------------|----------|
| Masked with reveal toggle | Standard password field with eye icon | ✓ |
| Last 4 chars only | Show partial key, no reveal option | |
| You decide | Claude picks more secure approach | |

**User's choice:** Masked with reveal toggle
**Notes:** Standard password field pattern.

---

## Hot-Swap Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Immediate (next API call) | Clear cached Settings, update DB instantly | |
| After save + confirmation | Switch on save after test succeeds | |
| You decide | Claude picks simplest approach | ✓ |

**User's choice:** You decide
**Notes:** Must work without container restart. lru_cache needs invalidation.

---

## Model Selection UX

| Option | Description | Selected |
|--------|-------------|----------|
| Curated dropdown + custom | Top 3-5 models per provider + custom text field | ✓ |
| Free text only | User types model ID directly | |
| You decide | Claude picks best balance | |

**User's choice:** Curated dropdown + custom
**Notes:** Good usability for common models, power user escape hatch for custom IDs.

---

## Store Change Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Re-use wizard component | Same zip search + results from wizard via HTMX partial | ✓ |
| Simpler inline | Text field for store ID or zip with search button | |
| You decide | Claude picks based on code reuse | |

**User's choice:** Re-use wizard component
**Notes:** Consistent UX, less new code.

---

## Kroger Re-Auth Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Re-auth button + status | Show auth status, manual re-authorize button | |
| Auto-prompt on expiry | Manual button plus proactive expiry banner | |
| You decide | Claude picks fitting approach | ✓ |

**User's choice:** You decide
**Notes:** Must show current auth status and provide manual re-authorize.

---

## App Preferences

| Option | Description | Selected |
|--------|-------------|----------|
| Review mode + threshold | Default review mode and confidence threshold slider | |
| Minimal — review mode only | Just default review mode toggle | ✓ |
| You decide | Claude picks what makes sense | |

**User's choice:** Minimal — review mode only
**Notes:** Keep it simple. Just exceptions-only vs full review toggle.

---

## Claude's Discretion

- Ollama configuration approach
- Kroger re-auth UX details
- Hot-swap timing mechanics

## Deferred Ideas

None — discussion stayed within phase scope
