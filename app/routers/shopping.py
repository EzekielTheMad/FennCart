"""Shopping router: all /shopping/* endpoints for the list-to-cart flow."""
import json
import re
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi.templating import Jinja2Templates
from app.config import get_settings
from app.services.kroger_config import get_active_kroger_config
from app.services.llm_config import get_active_llm_config

templates = Jinja2Templates(directory="templates")
from app.database import get_session
from app.services.cart_service import CartService
from app.services.oauth_manager import get_valid_access_token
from app.schemas.shopping import ConfirmedItem, MatchResult, ProductCandidate
from app.models.config_model import AppConfig

router = APIRouter(prefix="/shopping", tags=["shopping"])


@router.get("")
async def shopping_page(request: Request):
    """Render the shopping list input page."""
    return templates.TemplateResponse(
        request,
        "pages/shopping.html",
        {"active_page": "shopping"},
    )


@router.post("/preview")
async def shopping_preview(
    request: Request,
    list_text: str = Form(""),
):
    """HTMX partial: live list preview with 400ms debounce (D-01).

    Lightweight regex-based parse — NOT LLM — for instant feedback.
    Returns rendered list_preview.html partial.
    """
    if not list_text or len(list_text.strip()) < 2:
        return HTMLResponse("")

    parsed_items = _quick_parse(list_text)
    return templates.TemplateResponse(
        request,
        "partials/list_preview.html",
        {"items": parsed_items},
    )


@router.post("/match")
async def shopping_match(
    request: Request,
    list_text: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Main pipeline: parse list + search Kroger + LLM match.

    Stores match_result and candidates in server-side session for swap/confirm endpoints.
    Returns review_screen.html partial swapped into #shopping-content.
    """
    if not list_text or len(list_text.strip()) < 2:
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Your list is empty",
                "error_body": "Paste or type at least one item to get started.",
                "show_retry": False,
            },
        )

    # Get store_id and LLM config from AppConfig (DB-authoritative, per D-10)
    result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    location_id = (cfg.store_id or "") if cfg else ""
    review_mode = (cfg.review_mode or "exceptions") if cfg else "exceptions"

    llm_cfg = await get_active_llm_config(session)
    kroger_cfg = await get_active_kroger_config(session)

    cart_service = CartService(
        db=session,
        location_id=location_id,
        kroger_client_id=kroger_cfg["client_id"],
        kroger_client_secret=kroger_cfg["client_secret"],
        llm_api_key=llm_cfg["api_key"],
        llm_provider=llm_cfg["provider"],
        llm_model=llm_cfg["model"],
        llm_ollama_base_url=llm_cfg["ollama_base_url"],
    )

    try:
        match_result, candidates_dict = await cart_service.process_list(list_text)
        review_items, auto_items = cart_service.partition_matches(match_result)

        # Persist match data in server-side session for swap + confirm endpoints
        request.session["match_data"] = match_result.model_dump_json()
        request.session["candidates"] = json.dumps(
            {k: [c.model_dump() for c in v] for k, v in candidates_dict.items()}
        )

        return templates.TemplateResponse(
            request,
            "partials/review_screen.html",
            {
                "review_items": review_items,
                "auto_items": auto_items,
                "candidates_dict": candidates_dict,
                "total_items": len(match_result.matches),
                "preferences_loaded": cart_service.preferences_loaded,
                "review_mode": review_mode,
            },
        )
    except RuntimeError as e:
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Matching failed",
                "error_body": str(e) + ". Try again or check your LLM settings.",
                "show_retry": True,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Matching failed",
                "error_body": f"Unexpected error: {str(e)}. Try again or check your LLM settings.",
                "show_retry": True,
            },
        )



@router.post("/add-to-cart")
async def shopping_add_to_cart(
    request: Request,
    confirmed_items_json: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    """Confirm and add items to Kroger cart (CART-01).

    Accepts JSON string of ConfirmedItem dicts from the review form.
    Returns success_screen.html or error_block.html partial.
    """
    # Parse confirmed items from form JSON
    try:
        items_raw = json.loads(confirmed_items_json)
        confirmed_items = [ConfirmedItem(**item) for item in items_raw]
    except (json.JSONDecodeError, Exception) as e:
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Matching failed",
                "error_body": f"Could not read selected items: {str(e)}. Try again or check your LLM settings.",
                "show_retry": True,
            },
        )

    # Get user OAuth access token
    access_token = await get_valid_access_token(session)
    if access_token is None:
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Session expired",
                "error_body": 'Your Kroger session expired. <a href="/setup" class="text-red-300 underline">Reconnect in Settings.</a>',
                "show_retry": False,
            },
        )

    result = await session.execute(select(AppConfig).where(AppConfig.id == 1))
    cfg = result.scalar_one_or_none()
    location_id = (cfg.store_id or "") if cfg else ""

    llm_cfg = await get_active_llm_config(session)
    kroger_cfg = await get_active_kroger_config(session)

    cart_service = CartService(
        db=session,
        location_id=location_id,
        kroger_client_id=kroger_cfg["client_id"],
        kroger_client_secret=kroger_cfg["client_secret"],
        llm_api_key=llm_cfg["api_key"],
        llm_provider=llm_cfg["provider"],
        llm_model=llm_cfg["model"],
        llm_ollama_base_url=llm_cfg["ollama_base_url"],
    )

    cart_session_record, success_count, fail_count, error_msg = (
        await cart_service.add_confirmed_to_cart(confirmed_items, access_token)
    )

    if fail_count == len(confirmed_items):
        # Total failure
        return templates.TemplateResponse(
            request,
            "partials/error_block.html",
            {
                "error_heading": "Matching failed",
                "error_body": "Could not add items to your cart. Kroger may be temporarily unavailable. Your selections were not saved.",
                "show_retry": True,
            },
        )

    return templates.TemplateResponse(
        request,
        "partials/success_screen.html",
        {
            "session": cart_session_record,
            "items": confirmed_items,
            "success_count": success_count,
            "fail_count": fail_count,
            "error_msg": error_msg,
        },
    )


def _quick_parse(text: str) -> list[dict]:
    """Fast regex-based parse for live preview — NOT LLM.

    Handles patterns like "2 apples", "eggs, a dozen", "milk, 2%".
    Returns list of {name, quantity} dicts.
    """
    items = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Try to extract leading quantity: "2 apples", "3 eggs"
        qty_match = re.match(r"^(\d+)\s+(.+)$", line)
        if qty_match:
            quantity = int(qty_match.group(1))
            name = qty_match.group(2).strip()
        else:
            quantity = 1
            name = line

        # Strip trailing notes after comma/dash for cleaner display
        # Keep the full name for search purposes
        items.append({"name": name, "quantity": quantity})

    return items
