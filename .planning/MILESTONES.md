# Milestones

## v1.1 Tech Debt Cleanup (Shipped: 2026-04-08)

**Phases completed:** 2 phases, 5 plans, 8 tasks

**Key accomplishments:**

1. Container crash-loop on missing SESSION_SECRET_KEY replaced with helpful error page and setup instructions
2. README updated with real GitHub URL (EzekielTheMad/FennCart) and MIT License file created at repo root
3. Fragile `Alpine._x_dataStack` internal API replaced with stable `$root.updateItem()` state-lift pattern
4. Dead code removed: POST `/shopping/swap` endpoint, `review_card.html`, unused imports, deprecated TemplateResponse calls
5. All 7 v1.0 phases backfilled with nyquist-compliant VALIDATION.md files (197 tests mapped to requirements)

**v1.0 tech debt resolved:** All items from v1.0 tech debt list have been addressed.

**Archive:** [v1.1-ROADMAP.md](milestones/v1.1-ROADMAP.md) | [v1.1-REQUIREMENTS.md](milestones/v1.1-REQUIREMENTS.md)

---

## v1.0 MVP (Shipped: 2026-04-07)

**Phases:** 7 | **Plans:** 19 | **Commits:** 125 | **Timeline:** 5 days (Apr 2-6, 2026)
**Codebase:** ~6,400 Python + ~5,000 HTML | **Tests:** 187 passing

**Key accomplishments:**

1. Docker-containerized FastAPI app with guided setup wizard, Kroger OAuth PKCE, and encrypted token storage
2. End-to-end list-to-cart flow: NL shopping list -> LLM product matching -> review screen -> Kroger Cart API
3. Receipt PDF parsing with pdfplumber to bootstrap a living preference profile weighted by purchase frequency
4. Multi-provider LLM support (Claude, OpenAI, Ollama) with DB-authoritative hot-swap settings hub
5. Preference-compensated product matching with NL chat updates and manual CRUD
6. Docker hardening, Alembic migration safety tests, and quickstart README

**Tech debt carried forward:**

- SESSION_SECRET_KEY startup crash is opaque (no helpful error page)
- README has placeholder license and GitHub URL
- Alpine._x_dataStack internal API usage for product swap capture is fragile
- POST /shopping/swap is dead code
- Nyquist validation incomplete across all phases

**Archive:** [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) | [v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md) | [v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md)

---
