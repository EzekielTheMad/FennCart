# Phase 8: Code Cleanup - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-07
**Phase:** 08-code-cleanup
**Areas discussed:** README content

---

## Gray Area Selection

| Area | Selected |
|------|----------|
| Error page design | |
| Swap endpoint fate | |
| Dead code scope | |
| README content | yes |

User selected only README content. Other areas deferred to Claude's discretion.

---

## README Content

### Q1: GitHub repository URL

| Option | Description | Selected |
|--------|-------------|----------|
| Leave as youruser/fenncart | Keep the placeholder — users will fork/clone their own copy anyway | |
| Use a real GitHub URL | You have a specific GitHub org/user and repo name in mind | yes |
| Use a generic template | Something like '<your-org>/fenncart' that's clearly a fill-in-the-blank | |

**User's choice:** Use a real GitHub URL
**Follow-up:** User provided `https://github.com/EzekielTheMad/FennCart`

### Q2: License type

| Option | Description | Selected |
|--------|-------------|----------|
| MIT License (Recommended) | Standard open source. Matches the success criteria and pdfplumber's MIT license. | yes |
| Different license | You have another license in mind | |

**User's choice:** MIT License

### Q3: LICENSE file

| Option | Description | Selected |
|--------|-------------|----------|
| Both (Recommended) | Add a LICENSE file at repo root AND update the README line to link to it | yes |
| README only | Just change the README line to say 'MIT License' — no separate file | |

**User's choice:** Both — LICENSE file at root + README reference

---

## Claude's Discretion

- Error page design (how the missing-SESSION_SECRET_KEY error page looks/behaves)
- Swap endpoint fate (remove vs rewrite — tied to Alpine._x_dataStack fix)
- Dead code audit scope (all routers vs just swap endpoint)

## Deferred Ideas

None — discussion stayed within phase scope
