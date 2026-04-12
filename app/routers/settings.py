"""Settings router: /settings/* endpoints for the settings hub."""
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.config import get_settings
from app.models.config_model import AppConfig
from app.services import llm_service, kroger_client
from app.constants import get_models_for_provider
from app.services.llm_config import get_active_llm_config
from app.services.oauth_manager import get_or_create_fernet, get_valid_access_token

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="templates")


async def _get_or_create_config(session: AsyncSession) -> AppConfig:
    """Get or create AppConfig row (always id=1)."""
    result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    if cfg is None:
        cfg = AppConfig(id=1)
        session.add(cfg)
        await session.commit()
        await session.refresh(cfg)
    return cfg


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    section: str = "llm",
    db: AsyncSession = Depends(get_session),
):
    """Main settings page with sidebar sub-navigation."""
    cfg = await _get_or_create_config(db)
    llm_cfg = await get_active_llm_config(db)
    is_authorized = bool(await get_valid_access_token(db))
    models = await get_models_for_provider(
        cfg.llm_provider, cfg.llm_ollama_base_url
    )

    return templates.TemplateResponse(
        request,
        "pages/settings.html",
        {
            "active_page": "settings",
            "active_section": section,
            "cfg": cfg,
            "llm_cfg": llm_cfg,
            "has_db_key": bool(cfg.llm_api_key_encrypted),
            "is_authorized": is_authorized,
            "models": models,
            "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
        },
    )


@router.get("/settings/section/{section}", response_class=HTMLResponse)
async def settings_section(
    request: Request,
    section: str,
    db: AsyncSession = Depends(get_session),
):
    """HTMX partial for settings section switching."""
    cfg = await _get_or_create_config(db)

    if section == "llm":
        llm_cfg = await get_active_llm_config(db)
        models = await get_models_for_provider(
            cfg.llm_provider, cfg.llm_ollama_base_url
        )
        return templates.TemplateResponse(
            request,
            "partials/settings/llm.html",
            {
                "active_section": section,
                "cfg": cfg,
                "llm_cfg": llm_cfg,
                "has_db_key": bool(cfg.llm_api_key_encrypted),
                "models": models,
                "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
            },
        )
    elif section == "store":
        return templates.TemplateResponse(
            request,
            "partials/settings/store.html",
            {
                "active_section": section,
                "cfg": cfg,
            },
        )
    elif section == "account":
        is_authorized = bool(await get_valid_access_token(db))
        return templates.TemplateResponse(
            request,
            "partials/settings/account.html",
            {
                "active_section": section,
                "cfg": cfg,
                "is_authorized": is_authorized,
            },
        )
    elif section == "preferences":
        return templates.TemplateResponse(
            request,
            "partials/settings/preferences.html",
            {
                "active_section": section,
                "cfg": cfg,
            },
        )
    else:
        # Default fallback to LLM section
        llm_cfg = await get_active_llm_config(db)
        models = await get_models_for_provider(
            cfg.llm_provider, cfg.llm_ollama_base_url
        )
        return templates.TemplateResponse(
            request,
            "partials/settings/llm.html",
            {
                "active_section": "llm",
                "cfg": cfg,
                "llm_cfg": llm_cfg,
                "has_db_key": bool(cfg.llm_api_key_encrypted),
                "models": models,
                "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
            },
        )


