from sqlalchemy.ext.asyncio import AsyncSession

from api.infra import database
from api.infra.repositories import (
    SqlAlchemyAccountRepository,
    SqlAlchemyTransactionRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self) -> None:
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = database.SessionFactory()
        self.accounts = SqlAlchemyAccountRepository(self._session)
        self.transactions = SqlAlchemyTransactionRepository(self._session)
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        if self._session is None:
            return
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work is not active")
        await self._session.commit()

    async def rollback(self) -> None:
        if self._session is None:
            raise RuntimeError("unit of work is not active")
        await self._session.rollback()
