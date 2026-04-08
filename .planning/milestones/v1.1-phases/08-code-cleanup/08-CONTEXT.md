# Phase 8: Code Cleanup - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix four specific issues in the v1.0 codebase: crash on missing SESSION_SECRET_KEY, README placeholder content, fragile Alpine._x_dataStack internal API usage in product swap, and dead code removal (unused routes/imports).

</domain>

<decisions>
## Implementation Decisions

### README Content
- **D-01:** GitHub repository URL is `https://github.com/EzekielTheMad/FennCart` — replace all instances of `youruser/fenncart` in README.md
- **D-02:** License is MIT — update README line from `[Add your license here]` to reference MIT License
- **D-03:** Create a `LICENSE` file at repo root with full MIT License text AND update README to link to it

### Claude's Discretion
- **Error page design:** How the missing-SESSION_SECRET_KEY error page looks and behaves (currently raises ValueError that crash-loops Uvicorn). Claude should implement a user-friendly HTML page with setup instructions that displays instead of a stack trace.
- **Swap endpoint fate:** Success criteria says "POST /shopping/swap endpoint is absent" but the endpoint at `app/routers/shopping.py:143` is actively used by `review_card.html` for product swaps. Claude should investigate whether the swap can be handled client-side via Alpine.js (eliminating the server endpoint) or if the success criteria needs reinterpretation. The `Alpine._x_dataStack` fix (QUAL-01) and swap endpoint removal (QUAL-02) are likely related — fixing the Alpine API may enable a client-side swap that removes the need for the POST endpoint.
- **Dead code scope:** Audit all routers for unused routes and imports beyond just the swap endpoint. Remove anything confirmed dead.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — ERR-01, DOC-01, QUAL-01, QUAL-02 are the four requirements mapped to this phase

### Existing Code (primary targets)
- `app/config.py` — SESSION_SECRET_KEY validator (line 17-25) that raises ValueError on default value
- `app/routers/shopping.py` — POST `/swap` endpoint (line 143-191) and session-based match data
- `templates/partials/review_screen.html` — Alpine._x_dataStack usage (line 214-216)
- `templates/partials/review_card.html` — review card template referencing `/shopping/swap`
- `README.md` — placeholder URL (line 15) and license (line 93)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `app/config.py:Settings` — Pydantic validator already catches the bad key; needs a middleware/exception handler to serve an error page instead of crashing
- `templates/` — Jinja2 templates with Tailwind CSS styling; error page should match existing design language
- Alpine.js + HTMX patterns used throughout review flow — swap fix should stay within these paradigms

### Established Patterns
- `SetupGuardMiddleware` in `app/main.py` already intercepts requests when setup is incomplete — similar pattern could catch missing SESSION_SECRET_KEY
- Router-local `Jinja2Templates` instances (each router has its own)
- Server-side session for match state (`request.session["match_data"]`)

### Integration Points
- `app/main.py` — where middleware is registered and app startup occurs; error page intercept goes here
- `app/routers/shopping.py` — swap endpoint lives here; dead code removal target
- `templates/partials/review_screen.html` — Alpine data binding for product swap selection

</code_context>

<specifics>
## Specific Ideas

- GitHub URL confirmed by user: `https://github.com/EzekielTheMad/FennCart`
- MIT License — both LICENSE file at root and README reference

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 08-code-cleanup*
*Context gathered: 2026-04-07*
