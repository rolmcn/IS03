from datetime import datetime, timezone
import secrets
import smtplib
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from eigva_app.models.user import User
from eigva_app.models.payer import Payer
from eigva_app.models.session import UserSession
from eigva_app.models.message import Message, MessageEventType
from eigva_app.schemas.auth_schemas import LoginData, RegistrationData
from eigva_app.core.security.login_manager import generate_unique_login
from eigva_app.core.security.blind_index import generate_login_index
from eigva_app.core.security.crypto import encrypt_data, decrypt_data, hash_password, verify_password
from eigva_app.core.security.recaptcha import verify_recaptcha
from eigva_app.core.rate_limiting.rate_limiter import check_post_limit, register_post_attempt, reset_attempts
from eigva_app.core.security.token import generate_confirmation_token, verify_confirmation_token
from eigva_app.core.communication.mail import send_registration_confirmation_email, send_registration_success_email
from eigva_app.core.logging.logger import logger
from eigva_app.utils.system_messages import SystemMessages


async def authenticate_user(session: AsyncSession, login_id: str, password: str, request):
    # POST limit tikrinimas
    limit_error = check_post_limit(request)
    if limit_error:
        return {"error": limit_error.body.decode()}

    # Pydantic validacija
    try:
        data = LoginData(login_id=login_id, password=password)
    except ValidationError as e:
        msg = e.errors()[0]["msg"].replace("Value error, ", "")
        return {"error": msg}

    # Naudotojo paieška
    login_index = generate_login_index(data.login_id)
    result = await session.execute(select(User).where(User.login_index == login_index))
    user = result.scalar_one_or_none()

    # Slaptažodžio tikrinimas
    if not user or not verify_password(data.password, user.password_hash):
        register_post_attempt(request)
        return {"error": "Neteisingas prisijungimo ID arba slaptažodis"}

    # Statuso tikrinimas
    if user.status != "active":
        register_post_attempt(request)
        return {"error": "Naudotojas neaktyvus"}

    # Sukuriame sesiją
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
        return {"error": "Serverio klaida"}

    # Reset login bandymus
    reset_attempts(request)

    return {"session_id": session_id}


async def register_user(session: AsyncSession, first_name: str, last_name: str, email: str, password: str, recaptcha_response: str):
    # Pydantic validacija
    try:
        data = RegistrationData(first_name=first_name, last_name=last_name, email=email, password=password)
    except ValidationError as e:
        msg = e.errors()[0]["msg"].replace("Value error, ", "")
        return {"error": msg}

    # reCAPTCHA tikrinimas
    if not recaptcha_response or not await verify_recaptcha(recaptcha_response):
        return {"error": "reCAPTCHA patvirtinimas nepavyko"}

    # El. pašto unikalumo tikrinimas
    email_index = generate_login_index(data.email)
    result = await session.execute(select(User).where(User.email_index == email_index))
    if result.scalar_one_or_none():
        return {"error": "Naudotojas su šiuo el. pašto adresu jau egzistuoja"}

    # Generuojame patvirtinimo tokeną
    token_part, token_hash, expires_at = generate_confirmation_token()

    # Sukuriame mokėtoją
    payer = Payer()
    payer.country = "Lietuva"
    session.add(payer)
    await session.flush()  # gauname payer.id (įrašo pakeitimus į DB, bet dar nepadaro commit)

    # Sukuriame naudotoją
    new_user = User(
        payer_id=payer.id,
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

    # Įrašome į DB
    try:
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
    except SQLAlchemyError:
        logger.exception("Failed to create new user")
        return {"error": "Serverio klaida"}

    # Siunčiame patvirtinimo laišką
    try:
        await send_registration_confirmation_email(
            email=data.email,
            user_id=new_user.id,
            token=token_part
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send registration confirmation email to {data.email}")

    return {"success": True}


async def confirm_registration_service(session: AsyncSession, token: str):
    # Token formato patikrinimas
    try:
        user_id_str, token_part = token.split(".", 1)
        user_id = int(user_id_str)
    except (ValueError, AttributeError):
        return {"status": 404}

    # Naudotojo paieška
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        return {"status": 404}

    # Statuso tikrinimas
    if user.status != "pending" or not user.confirmation_token_hash:
        return {"status": 204}

    # Token tikrinimas
    if not verify_confirmation_token(token_part, user.confirmation_token_hash):
        return {"status": 204}

    # Token galiojimo tikrinimas
    expires_at = user.confirmation_token_expires
    now_utc = datetime.now(timezone.utc)
    if expires_at is None or expires_at < now_utc:
        return {"status": 410}

    # Aktyvuojame naudotoją
    try:
        email = decrypt_data(user.email_encrypted)
    except (ValueError, TypeError):
        logger.exception(f"Email decryption failed for user {user.id}")
        return {"status": 500}

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
        return {"status": 500}

    # Sukuriame FIRST_LOGIN sisteminį pranešimą
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

    # Siunčiame sėkmės el. laišką
    try:
        await send_registration_success_email(
            email=email,
            login_id=login_id,
        )
    except (smtplib.SMTPException, ConnectionError, TimeoutError):
        logger.exception(f"Failed to send registration success email to {email}")

    return {"status": 200}
