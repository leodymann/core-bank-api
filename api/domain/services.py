from decimal import Decimal
from api.domain.entities import Account
from api.domain.exceptions import InsufficientFundsError, InvalidTransactionError

class TransferService:
    @staticmethod
    def validate(source: Account, destination: Account, amount: Decimal)->None:
        if source.id == destination.id:
            raise InvalidTransactionError("source and destination accounts must be different")
        if amount <= Decimal("0"):
            raise InvalidTransactionError("amount must be greater than zero")
        if source.balance < amount:
            raise InsufficientFundsError("insufficient funds")
        
    @staticmethod
    def apply(source: Account, destination: Account, amount: Decimal)->None:
        TransferService.validate(source, destination, amount)
        source.balance -= amount
        destination.balance += amount