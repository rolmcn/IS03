import asyncio
from app.database import engine, Base
from app.models.user import User  # svarbu importuoti visus modelius, kad Base juos „žinotų“

async def main():
    async with engine.begin() as conn:
        # Šis metodas sukurs visas Base žinomas lenteles
        await conn.run_sync(Base.metadata.create_all)
    print("DB lentelės sukurtos!")

if __name__ == "__main__":
    asyncio.run(main())
