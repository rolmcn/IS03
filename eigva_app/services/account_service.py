from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from eigva_app.models.message import Message
from eigva_app.core.logging.logger import logger

async def get_user_messages(session: AsyncSession, user_id: int, limit: int = 50):
    try:
        result = await session.execute(
            select(Message)
            .where(Message.user_id == user_id)
            .order_by(
                Message.msg_read.asc(),
                Message.msg_created_at.desc()
            )
            .limit(limit)
        )
        return result.scalars().all()
    except SQLAlchemyError as e:
        logger.exception(f"Failed to load messages for user {user_id}: {e}")
        return []

async def mark_message_read(session: AsyncSession, user_id: int, msg_id: int):
    try:
        result = await session.execute(
            select(Message).where(
                Message.id == msg_id,
                Message.user_id == user_id
            )
        )
        message = result.scalar_one_or_none()
        if not message:
            return None

        if not message.msg_read:
            message.msg_read = datetime.now(timezone.utc)
            await session.commit()

        return message
    except Exception as e:
        logger.exception(f"Failed to mark message {msg_id} as read for user {user_id}: {e}")
        raise
