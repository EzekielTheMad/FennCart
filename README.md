# FennCart

A self-hosted web application that converts grocery shopping lists into loaded Kroger/Fry's carts. Paste a natural language shopping list, and FennCart matches items against your learned brand preferences using an LLM, presents selections for review, and adds confirmed items to your Kroger cart. Named after Fenn, a DnD character who doubled as the party's chef.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- A [Kroger developer account](https://developer.kroger.com) (free — create an app to get client ID and secret)
- An API key from [Anthropic](https://console.anthropic.com/), [OpenAI](https://platform.openai.com/api-keys), or a local [Ollama](https://ollama.ai) instance

## Quickstart

1. **Clone the repo**
   ```bash
   git clone https://github.com/youruser/fenncart.git && cd fenncart
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and fill in your credentials (see [Configuration](#configuration) below).

3. **Start the app**
   ```bash
   docker compose up -d
   ```

4. **Complete setup** — Open http://localhost:8000 and walk through the setup wizard:
   - Step 1: Validate your LLM API key
   - Step 2: Confirm Kroger credentials
   - Step 3: Select your store by zip code
   - Step 4: Authorize with Kroger (OAuth)

5. **Start shopping** — Paste a grocery list and add matched items to your Kroger cart.

## Configuration

All configuration is via environment variables in `.env`. See `.env.example` for the full template.

| Variable | Required | Description |
|----------|----------|-------------|
| `KROGER_CLIENT_ID` | Yes | From [developer.kroger.com](https://developer.kroger.com) — My Apps |
| `KROGER_CLIENT_SECRET` | Yes | From [developer.kroger.com](https://developer.kroger.com) — My Apps |
| `LLM_API_KEY` | Yes | Your Anthropic or OpenAI key (leave blank for Ollama) |
| `LLM_PROVIDER` | No | `anthropic` (default), `openai`, or `ollama` |
| `LLM_MODEL` | No | Model name (default: `claude-3-haiku-20240307`) |
| `SESSION_SECRET_KEY` | Yes | A random string for session cookie signing |
| `BASE_URL` | Yes | URL users access the app at (default: `http://localhost:8000`) |
| `PORT` | No | Port to expose (default: `8000`) |

**Important:** `SESSION_SECRET_KEY` must be changed from the default value or the app will refuse to start. Generate one with:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Upgrading

```bash
docker compose pull && docker compose up -d
```

Alembic migrations run automatically on container start. Your data in the `fenncart_data` Docker volume is preserved across upgrades.

## Architecture

- **Runtime:** Python 3.12 + FastAPI, server-rendered HTML with HTMX + Alpine.js + Tailwind CSS
- **Database:** SQLite (single file at `/data/fenncart.db`, persisted via Docker volume)
- **LLM:** LiteLLM + Instructor for multi-provider structured output
- **Auth:** Kroger OAuth 2.0 PKCE via Authlib
- **Container:** Single `docker compose up` — no separate database service needed

**Constraints:**
- Single container only (`--workers 1` for SQLite write safety)
- Kroger credentials are BYO (bring your own) per Kroger API TOS
- Cart API is add-only — FennCart tracks cart state locally

## Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/ -q

# Run locally (without Docker)
uvicorn app.main:app --reload --port 8000
```

## License

[Add your license here]
