class DomainError(Exception):
    pass

class AccountNotFoundError(DomainError):
    pass

class DuplicatedAccountError(DomainError):
    pass

class InsufficientFundsError(DomainError):
    pass

class InvalidTransactionError(DomainError):
    pass

class TransactionNotFoundError(DomainError):
    pass