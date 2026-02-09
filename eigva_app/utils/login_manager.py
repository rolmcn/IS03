import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from eigva_app.models import User
from eigva_app.utils.login_id import generate_login_id
from eigva_app.utils.blind_index import generate_login_index


async def generate_unique_login(session: AsyncSession) -> tuple[str, str]:
    """
    Sugeneruoja login_id ir login_index kol bus unikalus DB.
    """
    while True:
        login_id = generate_login_id()
        login_index = generate_login_index(login_id)

        result = await session.execute(
            select(User).where(User.login_index == login_index)
        )
        if result.scalar_one_or_none() is None:
            return login_id, login_index
