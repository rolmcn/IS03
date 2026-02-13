from typing_extensions import Annotated
from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from eigva_app.config import templates
from eigva_app.models.user import User
from eigva_app.core.security.auth import get_async_session, get_current_user
from eigva_app.services.account_service import get_user_messages, mark_message_read

router = APIRouter()
CurrentUser = Annotated[User, Depends(get_current_user)]

@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    messages = await get_user_messages(session, current_user.id)

    return templates.TemplateResponse(
        "account.html",
        {
            "request": request,
            "current_user": current_user,
            "active_page": "account",
            "environment": "auto",
            "messages": messages,
        },
    )

@router.post("/account/mark_read/{msg_id}")
async def mark_message_read_route(
    msg_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    message = await mark_message_read(session, current_user.id, msg_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    return JSONResponse({
        "status": "ok",
        "msg_read": message.msg_read.isoformat() if message.msg_read else None
    })
