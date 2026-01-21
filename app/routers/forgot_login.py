from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.config import templates


router = APIRouter()

@router.get("/forgot-login", response_class=HTMLResponse)
async def forgot_login_page(request: Request):
    return templates.TemplateResponse(
        "forgot-login.html",
        {
            "request": request
        }
    )