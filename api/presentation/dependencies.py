from fastapi import Request
from api.infra.exporters import MarkdownTransactionExporter, NoopTransactionExporter
from api.infra.queue import InMemoryTransactionQueue, RedisTransactionQueue

def get_transaction_queue(request:Request)->InMemoryTransactionQueue|RedisTransactionQueue:
    return request.app.state.transaction_queue

def get_transaction_exporter(
        request: Request,
)->MarkdownTransactionExporter|NoopTransactionExporter:
    return request.app.state.transaction_exporter