from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from api.domain.entities import TransactionStatus

class CreateAccountRequest(BaseModel):
    owner_name:str=Field(min_length=2, max_length=160)
    initial_balance:Decimal=Field(ge=Decimal("0"), decimal_places=2)

class AccountResponse(BaseModel):
    id:UUID
    owner_name:str
    balance:Decimal
    created_at:datetime
    model_config= ConfigDict(from_attributes=True)

class CreateTransferRequest(BaseModel):
    source_account_id:UUID
    destination_account_id:UUID
    amount:Decimal=Field(gt=Decimal("0"), decimal_places=2)

class EnqueueTransferResponse(BaseModel):
    transaction_id:UUID
    status: TransactionStatus
    duplicated:bool

class TransactionResponse(BaseModel):
    id:UUID
    source_account_id:UUID
    destination_account_id:UUID
    amount:Decimal
    idempotency_key:str
    status:TransactionStatus
    failure_reason:str|None
    created_at:datetime
    updated_at:datetime
    model_config=ConfigDict(from_attributes=True)