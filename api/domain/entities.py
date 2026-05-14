from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

class TransactionStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

@dataclass(init=False, slots=True)
class Account:
    owner_name: str
    balance: Decimal
    id: UUID
    created_at: datetime

    def __init__(
            self,
            owner_name: str,
            balance: Decimal,
            id: UUID | None = None,
            created_at: datetime | None = None,
    )->None:
        self.id = id or uuid4()
        self.owner_name = owner_name
        self.balance = balance
        self.created_at = created_at or datetime.now(UTC)

@dataclass(init=False, slots=True)
class Transaction:
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal
    idempotency_key: str
    id: UUID
    status: TransactionStatus = TransactionStatus.QUEUED
    failure_reason: str | None = None
    created_at: datetime
    updated_at: datetime

    def __init__(
            self,
            source_account_id: UUID,
            destination_account_id: UUID,
            amount: Decimal,
            idempotency_key: str,
            id: UUID | None = None,
            status: TransactionStatus = TransactionStatus.QUEUED,
            failure_reason: str | None = None,
            created_at: datetime | None = None,
            updated_at: datetime | None = None,
    )->None:
        now = datetime.now(UTC)
        self.id = id or uuid4()
        self.source_account_id = source_account_id
        self.destination_account_id = destination_account_id
        self.amount = amount
        self.idempotency_key = idempotency_key
        self.status = status
        self.failure_reason = failure_reason
        self.created_at = created_at or now
        self.updated_at = updated_at or now