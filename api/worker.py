import asyncio
import contextlib
import signal

from api.infra.config import get_settings
from api.infra.database import init_database
from api.infra.factories import create_transaction_exporter, create_transaction_queue
from api.infra.locks import InMemoryAccountLockProvider
from api.infra.queue import RedisTransactionQueue
from api.infra.worker import TransactionWorkerPool


async def main() -> None:
    settings = get_settings()
    queue, redis = create_transaction_queue(settings)
    if not isinstance(queue, RedisTransactionQueue):
        raise RuntimeError("standalone workers require QUEUE_BACKEND=redis")

    await init_database()
    workers = TransactionWorkerPool(
        queue=queue,
        locks=InMemoryAccountLockProvider(),
        worker_count=settings.queue_workers,
        exporter=create_transaction_exporter(settings),
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop_event.set)

    workers.start()
    try:
        await stop_event.wait()
    finally:
        await workers.stop()
        if redis is not None:
            await queue.close()


if __name__ == "__main__":
    asyncio.run(main())

