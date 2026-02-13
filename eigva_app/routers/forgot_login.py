from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from eigva_app.config import templates, settings
from eigva_app.database import get_async_session
from eigva_app.services.forgot_login_service import forgot_login_post_logic, forgot_login_confirm_logic

router = APIRouter()
SITE_KEY = settings.SITE_KEY


@router.get("/forgot-login", response_class=HTMLResponse)
async def forgot_login_page(request: Request):
    return templates.TemplateResponse(
        "forgot-login.html",
        {
            "request": request,
            "site_key": SITE_KEY,
            "forgot_login_error": None,
            "forgot_login_success": None,
            "form_data": {},
        },
    )


@router.post("/forgot-login", response_class=HTMLResponse)
async def forgot_login_post(request: Request, session: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    form_dict = dict(form)

    result = await forgot_login_post_logic(request, form_dict, session)

    # Paduodame context į templates
    return templates.TemplateResponse(
        "forgot-login.html",
        {
            "request": request,
            "site_key": SITE_KEY,
            **result["context"]
        },
    )


@router.get("/forgot-login/confirm", response_class=HTMLResponse)
async def forgot_login_confirm(request: Request, token: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    status_code, context = await forgot_login_confirm_logic(token, session)
    if status_code != 200:
        return HTMLResponse(status_code=status_code)

    return templates.TemplateResponse(
        "confirm.html",
        {
            "request": request,
            **context
        },
    )
