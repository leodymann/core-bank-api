from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi import FastAPI


@pytest.fixture
def database_url() -> str:
    test_dir = Path(".pytest_tmp")
    test_dir.mkdir(exist_ok=True)
    return f"sqlite+aiosqlite:///{(test_dir / f'{uuid4()}.db').resolve().as_posix()}"


@pytest.fixture
def migrated_database(monkeypatch: pytest.MonkeyPatch, database_url: str) -> Iterator[str]:
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("API_KEY", "test-secret")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    monkeypatch.setenv("QUEUE_BACKEND", "memory")
    monkeypatch.setenv("EMBEDDED_WORKERS_ENABLED", "false")
    monkeypatch.setenv("AUTO_CREATE_TABLES", "false")
    monkeypatch.setenv("MARKDOWN_EXPORT_ENABLED", "false")

    from api.infra.config import get_settings

    get_settings.cache_clear()

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    yield database_url

    get_settings.cache_clear()


@pytest_asyncio.fixture
async def app(migrated_database: str) -> AsyncIterator[FastAPI]:
    from api.infra import database
    from api.presentation.api import create_app

    await database.engine.dispose()
    database.engine = database.create_engine(migrated_database)
    database.SessionFactory = database.async_sessionmaker(database.engine, expire_on_commit=False)

    app = create_app()

    async with app.router.lifespan_context(app):
        yield app

    await database.engine.dispose()


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
