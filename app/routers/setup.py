from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.config import get_settings
from app.database import get_session
from app.models.config_model import AppConfig
from app.services import llm_service, kroger_client

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Maps wizard_step DB value to the step number (1-4)
STEP_ORDER = ["start", "llm", "kroger", "store", "oauth", "complete"]


def _step_number(wizard_step: str) -> int:
    """Return 1-based step number to show (the step AFTER the last completed step)."""
    if wizard_step == "start":
        return 1
    if wizard_step == "llm":
        return 2
    if wizard_step == "kroger":
        return 3
    # store, oauth, complete
    return 4


def _next_step_template(wizard_step: str) -> str:
    """Return template name for the next step after wizard_step."""
    if wizard_step == "start":
        return "setup/step_llm.html"
    if wizard_step == "llm":
        return "setup/step_kroger.html"
    if wizard_step == "kroger":
        return "setup/step_store.html"
    if wizard_step == "store":
        return "setup/step_oauth.html"
    return "setup/step_llm.html"


async def _get_or_create_config(session: AsyncSession) -> AppConfig:
    """Get or create AppConfig row (always id=1)."""
    result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = AppConfig(id=1, wizard_step="start", wizard_complete=False)
        session.add(cfg)
        await session.commit()
        await session.refresh(cfg)
    return cfg


@router.get("/setup", response_class=HTMLResponse)
async def setup_wizard(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Render the wizard shell with the current step."""
    cfg = await _get_or_create_config(session)
    step_template = _next_step_template(cfg.wizard_step)
    current_step = _step_number(cfg.wizard_step)
    settings = get_settings()
    masked_api_key = _mask_value(settings.llm_api_key)
    masked_client_id = _mask_value(settings.kroger_client_id)
    masked_client_secret = _mask_value(settings.kroger_client_secret)
    return templates.TemplateResponse(
        request,
        "setup/wizard.html",
        {
            "current_step": current_step,
            "step_template": step_template,
            "masked_api_key": masked_api_key,
            "masked_client_id": masked_client_id,
            "masked_client_secret": masked_client_secret,
        },
    )


@router.post("/setup/validate-llm", response_class=HTMLResponse)
async def validate_llm(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Validate LLM API key. On success advance wizard to step 2."""
    settings = get_settings()
    success, message = await llm_service.test_connection(
        api_key=settings.llm_api_key,
        provider=settings.llm_provider,
        model=settings.llm_model,
    )
    if success:
        cfg = await _get_or_create_config(session)
        cfg.wizard_step = "llm"
        session.add(cfg)
        await session.commit()
        return templates.TemplateResponse(
            request,
            "setup/step_kroger.html",
            {
                "masked_client_id": _mask_value(settings.kroger_client_id),
                "masked_client_secret": _mask_value(settings.kroger_client_secret),
            },
        )
    else:
        return templates.TemplateResponse(
            request,
            "setup/step_llm.html",
            {
                "error": message,
                "masked_api_key": _mask_value(settings.llm_api_key),
            },
        )


@router.post("/setup/validate-kroger", response_class=HTMLResponse)
async def validate_kroger(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Validate Kroger developer credentials. On success advance wizard to step 3."""
    settings = get_settings()
    success, message, _token = await kroger_client.get_app_token(
        client_id=settings.kroger_client_id,
        client_secret=settings.kroger_client_secret,
    )
    if success:
        cfg = await _get_or_create_config(session)
        cfg.wizard_step = "kroger"
        session.add(cfg)
        await session.commit()
        return templates.TemplateResponse(
            request,
            "setup/step_store.html",
            {
                "stores": [],
                "message": None,
                "selected_store": None,
            },
        )
    else:
        return templates.TemplateResponse(
            request,
            "setup/step_kroger.html",
            {
                "error": message,
                "masked_client_id": _mask_value(settings.kroger_client_id),
                "masked_client_secret": _mask_value(settings.kroger_client_secret),
            },
        )


@router.post("/setup/search-stores", response_class=HTMLResponse)
async def search_stores(
    request: Request,
    zip_code: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Search for stores by zip code. Returns updated step_store.html partial."""
    settings = get_settings()
    success_token, _msg, app_token = await kroger_client.get_app_token(
        client_id=settings.kroger_client_id,
        client_secret=settings.kroger_client_secret,
    )
    if not success_token or not app_token:
        return templates.TemplateResponse(
            request,
            "partials/setup/store_results.html",
            {
                "stores": [],
                "error_message": "Could not authenticate with Kroger API. Please go back and re-verify your credentials.",
                "selected_store": None,
                "zip_code": zip_code,
            },
        )

    success, message, stores = await kroger_client.search_stores_by_zip(
        zip_code=zip_code,
        app_token=app_token,
    )
    return templates.TemplateResponse(
        request,
        "partials/setup/store_results.html",
        {
            "stores": stores,
            "error_message": message if not success else None,
            "selected_store": None,
            "zip_code": zip_code,
        },
    )


@router.post("/setup/select-store", response_class=HTMLResponse)
async def select_store(
    request: Request,
    store_id: str = Form(...),
    store_name: str = Form(...),
    store_zip: Optional[str] = Form(default=None),
    session: AsyncSession = Depends(get_session),
):
    """Save selected store and advance wizard to OAuth step."""
    cfg = await _get_or_create_config(session)
    cfg.store_id = store_id
    cfg.store_name = store_name
    cfg.store_zip = store_zip
    cfg.wizard_step = "store"
    session.add(cfg)
    await session.commit()
    return templates.TemplateResponse(
        request,
        "setup/step_oauth.html",
        {
            "store_name": store_name,
        },
    )


def _mask_value(value: str) -> str:
    """Mask a credential value, showing only the last 4 characters."""
    if not value:
        return "(not set)"
    if len(value) <= 4:
        return "****"
    return "****" + value[-4:]
