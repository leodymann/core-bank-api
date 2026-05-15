import asyncio
from typing import Any
from uuid import UUID

from redis.asyncio import Redis


class QueueFullError(RuntimeError):
    pass


class InMemoryTransactionQueue:
    def __init__(self, max_size: int) -> None:
        self._queue: asyncio.Queue[UUID] = asyncio.Queue(maxsize=max_size)

    async def enqueue(self, transaction_id: UUID) -> None:
        try:
            self._queue.put_nowait(transaction_id)
        except asyncio.QueueFull as exc:
            raise QueueFullError("transaction queue is full") from exc

    async def dequeue(self) -> UUID:
        return await self._queue.get()

    def size(self) -> int:
        return self._queue.qsize()

    async def healthcheck(self) -> None:
        return None


class RedisTransactionQueue:
    def __init__(self, redis: Redis, queue_name: str, max_size: int) -> None:
        self._redis: Any = redis
        self._queue_name = queue_name
        self._max_size = max_size

    async def enqueue(self, transaction_id: UUID) -> None:
        size = await self._redis.llen(self._queue_name)

        if size >= self._max_size:
            raise QueueFullError("transaction queue is full")

        await self._redis.rpush(self._queue_name, str(transaction_id))

    async def dequeue(self) -> UUID:
        item = await self._redis.blpop(self._queue_name, timeout=0)

        if item is None:
            raise RuntimeError("redis queue returned no item")

        return UUID(item[1].decode("utf-8"))

    def size(self) -> int:
        raise RuntimeError("use async_size for redis queues")

    async def async_size(self) -> int:
        return await self._redis.llen(self._queue_name)

    async def healthcheck(self) -> None:
        await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()