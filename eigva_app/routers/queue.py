from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from eigva_app.config import templates

router = APIRouter()

@router.get("/queue", response_class=HTMLResponse)
async def queue_auto_page(request: Request):
    return templates.TemplateResponse("queue.html", {"request": request, "active_page": "queue", "environment": "queue"})
