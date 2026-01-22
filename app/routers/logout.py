from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from app.database import get_async_session
from app.models.sessions import UserSession

router = APIRouter()


@router.get("/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    session_id = request.cookies.get("session_id")

    if session_id:
        await session.execute(
            delete(UserSession).where(UserSession.session_id == session_id)
        )
        await session.commit()

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )

    response.delete_cookie("session_id")

    return response
