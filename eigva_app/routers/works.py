from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from eigva_app.config import templates

router = APIRouter()

@router.get("/works", response_class=HTMLResponse)
async def works_auto_page(request: Request):
    return templates.TemplateResponse("works.html", {"request": request, "active_page": "works", "environment": "works"})
