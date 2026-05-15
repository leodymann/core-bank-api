from typing import Annotated
from fastapi import APIRouter, Depends
from api.infra.config import Settings, get_settings
from api.infra.database import check_database, pool_status
from api.infra.queue import InMemoryTransactionQueue, RedisTransactionQueue
from api.presentation.dependencies import get_transaction_queue

router=APIRouter(tags=["health"])
SettingsDep=Annotated[Settings, Depends(get_settings)]
QueueDep=Annotated[
    InMemoryTransactionQueue | RedisTransactionQueue,
    Depends(get_transaction_queue),
]

@router.get("/health")
async def health(settings: SettingsDep)->dict[str, str]:
    return {"status": "ok", "environment": settings.environment}

@router.get("/ready")
async def ready(settings: SettingsDep, queue: QueueDep)->dict[str, str]:
    await check_database()
    await queue.healthcheck()
    return{
        "status": "ready",
        "environment": settings.environment,
        "queue_backend": settings.queue_backend,
    }

@router.get("/metrics")
async def metrics(settings: SettingsDep, queue: QueueDep)->dict[str, int | str]:
    queue_size=(
        await queue.async_size()
        if isinstance(queue, RedisTransactionQueue)
        else queue.size()
    )
    return{
        "transaction_queue_size": queue_size,
        "queue_backend": settings.queue_backend,
        "database_pool": pool_status(),
    }