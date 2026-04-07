# Phase 1: Foundation and Auth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 01-foundation-and-auth
**Areas discussed:** Setup wizard flow, Post-setup landing, Credential storage, Error handling UX, App shell / navigation, Docker compose shape

---

## Setup Wizard Flow

### Wizard Step Order

| Option | Description | Selected |
|--------|-------------|----------|
| LLM → Kroger API → Store → OAuth | Validate LLM first (cheapest), then Kroger dev keys, store, OAuth last | ✓ |
| Kroger API → OAuth → Store → LLM | Get Kroger working first (core dependency), LLM last | |
| You decide | Claude picks optimal order | |

**User's choice:** LLM → Kroger API → Store → OAuth
**Notes:** Validates cheapest credential first, builds up to the most complex step (OAuth).

### Step Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Validate each step (Recommended) | Test connection/credentials before allowing next step | ✓ |
| Validate at end | Collect all inputs, test in batch | |
| You decide | Claude picks | |

**User's choice:** Validate each step

### Wizard Resumability

| Option | Description | Selected |
|--------|-------------|----------|
| Resume from last completed step | Save progress to SQLite, pick up where left off | ✓ |
| Start over | Simpler, wizard is short | |
| You decide | Claude picks | |

**User's choice:** Resume from last completed step

---

## Post-Setup Landing

| Option | Description | Selected |
|--------|-------------|----------|
| Shopping list input immediately | Drop straight into main flow | |
| Dashboard with status | Show connected services with "Start Shopping" action | |
| Quick tour / tips | Brief walkthrough before main screen | ✓ |
| You decide | Claude picks | |

**User's choice:** Quick tour / tips
**Notes:** User wants a brief orientation before the main experience.

---

## Credential Storage

### Kroger Developer Credentials Source

| Option | Description | Selected |
|--------|-------------|----------|
| Env vars only | Set in .env, wizard reads but never stores in SQLite | ✓ |
| Wizard stores in SQLite | Entered in wizard, encrypted in SQLite | |
| Either path | Accept from env vars or wizard, env vars priority | |
| You decide | Claude picks | |

**User's choice:** Env vars only

### LLM API Key Source

| Option | Description | Selected |
|--------|-------------|----------|
| Same as Kroger creds | Same storage approach (env vars only) | ✓ |
| Always wizard-entered | LLM key through wizard into SQLite | |
| You decide | Claude picks | |

**User's choice:** Same as Kroger creds (env vars only)

### Encryption at Rest

| Option | Description | Selected |
|--------|-------------|----------|
| Encrypt tokens (Recommended) | Encrypt OAuth tokens in SQLite using app-generated key | ✓ |
| No encryption | Plaintext in SQLite, Docker volume is security boundary | |
| You decide | Claude picks | |

**User's choice:** Encrypt tokens

---

## Error Handling UX

### Error Display Pattern

| Option | Description | Selected |
|--------|-------------|----------|
| Inline errors with fix hints | Show error in wizard/page with "how to fix" | |
| Toast notifications | Non-blocking toasts with details link | |
| You decide | Claude picks the error UX pattern | ✓ |

**User's choice:** You decide

### Missing Credentials at Startup

| Option | Description | Selected |
|--------|-------------|----------|
| Start anyway, show wizard | Boot app, show wizard explaining what's missing | |
| Refuse to start with log message | Container exits with clear error in logs | |
| Both | Start but only serve "missing config" page | ✓ |

**User's choice:** Both (start but only serve missing config page)

---

## App Shell / Navigation

### Navigation Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal top bar | App name left, settings gear right | |
| Sidebar navigation | Persistent sidebar with all pages | |
| You decide | Claude picks the nav pattern | ✓ |

**User's choice:** You decide

### Phase 1 Pages

| Option | Description | Selected |
|--------|-------------|----------|
| Setup wizard + status page | Just wizard and confirmation | |
| Full shell with placeholders | All nav items, non-Phase-1 pages show "Coming soon" | ✓ |
| You decide | Claude picks | |

**User's choice:** Full shell with placeholders

---

## Docker Compose Shape

| Option | Description | Selected |
|--------|-------------|----------|
| You decide | Claude designs based on research recommendations | |
| Let me specify | User has specific preferences | ✓ |

**User's choice:** Let me specify
**Notes:** User wants Unraid Community Apps compatibility. Single container, Unraid CA template format with WebUI, port mappings, volume paths (/mnt/user/appdata/fenncart/), env vars in Unraid XML format. The container design must be Unraid-friendly from the start. Actual CA XML template can be Phase 5 deliverable.

---

## Claude's Discretion

- Error UX pattern (inline vs toasts vs pages)
- Navigation structure (top bar vs sidebar)

## Deferred Ideas

None — discussion stayed within phase scope.
