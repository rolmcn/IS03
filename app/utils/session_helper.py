from contextlib import asynccontextmanager
from app.database import AsyncSessionLocal  # tavo async_sessionmaker

@asynccontextmanager
async def session_context():
    """
    AsyncSession context manager naudojant AsyncSessionLocal.
    Veikia Python 3.14 ir IDE draugiška.
    """
    async with AsyncSessionLocal() as session:
        yield session