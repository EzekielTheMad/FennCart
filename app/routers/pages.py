from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.services.preference_service import PreferenceService

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("pages/shopping.html", {"request": request, "active_page": "shopping"})


@router.get("/shopping")
async def shopping(request: Request):
    return templates.TemplateResponse("pages/shopping.html", {"request": request, "active_page": "shopping"})


@router.get("/preferences")
async def preferences(request: Request, db: AsyncSession = Depends(get_session)):
    entries = await PreferenceService(db).list_preferences()
    return templates.TemplateResponse(
        "pages/preferences.html",
        {"request": request, "active_page": "preferences", "preferences": entries},
    )


@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("pages/history.html", {"request": request, "active_page": "history"})



@router.get("/tour")
async def tour(request: Request):
    return templates.TemplateResponse("tour.html", {"request": request})
