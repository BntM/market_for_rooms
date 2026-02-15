from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.config import settings

_is_sqlite = "sqlite" in settings.DATABASE_URL

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    # SQLite needs single-connection pool + relaxed thread check for async
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    poolclass=StaticPool if _is_sqlite else None,
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Seed default agents if none exist
    await seed_default_agents()


async def seed_default_agents():
    from sqlalchemy import select, func
    from app.models import Agent, AdminConfig

    async with async_session() as db:
        count = await db.scalar(select(func.count()).select_from(Agent))
        if count and count > 0:
            return
        config = await db.scalar(select(AdminConfig))
        balance = config.token_starting_amount if config else 100.0
        for i in range(1, 7):
            db.add(Agent(name=f"User_{i}", token_balance=balance, max_bookings=10))
        await db.commit()
