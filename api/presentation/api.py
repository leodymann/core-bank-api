from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from api.infra.config import get_settings
from api.infra.database import init_database
from api.infra.factories import create_transaction_exporter, create_transaction_queue
from api.infra.locks import InMemoryAccountLockProvider
from api.infra.queue import RedisTransactionQueue
from api.infra.worker import TransactionWorkerPool
from api.presentation.routes import accounts, health, transactions
from api.presentation.security import InMemoryRateLimitMiddleware, require_api_key


def create_app() -> FastAPI:
    settings = get_settings()

    queue, redis = create_transaction_queue(settings)
    locks = InMemoryAccountLockProvider()
    exporter = create_transaction_exporter(settings)

    workers = TransactionWorkerPool(
        queue=queue,
        locks=locks,
        worker_count=settings.queue_workers,
        exporter=exporter,
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await init_database()

        app.state.transaction_queue = queue
        app.state.account_locks = locks
        app.state.transaction_exporter = exporter

        if settings.embedded_workers_enabled:
            workers.start()

        try:
            yield

        finally:
            await workers.stop()

            if isinstance(queue, RedisTransactionQueue):
                await queue.close()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(InMemoryRateLimitMiddleware)

    app.include_router(health.router)

    app.include_router(
        accounts.router,
        dependencies=[Depends(require_api_key)],
    )

    app.include_router(
        transactions.router,
        dependencies=[Depends(require_api_key)],
    )

    return app