from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.services.preference_service import PreferenceService
from app.models.cart_session import CartSession
from app.models.cart_item import CartItem

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "pages/shopping.html", {"active_page": "shopping"})


@router.get("/shopping")
async def shopping(request: Request):
    return templates.TemplateResponse(request, "pages/shopping.html", {"active_page": "shopping"})


@router.get("/preferences")
async def preferences(request: Request, db: AsyncSession = Depends(get_session)):
    entries = await PreferenceService(db).list_preferences()
    return templates.TemplateResponse(
        request,
        "pages/preferences.html",
        {"active_page": "preferences", "preferences": entries},
    )


@router.get("/history")
async def history(request: Request, db: AsyncSession = Depends(get_session)):
    # Query all sessions, newest first (per D-04)
    result = await db.execute(
        select(CartSession).order_by(CartSession.created_at.desc())
    )
    sessions = result.scalars().all()

    # For each session, load its items
    sessions_with_items = []
    for s in sessions:
        items_result = await db.execute(
            select(CartItem).where(CartItem.session_id == s.id).order_by(CartItem.added_at)
        )
        items = items_result.scalars().all()
        sessions_with_items.append({"session": s, "items": items})

    return templates.TemplateResponse(
        request,
        "pages/history.html",
        {
            "active_page": "history",
            "sessions": sessions_with_items,
            "session_count": len(sessions),
        },
    )



@router.get("/tour")
async def tour(request: Request):
    return templates.TemplateResponse(request, "tour.html")
