from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from app.models.transaction import (
    TransactionUpdate,
    TransactionResponse,
    TransactionFilters,
    TransactionListResponse,
)
from app.services.transaction_service import transaction_service

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    date_from: Optional[date] = Query(None, description="Filter transactions on or after this date"),
    date_to: Optional[date] = Query(None, description="Filter transactions on or before this date"),
    amount_min: Optional[int] = Query(None, description="Filter by minimum amount (in cents)"),
    amount_max: Optional[int] = Query(None, description="Filter by maximum amount (in cents)"),
    reviewed: Optional[bool] = Query(None, description="Filter by review status"),
    search: Optional[str] = Query(None, max_length=100, description="Search in description"),
    limit: int = Query(50, ge=1, le=200, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
):
    """List transactions with optional filtering and pagination"""
    filters = TransactionFilters(
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        reviewed=reviewed,
        search=search,
        limit=limit,
        offset=offset,
    )
    return transaction_service.get_list(filters)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(transaction_id: str):
    """Get a single transaction by ID"""
    transaction = transaction_service.get_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(transaction_id: str, data: TransactionUpdate):
    """Update a transaction"""
    # Validate category_id if provided
    if data.category_id is not None:
        from app.services.category_service import category_service
        if not category_service.get_by_id(data.category_id):
            raise HTTPException(status_code=400, detail="Category not found")

    transaction = transaction_service.update(transaction_id, data)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return transaction


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(transaction_id: str):
    """Delete a transaction"""
    success = transaction_service.delete(transaction_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return None
