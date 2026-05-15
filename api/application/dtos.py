from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
from api.domain.entities import TransactionStatus

@dataclass(frozen=True, slots=True)
class CreateAccountCommand:
    owner_name:str
    initial_balance:Decimal

@dataclass(frozen=True, slots=True)
class TransferCommand:
    source_account_id:UUID
    destination_account_id:UUID
    amount:Decimal
    idempotency_key:str

@dataclass(frozen=True, slots=True)
class QueuedTransaction:
    transaction_id:UUID
    status:TransactionStatus
    duplicated:bool