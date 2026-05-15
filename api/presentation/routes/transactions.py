from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, status
from api.application.dtos import TransferCommand
from api.application.use_cases import EnqueueTransferUseCase, GetTransactionUseCase
from api.domain.exceptions import TransactionNotFoundError
from api.infra.exporters import MarkdownTransactionExporter, NoopTransactionExporter
from api.infra.queue import InMemoryTransactionQueue, QueueFullError, RedisTransactionQueue
from api.infra.uow import SqlAlchemyUnitOfWork
from api.presentation.dependencies import get_transaction_exporter, get_transaction_queue
from api.presentation.schemas import CreateTransferRequest, EnqueueTransferResponse, TransactionResponse
from sqlalchemy.exc import TimeoutError as SqlAlchemyTimeoutError

router = APIRouter(prefix="/transactions", tags=["transactions"])
IdempotencyKey = Annotated[str, Header(alias="Idempotency-Key", min_length=16, max_length=128)]
TransactionQueueDep = Annotated[
    InMemoryTransactionQueue | RedisTransactionQueue,
    Depends(get_transaction_queue),
]
TransactionExporterDep = Annotated[
    MarkdownTransactionExporter | NoopTransactionExporter,
    Depends(get_transaction_exporter),
]


@router.post(
    "/transfers",
    response_model=EnqueueTransferResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_transfer(
    payload: CreateTransferRequest,
    idempotency_key: IdempotencyKey,
    queue: TransactionQueueDep,
    exporter: TransactionExporterDep,
) -> EnqueueTransferResponse:
    use_case = EnqueueTransferUseCase(SqlAlchemyUnitOfWork, queue, exporter)
    try:
        queued = await use_case.execute(
            TransferCommand(
                source_account_id=payload.source_account_id,
                destination_account_id=payload.destination_account_id,
                amount=payload.amount,
                idempotency_key=idempotency_key,
            )
        )
    except SqlAlchemyTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database connection pool exhausted",
        ) from exc
    except QueueFullError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return EnqueueTransferResponse(
        transaction_id=queued.transaction_id,
        status=queued.status,
        duplicated=queued.duplicated,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: UUID) -> TransactionResponse:
    use_case = GetTransactionUseCase(SqlAlchemyUnitOfWork)
    try:
        transaction = await use_case.execute(transaction_id)
    except TransactionNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return TransactionResponse.model_validate(transaction)
