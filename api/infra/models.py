from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import DateTime, Enum, Index, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from api.domain.entities import TransactionStatus

class Base(DeclarativeBase):
    pass

class AccountModel(Base):
    __tablename__ = "accounts"

    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_name: Mapped[str]=mapped_column(String(160), nullable=False)
    balance: Mapped[Decimal]=mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class TransactionModel(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_idempotency_key", "idempotency_key", unique=True),
        Index("ix_transactions_status_created_at", "status", "created_at")
    )
    id:Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid4())) 
    source_account_id:Mapped[str]=mapped_column(String(36), nullable=False, index=True)
    destination_account_id:Mapped[str]=mapped_column(String(36), nullable=False, index=True)
    amount:Mapped[Decimal]=mapped_column(Numeric(18,2), nullable=False)
    idempotency_key:Mapped[str]=mapped_column(String(128), nullable=False)
    status:Mapped[TransactionStatus]=mapped_column(Enum(TransactionStatus), nullable=False, default=TransactionStatus.QUEUED)
    failure_reason:Mapped[str|None]=mapped_column(String(500), nullable=True)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at:Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)