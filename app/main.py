from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from app.config import get_settings
from app.database import init_db, get_session

templates = Jinja2Templates(directory="templates")


class SetupGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exempt paths: static files, setup wizard, auth callbacks, health check
        exempt_prefixes = ("/static", "/setup", "/auth", "/health")
        if any(request.url.path.startswith(p) for p in exempt_prefixes):
            return await call_next(request)

        if SESSION_KEY_MISSING:
            return templates.TemplateResponse(
                request,
                "session_error.html",
                status_code=500,
            )

        # Check Kroger credentials: env vars first (no DB needed), then DB
        settings = get_settings()
        has_kroger_creds = bool(settings.kroger_client_id and settings.kroger_client_secret)

        from app.models.config_model import AppConfig
        from sqlalchemy import select
        async for session in get_session():
            result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
            cfg = result.scalar_one_or_none()

            # If env vars empty, check DB for encrypted credentials
            if not has_kroger_creds and cfg:
                has_kroger_creds = bool(
                    cfg.kroger_client_id_encrypted and cfg.kroger_client_secret_encrypted
                )

            if not has_kroger_creds:
                return templates.TemplateResponse(
                    request,
                    "missing_config.html",
                    {"missing_vars": _get_missing_vars(settings)},
                )

            if not cfg or not cfg.wizard_complete:
                return RedirectResponse("/setup", status_code=302)

        return await call_next(request)


def _get_missing_vars(settings) -> list[str]:
    missing = []
    if not settings.kroger_client_id:
        missing.append("KROGER_CLIENT_ID")
    if not settings.kroger_client_secret:
        missing.append("KROGER_CLIENT_SECRET")
    return missing


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from app.services.oauth_manager import register_kroger_oauth
    # Register OAuth if credentials exist in env (DB creds checked at request time)
    settings = get_settings()
    if settings.kroger_client_id and settings.kroger_client_secret:
        register_kroger_oauth()
    yield


SESSION_KEY_MISSING = False
try:
    _session_secret = get_settings().session_secret_key
except (ValidationError, Exception):
    SESSION_KEY_MISSING = True
    _session_secret = "startup-error-placeholder-not-used"

app = FastAPI(title="FennCart", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=_session_secret)
app.add_middleware(SetupGuardMiddleware)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Pre-stubbed router includes (Plans 01-02, 01-03, 01-04 create these modules) ---
# Guard with try/except so app starts before router modules exist.
# Each subsequent plan creates the module; the import then succeeds on next restart.
try:
    from app.routers import pages
    app.include_router(pages.router)
except ImportError:
    pass  # Created by Plan 01-02

try:
    from app.routers import setup
    app.include_router(setup.router)
except ImportError:
    pass  # Created by Plan 01-03

try:
    from app.routers import auth
    app.include_router(auth.router)
except ImportError:
    pass  # Created by Plan 01-04

try:
    from app.routers import shopping
    app.include_router(shopping.router)
except ImportError:
    pass  # Created by Plan 02-03

try:
    from app.routers import preferences as preferences_router
    app.include_router(preferences_router.router)
except ImportError:
    pass  # Created by Plan 03-02

try:
    from app.routers import settings
    app.include_router(settings.router)
except ImportError:
    pass  # Created by Plan 04-02


@app.get("/health")
async def health():
    return {"status": "ok"}
