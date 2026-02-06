from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.database import get_async_session
from app.models.session import UserSession
from app.models.user import User


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> User:
    """
    Grąžina prisijungusį vartotoją pagal session_id cookie.
    Jei sesija negalioja – grąžina 401.
    """

    # 1. Paimame session_id iš cookie
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    # 2. Išvalome pasibaigusias sesijas (soft cleanup)
    await cleanup_expired_sessions(session)

    # 3. Ieškome aktyvios sesijos
    result = await session.execute(
        select(UserSession).where(
            UserSession.session_id == session_id,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )
    user_session = result.scalar_one_or_none()
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid",
        )

    # 4. Gauname vartotoją
    user = await session.get(User, user_session.user_id)
    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User inactive or not found",
        )

    return user


async def cleanup_expired_sessions(session: AsyncSession) -> None:
    """
    Pašalina visas pasibaigusias sesijas iš DB.
    """
    await session.execute(
        delete(UserSession).where(
            UserSession.expires_at < datetime.now(timezone.utc)
        )
    )
    await session.commit()
