from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from api.infra.config import get_settings
from api.infra.models import Base

from api.infra.config import get_settings
from api.infra.models import Base

def create_engine(database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or settings.database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    pool_options = {}
    if not url.startswith("sqlite"):
        pool_options = {
            "pool_size": settings.database_pool_size,
            "max_overflow": settings.database_max_overflow,
            "pool_timeout": settings.database_pool_timeout,
        }
    db_engine = create_async_engine(
        url,
        pool_pre_ping=True,
        connect_args=connect_args,
        **pool_options,
    )
    if url.startswith("sqlite"):
        _configure_sqlite(db_engine)
    return db_engine


def _configure_sqlite(db_engine: AsyncEngine) -> None:
    @event.listens_for(db_engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        cursor.close()


engine = create_engine()
SessionFactory = async_sessionmaker(engine, expire_on_commit=False)


def pool_status() -> str:
    return engine.sync_engine.pool.status()


async def init_database(db_engine: AsyncEngine | None = None) -> None:
    db_engine = db_engine or engine
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_database() -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
