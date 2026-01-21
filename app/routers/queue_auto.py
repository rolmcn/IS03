from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from app.config import templates

router = APIRouter()

@router.get("/queue-auto", response_class=HTMLResponse)
async def queue_auto_page(request: Request):
    return templates.TemplateResponse("queue-auto.html", {"request": request, "active_page": "queue-auto", "environment": "queue"})
