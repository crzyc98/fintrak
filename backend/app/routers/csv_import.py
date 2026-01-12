from fastapi import APIRouter, HTTPException

from app.models.csv_import import (
    CsvPreviewRequest,
    CsvPreviewResponse,
    CsvParseRequest,
    CsvParseResponse,
    BulkTransactionCreateRequest,
    BulkTransactionCreateResponse,
)
from app.services.csv_import_service import csv_import_service
from app.services.account_service import account_service

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
