from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_creates_current_schema(database_url: str, monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", database_url)

    command.upgrade(Config("alembic.ini"), "head")

    sync_database_url = database_url.replace("sqlite+aiosqlite:///", "sqlite:///")
    engine = create_engine(sync_database_url)
    try:
        with engine.connect() as connection:
            tables = set(inspect(connection).get_table_names())
    finally:
        engine.dispose()

    assert {"accounts", "transactions", "alembic_version"}.issubset(tables)
