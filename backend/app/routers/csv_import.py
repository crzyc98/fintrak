from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.csv_import import (
    CsvPreviewRequest,
    CsvPreviewResponse,
    CsvParseRequest,
    CsvParseResponse,
    BulkTransactionCreateRequest,
    BulkTransactionCreateResponse,
)
from app.models.category_mapping import (
    CategoryMappingSuggestRequest,
    CategoryMappingSuggestResponse,
    CategoryMappingSaveRequest,
    CategoryMappingSaveResponse,
    CategoryMappingListResponse,
    TransactionCategorizationRequest,
    TransactionCategorizationResponse,
    TransactionCategorySuggestion,
)
from app.services.csv_import_service import csv_import_service
from app.services.account_service import account_service
from app.services.category_mapping_service import category_mapping_service

router = APIRouter(prefix="/api/import", tags=["csv-import"])


@router.post("/preview", response_model=CsvPreviewResponse)
async def preview_csv(request: CsvPreviewRequest) -> CsvPreviewResponse:
    try:
        return csv_import_service.preview_csv(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/parse", response_model=CsvParseResponse)
async def parse_csv(request: CsvParseRequest) -> CsvParseResponse:
    # Verify account exists
    account = account_service.get_by_id(request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        return csv_import_service.parse_csv(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/transactions", response_model=BulkTransactionCreateResponse, status_code=201)
async def create_transactions(request: BulkTransactionCreateRequest) -> BulkTransactionCreateResponse:
    # Verify account exists
    account = account_service.get_by_id(request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    try:
        return csv_import_service.create_transactions(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/suggest-mappings", response_model=CategoryMappingSuggestResponse)
async def suggest_category_mappings(
    request: CategoryMappingSuggestRequest,
) -> CategoryMappingSuggestResponse:
    """Get AI-suggested mappings for unmatched source categories."""
    # Verify account exists
    account = account_service.get_by_id(request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not request.source_categories:
        return CategoryMappingSuggestResponse(suggestions=[])

    suggestions = category_mapping_service.suggest_mappings_with_ai(
        request.account_id,
        request.source_categories,
    )

    return CategoryMappingSuggestResponse(suggestions=suggestions)


@router.post("/mappings", response_model=CategoryMappingSaveResponse, status_code=201)
async def save_category_mappings(
    request: CategoryMappingSaveRequest,
) -> CategoryMappingSaveResponse:
    """Save user-confirmed category mappings."""
    # Verify account exists
    account = account_service.get_by_id(request.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if not request.mappings:
        return CategoryMappingSaveResponse(saved_count=0)

    mappings = [
        (m.source_category, m.target_category_id)
        for m in request.mappings
    ]

    saved_count = category_mapping_service.save_mappings(
        request.account_id,
        mappings,
        source="user",
    )

    return CategoryMappingSaveResponse(saved_count=saved_count)


@router.get("/mappings", response_model=CategoryMappingListResponse)
async def list_category_mappings(
    account_id: Optional[str] = Query(None, description="Account ID to filter mappings"),
) -> CategoryMappingListResponse:
    """List saved category mappings for an account."""
    if account_id:
        # Verify account exists
        account = account_service.get_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

    mappings = category_mapping_service.get_mappings_for_account(account_id)

    return CategoryMappingListResponse(
        mappings=mappings,
        total=len(mappings),
    )


@router.post("/categorize-transactions", response_model=TransactionCategorizationResponse)
async def categorize_transactions(
    request: TransactionCategorizationRequest,
) -> TransactionCategorizationResponse:
    """Use AI to categorize parsed transactions by their descriptions."""
    if not request.transactions:
        return TransactionCategorizationResponse(suggestions=[])

    # Convert to format expected by service
    transactions = [
        {
            "row_number": t.row_number,
            "description": t.description,
            "amount": t.amount,
        }
        for t in request.transactions
    ]

    # Get AI suggestions
    results = category_mapping_service.categorize_transactions_with_ai(transactions)

    # Convert to response format
    suggestions = [
        TransactionCategorySuggestion(
            row_number=row_number,
            category_id=data["category_id"],
            category_name=data["category_name"],
            category_emoji=data.get("category_emoji"),
            confidence=data["confidence"],
        )
        for row_number, data in results.items()
    ]

    return TransactionCategorizationResponse(suggestions=suggestions)
