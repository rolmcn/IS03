from datetime import datetime
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import ValidationError
from urllib.parse import unquote

from app.config import templates, settings
from app.database import get_async_session
from app.models.users import Users
from app.schemas.auth_schemas import RegistrationData, LoginData
from app.utils.login_manager import generate_unique_login
from app.utils.blind_index import generate_login_index
from app.utils.crypto import encrypt_data, decrypt_data, hash_password, verify_password
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit
from app.utils.token import generate_confirmation_token, verify_confirmation_token
from app.utils.mail import send_registration_confirmation_email, send_registration_success_email, send_confirmation_expired_email

router = APIRouter()
SITE_KEY = settings.SITE_KEY

# =========================
# GET /login
# =========================
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Rodo prisijungimo / registracijos puslapį.
    Pasiima flash cookies pranešimams apie registraciją arba tokeno klaidas.
    """
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

    # Ištriname flash cookies po atvaizdavimo
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
    """
    Apdoroja login arba registration formų pateikimą.
    """
    form = await request.form()
    form_dict = dict(form)

    # Rate limiter
    limit_error = check_post_limit(request)
    if limit_error:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "site_key": SITE_KEY,
                "login_error": limit_error,
                "login_success": None,
                "register_error": None,
                "register_success": None,
                "form_data": form_dict,
            },
        )

    # =========================
    # LOGIN
    # =========================
    if "submit_login" in form:
        login_id = form.get("login_id", "").strip()
        password = form.get("password", "").strip()

        try:
            data = LoginData(login_id=login_id, password=password)
        except ValidationError as e:
            msg = e.errors()[0]["msg"].replace("Value error, ", "")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": msg,
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": {"login_id": login_id},
                },
            )

        print("DEBUG: generate_login_index type:", type(generate_login_index))
        login_index = generate_login_index(data.login_id)
        result = await session.execute(select(Users).where(Users.login_index == login_index))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": "Neteisingas prisijungimo ID arba slaptažodis",
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": {"login_id": login_id},
                },
            )

        if user.status != "active":
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": "Vartotojas neaktyvus",
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": {"login_id": login_id},
                },
            )

        # Sėkmingas prisijungimas → nukreipiame į saugų puslapį
        return RedirectResponse(
            url="/account-auto.html",
            status_code=303
        )


    # =========================
    # REGISTRATION
    # =========================
    elif "submit_register" in form:
        first_name = form.get("first_name", "").strip()
        last_name = form.get("last_name", "").strip()
        email = form.get("email", "").strip()
        password = form.get("password", "").strip()
        recaptcha_response = form.get("g-recaptcha-response")

        try:
            data = RegistrationData(first_name=first_name, last_name=last_name, email=email, password=password)
        except ValidationError as e:
            msg = e.errors()[0]["msg"].replace("Value error, ", "")
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": None,
                    "login_success": None,
                    "register_error": msg,
                    "register_success": None,
                    "form_data": {"first_name": first_name, "last_name": last_name, "email": email},
                },
            )

        if not recaptcha_response or not await verify_recaptcha(recaptcha_response):
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": None,
                    "login_success": None,
                    "register_error": "reCAPTCHA patvirtinimas nepavyko",
                    "register_success": None,
                    "form_data": {"first_name": first_name, "last_name": last_name, "email": email},
                },
            )

        email_index = generate_login_index(data.email)
        result = await session.execute(select(Users).where(Users.email_index == email_index))
        if result.scalar_one_or_none():
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": None,
                    "login_success": None,
                    "register_error": "Naudotojas su šiuo el. pašto adresu jau egzistuoja",
                    "register_success": None,
                    "form_data": {"first_name": first_name, "last_name": last_name, "email": email},
                },
            )

        token, token_hash, expires_at = generate_confirmation_token()
        new_user = Users(
            first_name_encrypted=encrypt_data(data.first_name),
            last_name_encrypted=encrypt_data(data.last_name),
            email_encrypted=encrypt_data(data.email),
            mobile_phone_encrypted=None,
            mobile_phone_index=None,
            email_index=email_index,
            login_index=None,
            password_hash=hash_password(data.password),
            status="pending",
            confirmation_token_hash=token_hash,
            confirmation_token_expires=expires_at,
        )
        session.add(new_user)
        await session.commit()

        # Siunčiame patvirtinimo laišką
        await send_registration_confirmation_email(email=data.email, token=token)

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

    # =========================
    # FALLBACK
    # =================
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
async def confirm_registration(
    request: Request,
    token: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Patvirtina vartotojo registraciją pagal tokeną.
    - Jei tokenas galioja → aktyvuoja vartotoją, ištrina tokeną, siunčia sėkmės laišką
    - Jei tokenas negalioja arba nerastas → siunčia tokeno negaliojimo laišką
    - Visada atvaizduoja confirm.html su pranešimu vartotojui
    """
    # 1. Randame vartotoją, kuris dar nėra aktyvus ir turi tokeną
    result = await session.execute(
        select(Users).where(
            Users.status == "pending",
            Users.confirmation_token_hash.isnot(None),
        )
    )
    users = result.scalars().all()

    user = next(
        (u for u in users if verify_confirmation_token(token, u.confirmation_token_hash)),
        None,
    )

    # 2. Jei vartotojas nerastas → tokenas neteisingas
    if not user:
        return templates.TemplateResponse(
            "confirm.html",
            {
                "request": request,
                "auto_close": False,
                "countdown": 10,
                "message": "Tokenas neteisingas arba pasibaigęs. Prašome registruotis iš naujo."
            },
        )

    email = decrypt_data(user.email_encrypted)

    # 3. Jei tokenas rastas, bet pasibaigęs
    if not user.confirmation_token_expires or user.confirmation_token_expires < datetime.utcnow():
        await send_confirmation_expired_email(email)
        return templates.TemplateResponse(
            "confirm.html",
            {
                "request": request,
                "auto_close": False,
                "countdown": 10,
                "message": "Patvirtinimo nuorodos galiojimo laikas pasibaigė. Prašome registruotis iš naujo."
            },
        )

    # 4. Tokenas galioja → aktyvuojame vartotoją
    user.status = "active"
    user.confirmation_token_hash = None
    user.confirmation_token_expires = None

    login_id, login_index = await generate_unique_login(session)
    user.login_index = login_index

    await session.commit()

    # 5. Siunčiame sėkmingos registracijos laišką
    await send_registration_success_email(
        email=email,
        login_id=login_id,
    )

    # 6. Atvaizduojame confirm.html su automatinio uždarymo žinute
    return templates.TemplateResponse(
        "confirm.html",
        {
            "request": request,
            "auto_close": True,
            "countdown": 10,
            "message": f"Jūsų el. pašto adresas sėkmingai patvirtintas. Prisijungimo ID kodas Jums yra išsiųstas el. paštu."
        },
    )
