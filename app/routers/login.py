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
from app.models.user import User
from app.models.session import UserSession
from app.models.message import Message, MessageEventType
from app.schemas.auth_schemas import RegistrationData, LoginData
from app.utils.login_manager import generate_unique_login
from app.utils.blind_index import generate_login_index
from app.utils.crypto import encrypt_data, decrypt_data, hash_password, verify_password
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit, register_post_attempt, reset_attempts
from app.utils.token import generate_confirmation_token, verify_confirmation_token
from app.utils.mail import send_registration_confirmation_email, send_registration_success_email
from app.utils.logger import logger
from app.utils.system_messages import SystemMessages

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

        # 1️⃣ POST limit tikrinimas
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

        # 2️⃣ Pydantic validacija
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

        # 3️⃣ Naudotojo paieška
        login_index = generate_login_index(data.login_id)
        result = await session.execute(select(User).where(User.login_index == login_index))
        user = result.scalar_one_or_none()

        # 4️⃣ Slaptažodžio tikrinimas
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

        # 5️⃣ Statuso tikrinimas
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

        # 6️⃣ Sukuriame sesiją
        session_id = secrets.token_urlsafe(32)
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            expires_at=UserSession.expiry(),
        )

        try:
            session.add(user_session)
            await session.commit()
        except SQLAlchemyError:
            logger.exception(f"Failed to create session for user {user.id}")
            return Response(status_code=500)

        # 7️⃣ Reset login bandymus
        reset_attempts(request)

        # 8️⃣ Nukreipiame į paskyrą
        response = RedirectResponse(url="/account-auto", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,
            samesite="lax",
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

        # 3️⃣ El. pašto unikalumo tikrinimas
        email_index = generate_login_index(data.email)
        result = await session.execute(select(User).where(User.email_index == email_index))
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

        # 5️⃣ Sukuriame naudotoją
        new_user = User(
            first_name_encrypted=encrypt_data(data.first_name),
            last_name_encrypted=encrypt_data(data.last_name),
            email_encrypted=encrypt_data(data.email),
            email_index=email_index,
            login_index=None,
            password_hash=hash_password(data.password),
            status="pending",
            confirmation_token_hash=token_hash,
            confirmation_token_expires=expires_at,
            super_user=True,
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

        # 8️⃣ Grąžiname atsakymą
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
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return Response(status_code=404)

    # 3️⃣ Statuso tikrinimas
    if user.status != "pending" or not user.confirmation_token_hash:
        return Response(status_code=204)

    # 4️⃣ Token tikrinimas
    if not verify_confirmation_token(token_part, user.confirmation_token_hash):
        return Response(status_code=204)

    # 5️⃣ Token galiojimo tikrinimas
    expires_at = user.confirmation_token_expires
    now_utc = datetime.now(timezone.utc)
    if expires_at is None or expires_at < now_utc:
        return Response(status_code=410)

    # 6️⃣ Aktyvuojame naudotoją
    try:
        email = decrypt_data(user.email_encrypted)
    except (ValueError, TypeError):
        logger.exception(f"Email decryption failed for user {user.id}")
        return Response(status_code=500)

    user.status = "active"
    user.confirmation_token_hash = None
    user.confirmation_token_expires = None
    user.email_verified_at = datetime.now(timezone.utc)

    try:
        login_id, login_index = await generate_unique_login(session)
        user.login_index = login_index
        await session.commit()
    except SQLAlchemyError:
        logger.exception(f"Failed to activate user {user.id}")
        return Response(status_code=500)

    # 7️⃣ Sukuriame FIRST_LOGIN sisteminį pranešimą
    if user.super_user:
        message_content = SystemMessages.super_user_first_login_message(user)
    else:
        message_content = SystemMessages.user_first_login_message(user)

    message = Message(
        user_id=user.id,
        msg_title="Sveikiname prisijungus",
        msg_content=message_content,
        msg_type="system",
        msg_status="sent",
        msg_read=None,
        msg_event_type=MessageEventType.FIRST_LOGIN.value,
        msg_created_at=datetime.now(timezone.utc),
    )

    try:
        session.add(message)
        await session.commit()
    except SQLAlchemyError:
        logger.exception(f"Failed to create first login message for user {user.id}")

    # 8️⃣ Siunčiame sėkmės el. laišką
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
