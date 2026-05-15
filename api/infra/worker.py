import asyncio
import contextlib
import logging
from api.application.use_cases import ProcessTransferUseCase
from api.infra.exporters import MarkdownTransactionExporter, NoopTransactionExporter
from api.infra.locks import InMemoryAccountLockProvider
from api.infra.queue import InMemoryTransactionQueue, RedisTransactionQueue
from api.infra.uow import SqlAlchemyUnitOfWork

logger = logging.getLogger(__name__)


class TransactionWorkerPool:
    def __init__(
        self,
        queue: InMemoryTransactionQueue | RedisTransactionQueue,
        locks: InMemoryAccountLockProvider,
        worker_count: int,
        exporter: MarkdownTransactionExporter | NoopTransactionExporter,
    ) -> None:
        self._queue = queue
        self._locks = locks
        self._worker_count = worker_count
        self._exporter = exporter
        self._tasks: list[asyncio.Task[None]] = []

    def start(self) -> None:
        if self._tasks:
            return
        for worker_number in range(self._worker_count):
            task = asyncio.create_task(
                self._run(worker_number),
                name=f"transaction-worker-{worker_number}",
            )
            self._tasks.append(task)

    async def stop(self) -> None:
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _run(self, worker_number: int) -> None:
        use_case = ProcessTransferUseCase(SqlAlchemyUnitOfWork, self._locks, self._exporter)
        logger.info("transaction worker %s started", worker_number)
        while True:
            transaction_id = await self._queue.dequeue()
            try:
                await use_case.execute(transaction_id)
            except Exception:
                logger.exception("transaction worker failed to process %s", transaction_id)
