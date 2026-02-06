from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.utils.mail import send_confirmation_expired_email, send_reset_confirmation_expired_email
from app.utils.crypto import decrypt_data

async def cleanup_expired_tokens(session: AsyncSession):
    """
    Ištrina pasibaigusius registracijos tokenus ir išvalo pasibaigusius slaptažodžio reset tokenus.

    - Registracijos pending vartotojai: ištrinami
    - Reset (slaptažodžio keitimas) tokenai: tik išvalomi, statusas lieka
    """
    now_utc = datetime.now(timezone.utc)

    # 1️⃣ Registracijos pending vartotojai (trinami)
    result = await session.execute(
        select(User).where(
            User.status == "pending",
            User.confirmation_token_expires != None,
            User.confirmation_token_expires < now_utc
        )
    )
    expired_pending_users = result.scalars().all()

    pending_emails = []
    for user in expired_pending_users:
        pending_emails.append(decrypt_data(user.email_encrypted))
        await session.delete(user)

    # 2️⃣ Reset token pasibaigę (netrinami, tik išvalomi)
    result = await session.execute(
        select(User).where(
            User.reset_confirmation_token_expires != None,
            User.reset_confirmation_token_expires < now_utc
        )
    )
    expired_resets = result.scalars().all()

    reset_emails = []
    for user in expired_resets:
        reset_emails.append(decrypt_data(user.email_encrypted))
        user.reset_password_hash = None
        user.reset_confirmation_token_hash = None
        user.reset_confirmation_token_expires = None

    # 3️⃣ Commit pokyčius DB
    await session.commit()

    # 4️⃣ Siunčiame laiškus apie pasibaigusį registracijos tokeną
    for email in pending_emails:
        await send_confirmation_expired_email(email)

    # 5️⃣ Siunčiame laiškus apie pasibaigusį reset tokeną
    for email in reset_emails:
        await send_reset_confirmation_expired_email(email)