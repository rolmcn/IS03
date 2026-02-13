from fastapi import APIRouter, Request, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from eigva_app.database import get_async_session
from eigva_app.services.logout_service import logout_user

router = APIRouter()

@router.get("/logout")
async def logout(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    session_id = request.cookies.get("session_id")

    if session_id:
        await logout_user(session, session_id)

    response = RedirectResponse(
        url="/login",
        status_code=303,
    )
    response.delete_cookie("session_id")

    return response
