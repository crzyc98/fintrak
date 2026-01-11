"""
API endpoints for AI-powered transaction categorization.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.categorization import (
    CategorizationTriggerRequest,
    CategorizationBatchResponse,
    CategorizationBatchListResponse,
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    CategorizationRuleListResponse,
    NormalizationRequest,
    NormalizationResponse,
)
from app.services.categorization_service import categorization_service
from app.services.rule_service import rule_service
from app.services.batch_service import batch_service
from app.services.merchant_normalizer import normalize

router = APIRouter(prefix="/api/categorization", tags=["categorization"])


@router.get("/batches", response_model=CategorizationBatchListResponse)
async def list_batches(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> CategorizationBatchListResponse:
    """
    List categorization batch records.

    Returns batches ordered by start time (newest first).
    """
    return batch_service.get_list(limit, offset)


@router.get("/batches/{batch_id}", response_model=CategorizationBatchResponse)
async def get_batch(batch_id: str) -> CategorizationBatchResponse:
    """Get a specific categorization batch."""
    batch = batch_service.get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return batch


@router.post("/trigger", response_model=CategorizationBatchResponse)
async def trigger_categorization(
    request: Optional[CategorizationTriggerRequest] = None,
) -> CategorizationBatchResponse:
    """
    Trigger AI categorization for uncategorized transactions.

    Applies learned rules first, then sends remaining transactions to AI.
    Returns batch processing results.

    Args:
        request: Optional request body with specific transaction IDs or force_ai flag

    Returns:
        CategorizationBatchResponse with processing results
    """
    return categorization_service.trigger_categorization(request)


# ============================================================================
# Rule Management Endpoints
# ============================================================================


@router.get("/rules", response_model=CategorizationRuleListResponse)
async def list_rules(
    category_id: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> CategorizationRuleListResponse:
    """
    List all categorization rules.

    Returns rules ordered by creation date (newest first).
    """
    return rule_service.get_list(category_id, limit, offset)


@router.post("/rules", response_model=CategorizationRuleResponse, status_code=201)
async def create_rule(
    data: CategorizationRuleCreate,
) -> CategorizationRuleResponse:
    """
    Create a categorization rule manually.

    Rules are typically auto-created when users change transaction categories,
    but this endpoint allows manual rule creation.
    """
    return rule_service.create_rule(data)


@router.get("/rules/{rule_id}", response_model=CategorizationRuleResponse)
async def get_rule(rule_id: str) -> CategorizationRuleResponse:
    """Get a specific categorization rule."""
    rule = rule_service.get_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str) -> None:
    """
    Delete a categorization rule.

    Does not affect already-categorized transactions.
    """
    success = rule_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")


# ============================================================================
# Normalization Endpoints
# ============================================================================


@router.post("/normalize", response_model=NormalizationResponse)
async def preview_normalization(
    request: NormalizationRequest,
) -> NormalizationResponse:
    """
    Preview merchant name normalization.

    Takes a raw transaction description and returns the normalized merchant name
    along with a list of tokens that were removed.
    """
    normalized, tokens_removed = normalize(request.description)
    return NormalizationResponse(
        original=request.description,
        normalized=normalized,
        tokens_removed=tokens_removed,
    )
