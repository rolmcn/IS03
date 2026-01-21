from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.config import templates

router = APIRouter()

@router.get("/works-auto", response_class=HTMLResponse)
async def works_auto_page(request: Request):
    return templates.TemplateResponse("works-auto.html", {"request": request, "active_page": "works-auto", "environment": "works"})
