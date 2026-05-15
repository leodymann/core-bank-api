import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

class InMemoryAccountLockProvider:
    def __init__(self)->None:
        self._locks:defaultdict[UUID, asyncio.Lock]=defaultdict(asyncio.Lock)

    @asynccontextmanager
    async def lock_pair(self, first: UUID, second: UUID)-> AsyncIterator[None]:
        ordered = sorted((first, second), key=str)
        first_lock = self._locks[ordered[0]]
        second_lock = self._locks[ordered[1]]
        await first_lock.acquire()
        try:
            await second_lock.acquire()
            try:
                yield
            finally:
                second_lock.release()
        finally:
            first_lock.release()