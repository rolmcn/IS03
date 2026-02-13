from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import smtplib

from eigva_app.models.user import User
from eigva_app.schemas.auth_schemas import ForgotLoginData
from eigva_app.core.security.crypto import hash_password, decrypt_data
from eigva_app.core.security.recaptcha import verify_recaptcha
from eigva_app.core.rate_limiting.rate_limiter import check_post_limit, register_post_attempt, reset_attempts
from eigva_app.core.security.token import generate_confirmation_token, verify_confirmation_token
from eigva_app.core.communication.mail import send_reset_confirmation_email, send_reset_login_success_email
from eigva_app.core.security.login_manager import generate_unique_login
from eigva_app.core.security.blind_index import generate_login_index
from eigva_app.core.logging.logger import logger


async def forgot_login_post_logic(request, form_data: dict, session: AsyncSession):
    """
    Atliekame visą forgot-login POST logiką.
    Grąžina dict su:
        - 'response_type': 'success' arba 'error'
        - 'context': dict, kurį galima perduoti templates.TemplateResponse
    """
    email = form_data.get("email", "").strip()
    password = form_data.get("password", "").strip()
    recaptcha_response = form_data.get("g-recaptcha-response")

    # 1️⃣ Rate limiter
    limit_error = check_post_limit(request)
    if limit_error:
        return {
            "response_type": "error",
            "context": {
                "forgot_login_error": limit_error,
                "forgot_login_success": None,
                "form_data": form_data,
            }
        }

    # 2️⃣ Pydantic validacija
    try:
        ForgotLoginData(email=email, password=password)
    except ValidationError as e:
        register_post_attempt(request)
        msg = e.errors()[0]["msg"].replace("Value error, ", "")
        return {
            "response_type": "error",
            "context": {
                "forgot_login_error": msg,
                "forgot_login_success": None,
                "form_data": {"email": email},
            }
        }

    # 3️⃣ reCAPTCHA tikrinimas
    if not recaptcha_response or not await verify_recaptcha(recaptcha_response):
        register_post_attempt(request)
        return {
            "response_type": "error",
            "context": {
                "forgot_login_error": "reCAPTCHA patvirtinimas nepavyko",
                "forgot_login_success": None,
                "form_data": {"email": email},
            }
        }

    # 4️⃣ Rodome sėkmės pranešimą visada
    response_context = {
        "forgot_login_error": None,
        "forgot_login_success": (
            "Jei Jūsų nurodytas el. pašto adresas yra registruotas mūsų informacinėje sistemoje "
            "ir yra aktyvus, el. paštu gausite patvirtinimo nuorodą"
        ),
        "form_data": {},
    }

    # 5️⃣ Surandame vartotoją pagal email ir statusą active
    email_index = generate_login_index(email)
    result = await session.execute(select(User).where(User.email_index == email_index, User.status == "active"))
    user = result.scalar_one_or_none()

    if not user:
        register_post_attempt(request)
        return {"response_type": "success", "context": response_context}

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

    return {"response_type": "success", "context": response_context}


async def forgot_login_confirm_logic(token: str, session: AsyncSession):
    """
    Atliekame forgot-login confirm logiką.
    Grąžina tuple: (status_code, context)
    """
    # 1️⃣ Token atskyrimas į user_id ir token dalį
    try:
        user_id_str, token_part = token.split(".", 1)
        user_id = int(user_id_str)
    except (ValueError, AttributeError):
        return 404, None

    # 2️⃣ Surandame vartotoją pagal user_id
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or user.status != "active" or not user.reset_confirmation_token_hash:
        return 204, None

    # 3️⃣ Tikriname tokeno atitikimą
    if not verify_confirmation_token(token_part, user.reset_confirmation_token_hash):
        return 204, None

    # 4️⃣ Tikriname tokeno galiojimą
    expires_at = user.reset_confirmation_token_expires
    now_utc = datetime.now(timezone.utc)
    if (
        expires_at is None
        or (expires_at.tzinfo is None and expires_at.replace(tzinfo=timezone.utc) < now_utc)
        or (expires_at.tzinfo is not None and expires_at < now_utc)
    ):
        return 410, None

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
        return 500, None

    # 6️⃣ Siunčiame sėkmės el. laišką
    try:
        email_decrypted = decrypt_data(user.email_encrypted)
        await send_reset_login_success_email(
            email=email_decrypted,
            login_id=login_id
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send reset login success email to user {user.id}")

    # 7️⃣ Grąžiname context į confirm.html
    context = {
        "auto_close": True,
        "countdown": 10,
        "message": "Jūsų prisijungimo duomenys sėkmingai pakeisti. Naujas prisijungimo ID kodas išsiųstas el. paštu.",
    }

    return 200, context
