from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from eigva_app.config import templates

router = APIRouter()

@router.get("/customers", response_class=HTMLResponse)
async def customers_auto_page(request: Request):
    return templates.TemplateResponse("customers.html", {"request": request, "active_page": "customers", "environment": "customers"})
