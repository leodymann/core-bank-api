from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from api.application.dtos import CreateAccountCommand
from api.application.use_cases import CreateAccountUseCase, GetAccountUseCase
from api.domain.exceptions import AccountNotFoundError
from api.infra.uow import SqlAlchemyUnitOfWork
from api.presentation.schemas import AccountResponse, CreateAccountRequest

router=APIRouter(prefix="/accounts", tags=["accounts"])

@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(payload: CreateAccountRequest)->AccountResponse:
    use_case = CreateAccountUseCase(SqlAlchemyUnitOfWork)
    account = await use_case.execute(
        CreateAccountCommand(
            owner_name=payload.owner_name,
            initial_balance=payload.initial_balance,
        )
    )
    return AccountResponse.model_validate(account)

@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id:UUID)->AccountResponse:
    use_case=GetAccountUseCase(SqlAlchemyUnitOfWork)
    try:
        account=await use_case.execute(account_id)
    except AccountNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AccountResponse.model_validate(account)