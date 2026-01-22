from typing_extensions import Annotated

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import templates
from app.models.users import Users
from app.utils.auth import get_current_user


router = APIRouter()

# Type alias FastAPI Depends + Users
CurrentUser = Annotated[Users, Depends(get_current_user)]


@router.get("/account-auto.html", response_class=HTMLResponse)
async def account_auto_page(
    request: Request,
    current_user: CurrentUser,
):
    # Jei dėl kokios nors priežasties vartotojas neaktyvus –
    # (teoriškai neturėtų nutikti, nes auth.py jau tikrina)
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "account-auto.html",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "account-auto",
            "environment": "auto",
        }
    )
