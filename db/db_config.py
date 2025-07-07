from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from db.models import Base


engine = create_async_engine(
    "sqlite+aiosqlite:///database.db",
    echo=True,
)


sess = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def make_session():
    async with sess() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
