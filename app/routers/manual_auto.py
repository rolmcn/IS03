from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.utils.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/manual-auto", response_class=HTMLResponse)
async def manual(request: Request, current_user=Depends(get_current_user)):
    """
    Žinyno / Manual puslapis
    Naudoja manual-auto.html šabloną
    Perdavinėja realų vartotoją šablonui
    """
    return templates.TemplateResponse(
        "manual-auto.html",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "manual"
        }
    )