@router.post("/settings/save-llm", response_class=HTMLResponse)
async def save_llm(
    request: Request,
    provider: str = Form(...),
    model: str = Form(default=""),
    api_key: str = Form(default=""),
    custom_model: str = Form(default=""),
    ollama_base_url: str = Form(default=""),
    db: AsyncSession = Depends(get_session),
):
    """Save LLM provider configuration after test_connection succeeds."""
    cfg = await _get_or_create_config(db)

    # Determine active model: custom_model takes precedence over model dropdown
    active_model = custom_model.strip() if custom_model.strip() else model.strip()
    # Determine active key and base_url
    active_key = api_key.strip() if provider != "ollama" else ""
    base_url = ollama_base_url.strip() if provider == "ollama" else None

    # Test connection before saving (D-08)
    success, message = await llm_service.test_connection(
        api_key=active_key,
        provider=provider,
        model=active_model,
        base_url=base_url,
    )

    llm_cfg = await get_active_llm_config(db)

    if not success:
        models = await get_models_for_provider(provider, base_url)
        return templates.TemplateResponse(
            request,
            "partials/settings/llm.html",
            {
                "active_section": "llm",
                "cfg": cfg,
                "llm_cfg": llm_cfg,
                "has_db_key": bool(cfg.llm_api_key_encrypted),
                "error": f"Connection failed: {message}. Check your API key and try again.",
                "models": models,
                "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
            },
        )

    # Test passed — save the config
    cfg.llm_provider = provider
    cfg.llm_model = active_model

    if provider == "ollama":
        cfg.llm_api_key_encrypted = None
        cfg.llm_ollama_base_url = ollama_base_url.strip() or None
    else:
        cfg.llm_ollama_base_url = None
        # Only overwrite key if user provided one (leave blank to keep current)
        if active_key:
            f = get_or_create_fernet()
            cfg.llm_api_key_encrypted = f.encrypt(active_key.encode()).decode()

    await db.commit()
    await db.refresh(cfg)

    # Re-read llm_cfg after save
    llm_cfg = await get_active_llm_config(db)

    models = await get_models_for_provider(provider, base_url)
    return templates.TemplateResponse(
        request,
        "partials/settings/llm.html",
        {
            "active_section": "llm",
            "cfg": cfg,
            "llm_cfg": llm_cfg,
            "has_db_key": bool(cfg.llm_api_key_encrypted),
            "success": "Provider updated successfully.",
            "models": models,
            "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
        },
    )


@router.get("/settings/models", response_class=HTMLResponse)
async def list_models(
    request: Request,
    provider: str = "anthropic",
    ollama_base_url: str = "",
    current_model: str = "",
):
    """HTMX partial: return <option> elements for available models."""
    models = await get_models_for_provider(provider, ollama_base_url or None)
    return templates.TemplateResponse(
        request,
        "partials/settings/model_options.html",
        {
            "models": models,
            "model_ids": [m["id"] for m in models],
            "current_model": cfg.llm_model,
            "current_model": current_model,
        },
    )


@router.post("/settings/search-stores", response_class=HTMLResponse)
async def settings_search_stores(
    request: Request,
    zip_code: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Search for stores by zip code (settings-specific, no wizard_step mutation)."""
    cfg = await _get_or_create_config(db)
    settings = get_settings()

    # Get app token for store search
    success_token, _msg, app_token = await kroger_client.get_app_token(
        client_id=settings.kroger_client_id,
        client_secret=settings.kroger_client_secret,
    )

    if not success_token or not app_token:
        return templates.TemplateResponse(
            request,
            "partials/settings/store.html",
            {
                "active_section": "store",
                "cfg": cfg,
                "stores": [],
                "zip_code": zip_code,
                "error": "Could not authenticate with Kroger API. Check your Kroger credentials.",
            },
        )

    success, message, stores = await kroger_client.search_stores_by_zip(
        zip_code=zip_code,
        app_token=app_token,
    )

    return templates.TemplateResponse(
        request,
        "partials/settings/store.html",
        {
            "active_section": "store",
            "cfg": cfg,
            "stores": stores,
            "zip_code": zip_code,
            "error": message if not success else None,
        },
    )


@router.post("/settings/select-store", response_class=HTMLResponse)
async def settings_select_store(
    request: Request,
    store_id: str = Form(...),
    store_name: str = Form(...),
    store_zip: str = Form(default=""),
    db: AsyncSession = Depends(get_session),
):
    """Save selected store without touching wizard_step or wizard_complete."""
    cfg = await _get_or_create_config(db)
    cfg.store_id = store_id
    cfg.store_name = store_name
    cfg.store_zip = store_zip or None
    # Do NOT modify wizard_step or wizard_complete (Pitfall 4 from RESEARCH)
    await db.commit()
    await db.refresh(cfg)

    return templates.TemplateResponse(
        request,
        "partials/settings/store.html",
        {
            "active_section": "store",
            "cfg": cfg,
            "success": f"{store_name} saved.",
        },
    )


@router.post("/settings/save-preferences", response_class=HTMLResponse)
async def save_preferences(
    request: Request,
    review_mode: str = Form(...),
    db: AsyncSession = Depends(get_session),
):
    """Save review mode preference."""
    cfg = await _get_or_create_config(db)
    cfg.review_mode = review_mode
    await db.commit()
    await db.refresh(cfg)

    return templates.TemplateResponse(
        request,
        "partials/settings/preferences.html",
        {
            "active_section": "preferences",
            "cfg": cfg,
            "success": "Preferences saved.",
        },
    )
