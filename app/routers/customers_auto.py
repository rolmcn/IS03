from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.config import templates

router = APIRouter()

@router.get("/customers-auto", response_class=HTMLResponse)
async def customers_auto_page(request: Request):
    return templates.TemplateResponse("customers-auto.html", {"request": request, "active_page": "customers-auto", "environment": "customers"})
