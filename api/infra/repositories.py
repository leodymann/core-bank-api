from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.domain.entities import Account, Transaction, TransactionStatus
from api.infra.models import AccountModel, TransactionModel

def account_to_domain(model: AccountModel)->Account:
    return Account(
        id=UUID(model.id),
        owner_name=model.owner_name,
        balance=model.balance,
        created_at=model.created_at,
    )

def transaction_to_domain(model: TransactionModel)-> Transaction:
    return Transaction(
        id=UUID(model.id),
        source_account_id=UUID(model.source_account_id),
        destination_account_id=UUID(model.destination_account_id),
        amount=model.amount,
        idempotency_key=model.idempotency_key,
        status=model.status,
        failure_reason=model.failure_reason,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

class SqlAlchemyAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, account: Account)->None:
        self._session.add(
            AccountModel(
                id=str(account.id),
                owner_name=account.owner_name,
                balance=account.balance,
                created_at=account.created_at,
            )
        )
    
    async def get(self, account_id: UUID)-> Account | None:
        model = await self._session.get(AccountModel, str(account_id))
        return account_to_domain(model) if model else None
    
    async def get_for_update(self, account_id: UUID)-> Account | None:
        result = await self._session.execute(
            select(AccountModel)
            .where(AccountModel.id == str(account_id))
            .with_for_update()
        )
        model = result.scalar_one_or_none()
        return account_to_domain(model) if model else None
    
    async def save(self, account: Account)-> None:
        model = await self._session.get(AccountModel, str(account.id))
        if model is None:
            await self.add(account)
            return
        model.owner_name=account.owner_name
        model.balance=account.balance

class SqlAlchemyTransactionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session=session

    async def add(self, transaction: Transaction)->None:
        self._session.add(
            TransactionModel(
                id=str(transaction.id),
                source_account_id=str(transaction.source_account_id),
                destination_account_id=str(transaction.destination_account_id),
                amount=transaction.amount,
                idempotency_key=transaction.idempotency_key,
                status=transaction.status,
                failure_reason=transaction.failure_reason,
                created_at=transaction.created_at,
                updated_at=transaction.updated_at,
            )
        )
    
    async def get(self, transaction_id: UUID)-> Transaction | None:
        model = await self._session.get(TransactionModel, str(transaction_id))
        return transaction_to_domain(model) if model else None
    
    async def get_by_idempotency_key(self, idempotency_key: str)-> Transaction | None:
        result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.idempotency_key == idempotency_key)
        )
        model = result.scalar_one_or_none()
        return transaction_to_domain(model) if model else None
    
    async def save(self, transaction: Transaction)-> None:
        model = await self._session.get(TransactionModel, str(transaction.id))
        if model is None:
            await self.add(transaction)
            return
        model.status=transaction.status
        model.failure_reason=transaction.failure_reason
        model.amount=transaction.amount

    async def list_by_status(self, status: TransactionStatus, limit: int)-> list[Transaction]:
        result = await self._session.execute(
            select(TransactionModel)
            .where(TransactionModel.status == status)
            .order_by(TransactionModel.created_at)
            .limit(limit)
        )
        return [transaction_to_domain(model) for model in result.scalars()]