from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.config import get_settings
from app.services.oauth_manager import oauth, store_token
from app.models.config_model import AppConfig
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/auth/kroger/start")
async def kroger_auth_start(request: Request):
    """Initiate Kroger OAuth PKCE flow. Redirects user to Kroger login."""
    settings = get_settings()
    redirect_uri = f"{settings.base_url}/auth/kroger/callback"
    return await oauth.kroger.authorize_redirect(
        request, redirect_uri, code_challenge_method="S256"
    )


@router.get("/auth/kroger/callback")
async def kroger_auth_callback(request: Request, db: AsyncSession = Depends(get_session)):
    """Handle Kroger OAuth callback — exchange code for tokens, encrypt and store."""
    try:
        token = await oauth.kroger.authorize_access_token(request)
        await store_token(token, db)

        # Mark wizard as complete (D-02)
        result = await db.execute(select(AppConfig).where(AppConfig.id == 1))
        cfg = result.scalar_one_or_none()
        # Capture pre-auth state to determine redirect destination
        was_already_complete = cfg.wizard_complete if cfg else False
        if cfg:
            cfg.wizard_step = "complete"
            cfg.wizard_complete = True
            await db.commit()

        if was_already_complete:
            # Re-auth from settings — go back to settings
            return RedirectResponse("/settings?section=account", status_code=302)
        return RedirectResponse("/tour", status_code=302)
    except Exception as e:
        # OAuth failed — render step_oauth with error
        return templates.TemplateResponse("setup/step_oauth.html", {
            "request": request,
            "error": f"Authorization failed. This usually means the redirect URI doesn't match what's registered in your Kroger developer app. Check BASE_URL in your environment. Detail: {str(e)}",
            "current_step": 4,
        })
