from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.config import templates

router = APIRouter()

@router.get("/account-auto.html", response_class=HTMLResponse)
async def account_auto_page(request: Request):
    return templates.TemplateResponse("account-auto.html", {"request": request, "active_page": "account-auto", "environment": "auto"})
