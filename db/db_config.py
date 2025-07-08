from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from db.models import Base
import os


async def make_engine():
    return create_async_engine(
        os.getenv("DATABASE_URL"),
        echo=True,
    )


async def make_session():
    engine = await make_engine()
    sess = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with sess() as session:
        yield session


async def init_db():
    engine = await make_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
