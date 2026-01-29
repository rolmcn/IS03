from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from urllib.parse import unquote
import secrets
import smtplib

from app.config import templates, settings
from app.database import get_async_session
from app.models.users import Users
from app.models.sessions import UserSession
from app.schemas.auth_schemas import RegistrationData, LoginData
from app.utils.login_manager import generate_unique_login
from app.utils.blind_index import generate_login_index
from app.utils.crypto import encrypt_data, decrypt_data, hash_password, verify_password
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit, register_post_attempt, reset_attempts
from app.utils.token import generate_confirmation_token, verify_confirmation_token
from app.utils.mail import send_registration_confirmation_email, send_registration_success_email
from app.utils.logger import logger

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

    # =========================
    # LOGIN
    # =========================
    if "submit_login" in form:
        limit_error = check_post_limit(request)
        if limit_error:
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": limit_error.body.decode(),
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": form_dict,
                },
            )
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

        login_index = generate_login_index(data.login_id)
        result = await session.execute(select(Users).where(Users.login_index == login_index))
        user = result.scalar_one_or_none()

        if not user or not verify_password(data.password, user.password_hash):
            register_post_attempt(request)
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
            register_post_attempt(request)
            return templates.TemplateResponse(
                "login.html",
                {
                    "request": request,
                    "site_key": SITE_KEY,
                    "login_error": "Naudotojas neaktyvus",
                    "login_success": None,
                    "register_error": None,
                    "register_success": None,
                    "form_data": {"login_id": login_id},
                },
            )

        # Sukuriame sesiją
        session_id = secrets.token_urlsafe(32)
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            expires_at=UserSession.expiry()
        )
        try:
            session.add(user_session)
            await session.commit()
        except SQLAlchemyError:
            logger.exception(f"Failed to create session for user {user.id}")
            return Response(status_code=500)

        reset_attempts(request)
        response = RedirectResponse(url="/account-auto.html", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False, # perėjus prie https nustatyti True
            samesite="lax"
        )
        return response

    # =========================
    # REGISTRATION
    # =========================
    elif "submit_register" in form:
        first_name = form.get("first_name", "").strip()
        last_name = form.get("last_name", "").strip()
        email = form.get("email", "").strip()
        password = form.get("password", "").strip()
        recaptcha_response = form.get("g-recaptcha-response")

        # 1️⃣ Pydantic validacija
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

        # 2️⃣ reCAPTCHA tikrinimas
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

        # 3️⃣ Patikriname, ar el. paštas jau nėra užimtas
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

        # 4️⃣ Generuojame patvirtinimo tokeną
        token_part, token_hash, expires_at = generate_confirmation_token()

        # 5️⃣ Sukuriame vartotoją
        new_user = Users(
            first_name_encrypted=encrypt_data(data.first_name),
            last_name_encrypted=encrypt_data(data.last_name),
            email_encrypted=encrypt_data(data.email),
            email_index=email_index,
            login_index=None,
            password_hash=hash_password(data.password),
            status="pending",
            confirmation_token_hash=token_hash,
            confirmation_token_expires=expires_at,
        )

        # 6️⃣ Įrašome į DB
        try:
            session.add(new_user)
            await session.commit()
            await session.refresh(new_user)
        except SQLAlchemyError:
            logger.exception("Failed to create new user")
            return Response(status_code=500)

        # 7️⃣ Siunčiame patvirtinimo laišką
        try:
            await send_registration_confirmation_email(
                email=data.email,
                user_id=new_user.id,
                token=token_part
            )
        except (smtplib.SMTPException, ConnectionError, TimeoutError):
            logger.exception(f"Failed to send registration confirmation email to {data.email}")

        # 8️⃣ Gražiname atsakymą
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
async def confirm_registration(
    request: Request,
    token: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    # 1️⃣ Token formato patikrinimas
    try:
        user_id_str, token_part = token.split(".", 1)
        user_id = int(user_id_str)
    except (ValueError, AttributeError):
        return Response(status_code=404)

    # 2️⃣ Naudotojo paieška
    result = await session.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return Response(status_code=404)

    # 3️⃣ Tikriname statusą
    if user.status != "pending" or not user.confirmation_token_hash:
        return Response(status_code=204)

    # 4️⃣ Tikriname tokeno atitikimą
    if not verify_confirmation_token(token_part, user.confirmation_token_hash):
        return Response(status_code=204)

    # 5️⃣ Tikriname tokeno galiojimą
    expires_at = user.confirmation_token_expires
    now_utc = datetime.now(timezone.utc)
    if (
        expires_at is None
        or (expires_at.tzinfo is None and expires_at.replace(tzinfo=timezone.utc) < now_utc)
        or (expires_at.tzinfo is not None and expires_at < now_utc)
    ):
        return Response(status_code=410)

    # 6️⃣ Sėkmingas patvirtinimas
    try:
        email = decrypt_data(user.email_encrypted)
    except (ValueError, TypeError):
        logger.exception(f"Email decryption failed for user {user.id}")
        return Response(status_code=500)

    user.status = "active"
    user.confirmation_token_hash = None
    user.confirmation_token_expires = None

    try:
        login_id, login_index = await generate_unique_login(session)
        user.login_index = login_index
        await session.commit()
    except SQLAlchemyError:
        logger.exception(f"Failed to activate user {user.id}")
        return Response(status_code=500)

    # Siunčiame sėkmės el. laišką
    try:
        await send_registration_success_email(
            email=email,
            login_id=login_id,
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send registration success email to {email}")

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