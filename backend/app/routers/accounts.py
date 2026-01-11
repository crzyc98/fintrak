from fastapi import APIRouter, HTTPException

from app.models.account import AccountCreate, AccountUpdate, AccountResponse
from app.services.account_service import account_service

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
async def get_accounts():
    return account_service.get_all()


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(data: AccountCreate):
    return account_service.create(data)


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: str):
    account = account_service.get_by_id(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(account_id: str, data: AccountUpdate):
    account = account_service.update(account_id, data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: str):
    success, error = account_service.delete(account_id)
    if not success:
        if error == "Account not found":
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=400, detail=error)
