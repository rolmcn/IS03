from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from eigva_app.models.session import UserSession
from sqlalchemy.exc import SQLAlchemyError
from eigva_app.core.logging.logger import logger

async def logout_user(session: AsyncSession, session_id: str) -> bool:
    """
    Ištrina naudotojo sesiją pagal session_id.
    Grąžina True jei operacija sėkminga, False jei klaida.
    """
    try:
        await session.execute(
            delete(UserSession).where(UserSession.session_id == session_id)
        )
        await session.commit()
        return True
    except SQLAlchemyError:
        logger.exception(f"Failed to delete session {session_id}")
        return False
