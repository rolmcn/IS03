from datetime import datetime, timezone

from typing_extensions import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import logging

from eigva_app.config import templates
from eigva_app.models.user import User
from eigva_app.models.message import Message
from eigva_app.utils.auth import get_async_session, get_current_user

router = APIRouter()
logger = logging.getLogger("account")

CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/account", response_class=HTMLResponse)
async def account_page(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    if not current_user:
        return RedirectResponse("/login", status_code=303)

    try:
        # Rikiavimas: neskaityti viršuje, skaityti žemiau,
        # kiekvienos grupės viduje nuo naujausio iki seniausio
        result = await session.execute(
            select(Message)
            .where(Message.user_id == current_user.id)
            .order_by(
                Message.msg_read.asc(),          # unread pirmiau
                Message.msg_created_at.desc()    # naujausi viršuje
            )
            .limit(50)
        )
        messages = result.scalars().all()

    except SQLAlchemyError as e:
        logger.exception(f"Failed to load messages for user {current_user.id}: {e}")
        return templates.TemplateResponse(
            "account.html",
            {
                "request": request,
                "current_user": current_user,
                "active_page": "account",
                "environment": "auto",
                "messages": [],
                "error_message": "Nepavyko įkelti pranešimų.",
            },
        )

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
async def mark_message_read(
    msg_id: int,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_async_session),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        # Gauname žinutę pagal msg_id ir user_id
        result = await session.execute(
            select(Message).where(
                Message.id == msg_id,
                Message.user_id == current_user.id
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(status_code=404, detail="Message not found")

        # Jei dar neskaityta, pažymime UTC datetime
        if not message.msg_read:
            message.msg_read = datetime.now(timezone.utc)
            await session.commit()

        # Konvertuojame datetime į ISO string
        return JSONResponse({
            "status": "ok",
            "msg_read": message.msg_read.isoformat() if message.msg_read else None
        })

    except Exception as e:
        # Debug variantas: logina tikslų error ir grąžina naršyklei / Postman
        logger.exception(f"Failed to mark message {msg_id} as read: {e}")
        raise HTTPException(status_code=500, detail=str(e))
