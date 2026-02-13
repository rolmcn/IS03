from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from urllib.parse import unquote
from sqlalchemy.ext.asyncio import AsyncSession
from eigva_app.database import get_async_session
from eigva_app.config import templates, settings
from eigva_app.services.login_service import (
    authenticate_user,
    register_user,
    confirm_registration_service
)

router = APIRouter()
SITE_KEY = settings.SITE_KEY


# =========================
# GET /login
# =========================
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    register_success_cookie = unquote(request.cookies.get("register_success", "")) if request.cookies.get("register_success") else None
    confirm_error_cookie = unquote(request.cookies.get("confirm_error", "")) if request.cookies.get("confirm_error") else None

    response = templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "site_key": SITE_KEY,
            "login_error": None,
            "login_success": None,
            "register_error": None,
            "register_success": None,
            "register_success_cookie": register_success_cookie,
            "confirm_error_cookie": confirm_error_cookie,
            "form_data": {},
        },
    )

    if register_success_cookie:
        response.delete_cookie("register_success")
    if confirm_error_cookie:
        response.delete_cookie("confirm_error")

    return response


# =========================
# POST /login
# =========================
@router.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, session: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    form_dict = dict(form)

    # LOGIN
    if "submit_login" in form:
        login_id = form.get("login_id", "").strip()
        password = form.get("password", "").strip()
        result = await authenticate_user(session, login_id, password, request)

        if "error" in result:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": result["error"],
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": {"login_id": login_id},
                },
            )

        # Sėkmės atvejis: nukreipiame ir nustatome cookie
        response = RedirectResponse(url="/account", status_code=303)
        response.set_cookie(
            key="session_id",
            value=result["session_id"],
            httponly=True,
            secure=False,  # gamybinėje True
            samesite="lax",
        )
        return response

    # REGISTRATION
    elif "submit_register" in form:
        first_name = form.get("first_name", "").strip()
        last_name = form.get("last_name", "").strip()
        email = form.get("email", "").strip()
        password = form.get("password", "").strip()
        recaptcha_response = form.get("g-recaptcha-response")

        result = await register_user(session, first_name, last_name, email, password, recaptcha_response)

        if "error" in result:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": None,
                    "login_success": None,
                    "register_error": result["error"],
                    "register_success": None,
                    "form_data": {"first_name": first_name, "last_name": last_name, "email": email},
                },
            )

        # Sėkmės atvejis
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "site_key": SITE_KEY,
                "login_error": None,
                "login_success": None,
                "register_error": None,
                "register_success": "Jūsų paskyra sukurta. El. paštu išsiųsta patvirtinimo nuoroda.",
                "form_data": {},
            },
        )

    # FALLBACK
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "site_key": SITE_KEY,
            "login_error": "Neteisinga užklausa",
            "login_success": None,
            "register_error": None,
            "register_success": None,
            "form_data": form_dict,
        },
    )


# =========================
# GET /login/confirm
# =========================
@router.get("/login/confirm", response_class=HTMLResponse)
async def login_confirm(request: Request, token: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    result = await confirm_registration_service(session, token)

    if result.get("status") != 200:
        return Response(status_code=result.get("status", 500))

    return templates.TemplateResponse(
        "confirm.html",
        {
            "request": request,
            "auto_close": True,
            "countdown": 10,
            "message": (
                "Jūsų el. pašto adresas sėkmingai patvirtintas.<br>"
                "Prisijungimo ID kodas Jums yra išsiųstas el. paštu."
            ),
        },
    )
