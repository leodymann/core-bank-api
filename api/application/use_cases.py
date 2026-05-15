from decimal import Decimal
from uuid import UUID
from sqlalchemy.exc import IntegrityError
from api.application.dtos import CreateAccountCommand, QueuedTransaction, TransferCommand
from api.application.ports import AccountLockProvider, TransactionExporter, TransactionQueue, UnitOfWork
from api.domain.entities import Account, Transaction, TransactionStatus
from api.domain.exceptions import AccountNotFoundError, TransactionNotFoundError
from api.domain.services import TransferService
from collections.abc import Callable

class CreateAccountUseCase:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, command: CreateAccountCommand) -> Account:
        account = Account(
            owner_name=command.owner_name.strip(),
            balance=command.initial_balance,
        )

        async with self._uow_factory() as uow:
            await uow.accounts.add(account)
            await uow.commit()

        return account
class GetAccountUseCase:
    def __init__(self, uow_factory: type[UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, account_id: UUID) -> Account:
        async with self._uow_factory() as uow:
            account = await uow.accounts.get(account_id)
        if account is None:
            raise AccountNotFoundError("account not found")
        return account


class EnqueueTransferUseCase:
    def __init__(
        self,
        uow_factory: type[UnitOfWork],
        queue: TransactionQueue,
        exporter: TransactionExporter,
    ) -> None:
        self._uow_factory = uow_factory
        self._queue = queue
        self._exporter = exporter

    async def execute(self, command: TransferCommand) -> QueuedTransaction:
        async with self._uow_factory() as uow:
            transaction = Transaction(
                source_account_id=command.source_account_id,
                destination_account_id=command.destination_account_id,
                amount=command.amount,
                idempotency_key=command.idempotency_key,
            )
            await uow.transactions.add(transaction)
            try:
                await uow.commit()
            except IntegrityError:
                await uow.rollback()
                existing = await uow.transactions.get_by_idempotency_key(command.idempotency_key)
                if existing is not None:
                    await self._exporter.export(existing)
                    return QueuedTransaction(
                        transaction_id=existing.id,
                        status=existing.status,
                        duplicated=True,
                    )
                raise

        await self._queue.enqueue(transaction.id)
        await self._exporter.export(transaction)
        return QueuedTransaction(
            transaction_id=transaction.id,
            status=TransactionStatus.QUEUED,
            duplicated=False,
        )


class GetTransactionUseCase:
    def __init__(self, uow_factory: type[UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    async def execute(self, transaction_id: UUID) -> Transaction:
        async with self._uow_factory() as uow:
            transaction = await uow.transactions.get(transaction_id)
        if transaction is None:
            raise TransactionNotFoundError("transaction not found")
        return transaction


class ProcessTransferUseCase:
    def __init__(
        self,
        uow_factory: type[UnitOfWork],
        locks: AccountLockProvider,
        exporter: TransactionExporter,
    ) -> None:
        self._uow_factory = uow_factory
        self._locks = locks
        self._exporter = exporter

    async def execute(self, transaction_id: UUID) -> None:
        async with self._uow_factory() as uow:
            transaction = await uow.transactions.get(transaction_id)
            if transaction is None:
                raise TransactionNotFoundError("transaction not found")
            if transaction.status is TransactionStatus.SUCCEEDED:
                return
            transaction.status = TransactionStatus.PROCESSING
            await uow.transactions.save(transaction)
            await uow.commit()
            await self._exporter.export(transaction)

        async with self._uow_factory() as uow:
            transaction = await uow.transactions.get(transaction_id)
            if transaction is None:
                raise TransactionNotFoundError("transaction not found")

            async with self._locks.lock_pair(
                transaction.source_account_id,
                transaction.destination_account_id,
            ):
                source = await uow.accounts.get_for_update(transaction.source_account_id)
                destination = await uow.accounts.get_for_update(transaction.destination_account_id)
                if source is None or destination is None:
                    transaction.status = TransactionStatus.FAILED
                    transaction.failure_reason = "account not found"
                else:
                    try:
                        TransferService.apply(source, destination, Decimal(transaction.amount))
                    except Exception as exc:
                        transaction.status = TransactionStatus.FAILED
                        transaction.failure_reason = str(exc)
                    else:
                        transaction.status = TransactionStatus.SUCCEEDED
                        transaction.failure_reason = None
                        await uow.accounts.save(source)
                        await uow.accounts.save(destination)

                await uow.transactions.save(transaction)
                await uow.commit()
                await self._exporter.export(transaction)
