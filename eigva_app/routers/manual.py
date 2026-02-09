from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from eigva_app.utils.auth import get_current_user
from eigva_app.config import templates

router = APIRouter()

@router.get("/manual", response_class=HTMLResponse)
async def manual(request: Request, current_user=Depends(get_current_user)):
    """
    Žinyno / Manual puslapis
    Naudoja manual.html šabloną
    Perdavinėja realų vartotoją šablonui
    """
    return templates.TemplateResponse(
        "manual.html",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "manual"
        }
    )
