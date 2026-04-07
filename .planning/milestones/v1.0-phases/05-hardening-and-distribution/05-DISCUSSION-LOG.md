# Phase 5: Hardening and Distribution - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-06
**Phase:** 05-hardening-and-distribution
**Areas discussed:** Docker optimization, Setup documentation, Migration safety, Security hardening

---

## Docker Optimization

### Image Size Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Lean but simple | Add .dockerignore, pin LiteLLM extras. Keep single-stage build. | ✓ |
| Multi-stage minimal | Compile stage + final stage. Smaller image but more complex Dockerfile. | |
| You decide | Claude picks the best approach | |

**User's choice:** Lean but simple
**Notes:** None — straightforward preference for simplicity.

### LLM Provider Dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| All providers included | Ship with anthropic, openai, ollama support baked in. Switch in settings without rebuild. | ✓ |
| User picks at build time | Docker build arg selects providers. Smaller image but must rebuild to switch. | |
| Minimal + lazy install | Bare LiteLLM, pip install on first use. Complex but smallest default. | |

**User's choice:** All providers included
**Notes:** Prioritizes user convenience over image size.

---

## Setup Documentation

### README Depth

| Option | Description | Selected |
|--------|-------------|----------|
| Quickstart-focused | Concise: what it does, prerequisites, 5-step quickstart. | ✓ |
| Comprehensive single doc | Full README with architecture, all config, troubleshooting, screenshots. | |
| README + separate docs/ | Short README plus docs/ folder with detailed guides. | |

**User's choice:** Quickstart-focused
**Notes:** None.

### Credential Guidance

| Option | Description | Selected |
|--------|-------------|----------|
| Brief pointers | Link to portals with 1-2 sentence guidance. | ✓ |
| Step-by-step walkthrough | Detailed screenshots/instructions for each portal. | |
| Skip entirely | Just list required credentials with no links. | |

**User's choice:** Brief pointers
**Notes:** None.

---

## Migration Safety

### Verification Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Upgrade-path test | Automated test applying migrations sequentially, verify final schema matches models. | ✓ |
| Upgrade + seed data test | Sequential test with seeded data at each step to verify data survives. | |
| Manual verification only | Document path, test manually before release. | |

**User's choice:** Upgrade-path test
**Notes:** None.

### Rollback Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Forward-only | No downgrade support. Restore from backup if needed. | ✓ |
| Downgrade support | Each migration has working downgrade(). Roll back one version. | |

**User's choice:** Forward-only
**Notes:** None.

---

## Security Hardening

### Hardening Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Essential checks | Enforce SESSION_SECRET_KEY change, verify .gitignore, health endpoint note. No pre-commit. | |
| Pre-commit + scanning | Secret scanning, dependency audit. More robust but adds dev complexity. | |
| You decide | Claude picks what's appropriate for BYO-credentials self-hosted app. | ✓ |

**User's choice:** You decide (Claude's Discretion)
**Notes:** User deferred security scope to Claude. Expected: essential runtime checks, no unnecessary dev-tooling overhead.

---

## Claude's Discretion

- Security hardening scope — Claude determines appropriate balance for single-user self-hosted app

## Deferred Ideas

None — discussion stayed within phase scope.
