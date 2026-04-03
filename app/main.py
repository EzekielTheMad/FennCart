from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

        settings = get_settings()
        # Check for missing Kroger credentials (D-07: serve missing config page)
        if not settings.kroger_client_id or not settings.kroger_client_secret:
            return templates.TemplateResponse(
                request,
                "missing_config.html",
                {"missing_vars": _get_missing_vars(settings)},
            )

        # Check wizard completion (D-02: resumable wizard)
        from app.models.config_model import AppConfig
        from sqlalchemy import select
        async for session in get_session():
            result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
            cfg = result.scalar_one_or_none()
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
    yield


app = FastAPI(title="FennCart", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=get_settings().session_secret_key)
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


@app.get("/health")
async def health():
    return {"status": "ok"}
