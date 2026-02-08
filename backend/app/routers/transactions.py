from typing import Optional
from datetime import date
from fastapi import APIRouter, HTTPException, Query

from app.models.transaction import (
    TransactionUpdate,
    TransactionResponse,
    TransactionFilters,
    TransactionListResponse,
    MonthlySpendingResponse,
)
from app.models.review import (
    BulkOperationRequest,
    BulkOperationType,
    BulkOperationResponse,
    ReviewQueueResponse,
    ReviewQueueCountResponse,
)
from app.services.transaction_service import transaction_service
from app.services.review_service import review_service
from app.services.spending_service import spending_service

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


# Review workflow endpoints - must be before /{transaction_id} routes

@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    limit: int = Query(50, ge=1, le=200, description="Maximum transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
):
    """
    Get unreviewed transactions grouped by day.

    Returns transactions where reviewed=false, ordered by date descending,
    with date labels (Today, Yesterday, or formatted date).
    """
    return review_service.get_review_queue(limit, offset)


@router.get("/review-queue/count", response_model=ReviewQueueCountResponse)
async def get_review_queue_count():
    """Get count of unreviewed transactions without fetching full data"""
    count = transaction_service.count(TransactionFilters(reviewed=False))
    return ReviewQueueCountResponse(count=count)


@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_update_transactions(request: BulkOperationRequest):
    """
    Perform bulk operations on multiple transactions atomically.

    All operations succeed or all fail (no partial updates).

    Supported operations:
    - mark_reviewed: Sets reviewed=true and reviewed_at=now
    - set_category: Updates category_id and sets categorization_source='manual'
    - add_note: Appends note text to existing notes (with newline separator)
    """
    try:
        if request.operation == BulkOperationType.MARK_REVIEWED:
            return review_service.bulk_mark_reviewed(request.transaction_ids)
        elif request.operation == BulkOperationType.SET_CATEGORY:
            return review_service.bulk_set_category(
                request.transaction_ids, request.category_id  # type: ignore
            )
        elif request.operation == BulkOperationType.ADD_NOTE:
            return review_service.bulk_add_note(
                request.transaction_ids, request.note  # type: ignore
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/spending/monthly", response_model=MonthlySpendingResponse)
async def get_monthly_spending():
    """
    Get monthly spending data for the dashboard.

    Returns cumulative daily spending for the current month,
    comparison to last month, and a linear pace line.
    """
    return spending_service.get_monthly_spending()


# Single transaction routes - must be after specific path routes

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
