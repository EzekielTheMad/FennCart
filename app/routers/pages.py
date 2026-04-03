from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def index(request: Request):
    return templates.TemplateResponse("pages/shopping.html", {"request": request, "active_page": "shopping"})


@router.get("/shopping")
async def shopping(request: Request):
    return templates.TemplateResponse("pages/shopping.html", {"request": request, "active_page": "shopping"})


@router.get("/preferences")
async def preferences(request: Request):
    return templates.TemplateResponse("pages/preferences.html", {"request": request, "active_page": "preferences"})


@router.get("/history")
async def history(request: Request):
    return templates.TemplateResponse("pages/history.html", {"request": request, "active_page": "history"})


@router.get("/settings")
async def settings(request: Request):
    return templates.TemplateResponse("pages/settings.html", {"request": request, "active_page": "settings"})


@router.get("/tour")
async def tour(request: Request):
    return templates.TemplateResponse("tour.html", {"request": request})
