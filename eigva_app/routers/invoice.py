from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from eigva_app.config import templates, CONTACT_INFO

router = APIRouter()

@router.get("/invoice", response_class=HTMLResponse)
async def invoice_page(request: Request):
    return templates.TemplateResponse(
        "invoice.html",
        {"request": request, "contact": CONTACT_INFO},
    )