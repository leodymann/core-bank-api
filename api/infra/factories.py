from redis.asyncio import Redis
from api.infra.config import Settings
from api.infra.exporters import MarkdownTransactionExporter, NoopTransactionExporter
from api.infra.queue import InMemoryTransactionQueue, RedisTransactionQueue

def create_transaction_queue(
        settings: Settings,
) -> tuple[InMemoryTransactionQueue | RedisTransactionQueue, Redis | None]:
    if settings.queue_backend == "redis":
        redis = Redis.from_url(settings.redis_url)
        return(
            RedisTransactionQueue(
                redis=redis,
                queue_name=settings.redis_transaction_queue_name,
                max_size=settings.queue_max_size,
            ),
            redis,
        )
    return InMemoryTransactionQueue(max_size=settings.queue_max_size),None

def create_transaction_exporter(
        settings: Settings,
)-> MarkdownTransactionExporter | NoopTransactionExporter:
    if settings.markdown_export_enabled:
        return MarkdownTransactionExporter(settings.markdown_export_dir)
    return NoopTransactionExporter()