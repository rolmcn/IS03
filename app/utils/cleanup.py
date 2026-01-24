from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.users import Users
from app.utils.mail import send_confirmation_expired_email
from app.utils.crypto import decrypt_data

async def cleanup_expired_pending_users(session: AsyncSession):
    """Ištrina pending vartotojus, kurių tokenai pasibaigę, ir siunčia laiškus."""
    now_utc = datetime.now(timezone.utc)

    # 1️⃣ Surandame visus pasibaigusius pending vartotojus
    result = await session.execute(
        select(Users).where(
            Users.status == "pending",
            Users.confirmation_token_expires != None,
            Users.confirmation_token_expires < now_utc
        )
    )
    expired_users = result.scalars().all()

    # 2️⃣ Išsaugome el. paštus laiškams prieš trynimą
    emails = []
    for user in expired_users:
        emails.append(decrypt_data(user.email_encrypted))
        await session.delete(user)

    # 3️⃣ Commit - dabar vartotojai DB jau ištrinti
    await session.commit()

    # 4️⃣ Siunčiame laiškus apie pasibaigusį tokeną
    for email in emails:
        await send_confirmation_expired_email(email)
