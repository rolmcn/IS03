from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import smtplib

from app.config import templates, settings
from app.database import get_async_session
from app.models.users import Users
from app.schemas.auth_schemas import ForgotLoginData
from app.utils.crypto import hash_password, decrypt_data
from app.utils.recaptcha import verify_recaptcha
from app.utils.rate_limiter import check_post_limit, register_post_attempt, reset_attempts
from app.utils.token import generate_confirmation_token, verify_confirmation_token
from app.utils.mail import send_reset_confirmation_email, send_reset_login_success_email
from app.utils.login_manager import generate_unique_login
from app.utils.blind_index import generate_login_index
from app.utils.logger import logger

router = APIRouter()
SITE_KEY = settings.SITE_KEY

# =========================
# GET /forgot-login
# =========================
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

# =========================
# POST /forgot-login
# =========================
@router.post("/forgot-login", response_class=HTMLResponse)
async def forgot_login_post(request: Request, session: AsyncSession = Depends(get_async_session)):
    form = await request.form()
    form_dict = dict(form)
    email = form.get("email", "").strip()
    password = form.get("password", "").strip()
    recaptcha_response = form.get("g-recaptcha-response")

    # 1️⃣ Rate limiter
    limit_error = check_post_limit(request)
    if limit_error:
        return templates.TemplateResponse(
            "forgot-login.html",
            {
                "request": request,
                "site_key": SITE_KEY,
                "forgot_login_error": limit_error,
                "forgot_login_success": None,
                "form_data": form_dict,
            },
        )

    # 2️⃣ Pydantic validacija
    try:
        ForgotLoginData(email=email, password=password)  # tik validacija
    except ValidationError as e:
        register_post_attempt(request)
        msg = e.errors()[0]["msg"].replace("Value error, ", "")
        return templates.TemplateResponse(
            "forgot-login.html",
            {
                "request": request,
                "site_key": SITE_KEY,
                "forgot_login_error": msg,
                "forgot_login_success": None,
                "form_data": {"email": email},
            },
        )

    # 3️⃣ reCAPTCHA tikrinimas
    if not recaptcha_response or not await verify_recaptcha(recaptcha_response):
        register_post_attempt(request)
        return templates.TemplateResponse(
            "forgot-login.html",
            {
                "request": request,
                "site_key": SITE_KEY,
                "forgot_login_error": "reCAPTCHA patvirtinimas nepavyko",
                "forgot_login_success": None,
                "form_data": {"email": email},
            },
        )

    # 4️⃣ Rodome sėkmės pranešimą visada, nepriklausomai nuo to, ar vartotojas egzistuoja
    response = templates.TemplateResponse(
        "forgot-login.html",
        {
            "request": request,
            "site_key": SITE_KEY,
            "forgot_login_error": None,
            "forgot_login_success": (
                "Jei Jūsų nurodytas el. pašto adresas yra registruotas mūsų informacinėje sistemoje "
                "ir yra aktyvus, el. paštu gausite patvirtinimo nuorodą"
            ),
            "form_data": {},
        },
    )

    # 5️⃣ Surandame vartotoją pagal email ir statusą active
    email_index = generate_login_index(email)
    result = await session.execute(select(Users).where(Users.email_index == email_index, Users.status == "active"))
    user = result.scalar_one_or_none()

    if not user:
        register_post_attempt(request)
        return response  # jei vartotojas nerastas, nieko daugiau nedarome

    # 6️⃣ Sukuriame reset token ir įrašome į DB
    reset_password_hash = hash_password(password)
    reset_token, reset_token_hash, reset_token_expires = generate_confirmation_token()
    user.reset_password_hash = reset_password_hash
    user.reset_confirmation_token_hash = reset_token_hash
    user.reset_confirmation_token_expires = reset_token_expires

    try:
        await session.commit()
        reset_attempts(request)
    except SQLAlchemyError:
        logger.exception(f"Failed to save reset token for user {user.id}")

    # 7️⃣ Siunčiame el. laišką su tokenu
    try:
        await send_reset_confirmation_email(
            email=email,
            user_id=user.id,
            token=reset_token
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send reset login success email to {email}")

    return response

# =========================
# GET /forgot-login/confirm
# =========================
@router.get("/forgot-login/confirm", response_class=HTMLResponse)
async def forgot_login_confirm(
    request: Request,
    token: str = Query(...),
    session: AsyncSession = Depends(get_async_session),
):
    # 1️⃣ Token atskyrimas į user_id ir token dalį
    try:
        user_id_str, token_part = token.split(".", 1)
        user_id = int(user_id_str)
    except (ValueError, AttributeError):
        return Response(status_code=404)

    # 2️⃣ Surandame vartotoją pagal user_id
    result = await session.execute(select(Users).where(Users.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "active" or not user.reset_confirmation_token_hash:
        return Response(status_code=204)

    # 3️⃣ Tikriname tokeno atitikimą
    if not verify_confirmation_token(token_part, user.reset_confirmation_token_hash):
        return Response(status_code=204)

    # 4️⃣ Tikriname tokeno galiojimą
    expires_at = user.reset_confirmation_token_expires
    now_utc = datetime.now(timezone.utc)
    if (
        expires_at is None
        or (expires_at.tzinfo is None and expires_at.replace(tzinfo=timezone.utc) < now_utc)
        or (expires_at.tzinfo is not None and expires_at < now_utc)
    ):
        return Response(status_code=410)

    # 5️⃣ Sukuriame naują login_id ir login_index
    try:
        login_id, login_index = await generate_unique_login(session)
        user.login_index = login_index
        user.password_hash = user.reset_password_hash
        user.reset_password_hash = None
        user.reset_confirmation_token_hash = None
        user.reset_confirmation_token_expires = None
        await session.commit()
    except SQLAlchemyError:
        logger.exception(f"Failed to update login info for user {user.id}")
        return Response(status_code=500)

    # 6️⃣ Siunčiame sėkmės el. laišką
    try:
        email_decrypted = decrypt_data(user.email_encrypted)
        await send_reset_login_success_email(
            email=email_decrypted,
            login_id=login_id
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send reset login success email to user {user.id}")

    # 7️⃣ Gražiname confirm.html su auto-close
    return templates.TemplateResponse(
        "confirm.html",
        {
            "request": request,
            "auto_close": True,
            "countdown": 10,
            "message": "Jūsų prisijungimo duomenys sėkmingai pakeisti. Naujas prisijungimo ID kodas išsiųstas el. paštu.",
        },
    )