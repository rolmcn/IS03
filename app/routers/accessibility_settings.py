from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.config import templates

router = APIRouter()

@router.get("/accessibility-settings", response_class=HTMLResponse)
async def accessibility_settings_page(request: Request):
    return templates.TemplateResponse("accessibility-settings.html", {"request": request})