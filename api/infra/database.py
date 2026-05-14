from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from api.infra.config import get_settings
from api.infra.models import Base
