"""
API endpoints for AI-powered transaction categorization.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, model_validator

from app.models.categorization import (
    CategorizationTriggerRequest,
    CategorizationBatchResponse,
    CategorizationBatchListResponse,
    CategorizationRuleCreate,
    CategorizationRuleResponse,
    CategorizationRuleListResponse,
    DescriptionPatternRuleCreate,
    PatternPreviewRequest,
    PatternPreviewResponse,
    NormalizationRequest,
    NormalizationResponse,
    BatchTriggerResponse,
    UnclassifiedCountResponse,
    BatchProgressResponse,
)
from app.services.categorization_service import categorization_service
from app.services.rule_service import rule_service
from app.services.batch_service import batch_service
from app.services.merchant_normalizer import normalize
from app.services.desc_rule_service import desc_rule_service
from app.services.pattern_extractor import extract_pattern

router = APIRouter(prefix="/api/categorization", tags=["categorization"])


class RuleCreateRequest(BaseModel):
    merchant_pattern: Optional[str] = None
    category_id: str
    description_pattern: Optional[str] = None
    account_id: Optional[str] = None

    @model_validator(mode='after')
    def check_mutual_exclusivity(self):
        has_merchant = self.merchant_pattern is not None
        has_desc = self.description_pattern is not None
        if has_merchant and has_desc:
            raise ValueError("Cannot provide both merchant_pattern and description_pattern")
        if not has_merchant and not has_desc:
            raise ValueError("Must provide either merchant_pattern or description_pattern")
        if has_desc and not self.account_id:
            raise ValueError("account_id is required for description pattern rules")
        return self


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


@router.get("/unclassified-count", response_model=UnclassifiedCountResponse)
async def get_unclassified_count() -> UnclassifiedCountResponse:
    """Get count of transactions needing classification."""
    count = categorization_service.get_unclassified_count()
    return UnclassifiedCountResponse(count=count)


@router.get("/batches/{batch_id}/progress", response_model=BatchProgressResponse)
async def get_batch_progress(batch_id: str) -> BatchProgressResponse:
    """Get real-time progress of a batch classification job."""
    progress = categorization_service.get_batch_progress(batch_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Batch not found or no progress tracked")
    return progress


@router.post("/trigger")
async def trigger_categorization(
    request: Optional[CategorizationTriggerRequest] = None,
):
    """
    Trigger AI categorization for uncategorized transactions.

    When called with transaction_ids (from review page / CSV import), runs
    synchronously and returns CategorizationBatchResponse.

    When called without transaction_ids (batch classify from Settings),
    starts background processing and returns BatchTriggerResponse with HTTP 202.
    Returns HTTP 409 if a batch job is already running.
    """
    # If specific transaction_ids are given, use synchronous path (existing behavior)
    if request and request.transaction_ids:
        return categorization_service.trigger_categorization(request)

    # Batch classify path — background processing
    try:
        result = categorization_service.trigger_batch_classification(request)
    except RuntimeError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    status_code = 202 if result["status"] == "running" else 200
    return JSONResponse(
        content=result,
        status_code=status_code,
    )


# ============================================================================
# Rule Management Endpoints
# ============================================================================


@router.get("/rules", response_model=CategorizationRuleListResponse)
async def list_rules(
    category_id: Optional[str] = Query(None, description="Filter by category"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type: merchant or description"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> CategorizationRuleListResponse:
    """
    List all categorization rules.

    Returns rules ordered by creation date (newest first).
    Supports filtering by rule_type: 'merchant' or 'description'.
    """
    if rule_type == "merchant":
        merchant_rules = rule_service.get_all_rules(category_id, limit, offset)
        total = rule_service.count_rules(category_id)
        return CategorizationRuleListResponse(
            rules=merchant_rules,
            total=total,
            has_more=(offset + len(merchant_rules)) < total,
        )
    elif rule_type == "description":
        desc_rules_raw = desc_rule_service.get_all_rules(category_id=category_id, limit=limit, offset=offset)
        desc_rules = [
            CategorizationRuleResponse(
                id=r.id,
                merchant_pattern=None,
                category_id=r.category_id,
                category_name=r.category_name,
                rule_type="description",
                description_pattern=r.description_pattern,
                account_id=r.account_id,
                account_name=r.account_name,
                created_at=r.created_at,
            )
            for r in desc_rules_raw
        ]
        total = desc_rule_service.count_rules(category_id=category_id)
        return CategorizationRuleListResponse(
            rules=desc_rules,
            total=total,
            has_more=(offset + len(desc_rules)) < total,
        )
    else:
        # Fetch all rules from both services (use large limit, we'll paginate manually)
        merchant_rules = rule_service.get_all_rules(category_id, limit=1000, offset=0)
        desc_rules_raw = desc_rule_service.get_all_rules(category_id=category_id, limit=1000, offset=0)

        # Convert desc rules to unified response format
        desc_rules = [
            CategorizationRuleResponse(
                id=r.id,
                merchant_pattern=None,
                category_id=r.category_id,
                category_name=r.category_name,
                rule_type="description",
                description_pattern=r.description_pattern,
                account_id=r.account_id,
                account_name=r.account_name,
                created_at=r.created_at,
            )
            for r in desc_rules_raw
        ]

        # Merge and sort by created_at DESC
        all_rules = merchant_rules + desc_rules
        all_rules.sort(key=lambda r: r.created_at, reverse=True)

        total = len(all_rules)
        paginated = all_rules[offset:offset + limit]
        has_more = (offset + len(paginated)) < total

        return CategorizationRuleListResponse(
            rules=paginated,
            total=total,
            has_more=has_more,
        )


@router.post("/rules", response_model=CategorizationRuleResponse, status_code=201)
async def create_rule(data: RuleCreateRequest) -> CategorizationRuleResponse:
    """
    Create a categorization rule manually.

    Rules are typically auto-created when users change transaction categories,
    but this endpoint allows manual rule creation.

    Supports both merchant pattern rules and description pattern rules.
    Provide either merchant_pattern OR (description_pattern + account_id).
    """
    if data.description_pattern:
        desc_data = DescriptionPatternRuleCreate(
            description_pattern=data.description_pattern,
            account_id=data.account_id,
            category_id=data.category_id,
        )
        result = desc_rule_service.create_rule(desc_data)
        return CategorizationRuleResponse(
            id=result.id,
            merchant_pattern=None,
            category_id=result.category_id,
            category_name=result.category_name,
            rule_type="description",
            description_pattern=result.description_pattern,
            account_id=result.account_id,
            account_name=result.account_name,
            created_at=result.created_at,
        )
    else:
        merchant_data = CategorizationRuleCreate(
            merchant_pattern=data.merchant_pattern,
            category_id=data.category_id,
        )
        return rule_service.create_rule(merchant_data)


@router.get("/rules/{rule_id}", response_model=CategorizationRuleResponse)
async def get_rule(rule_id: str) -> CategorizationRuleResponse:
    """Get a specific categorization rule."""
    rule = rule_service.get_by_id(rule_id)
    if rule:
        return rule
    desc_rule = desc_rule_service.get_by_id(rule_id)
    if desc_rule:
        return CategorizationRuleResponse(
            id=desc_rule.id,
            merchant_pattern=None,
            category_id=desc_rule.category_id,
            category_name=desc_rule.category_name,
            rule_type="description",
            description_pattern=desc_rule.description_pattern,
            account_id=desc_rule.account_id,
            account_name=desc_rule.account_name,
            created_at=desc_rule.created_at,
        )
    raise HTTPException(status_code=404, detail="Rule not found")


@router.delete("/rules/{rule_id}", status_code=204)
async def delete_rule(rule_id: str) -> None:
    """
    Delete a categorization rule.

    Does not affect already-categorized transactions.
    Tries merchant rules first, then description pattern rules.
    """
    success = rule_service.delete_rule(rule_id)
    if not success:
        success = desc_rule_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rule not found")


# ============================================================================
# Pattern Preview Endpoints
# ============================================================================


@router.post("/preview-pattern", response_model=PatternPreviewResponse)
async def preview_pattern(request: PatternPreviewRequest) -> PatternPreviewResponse:
    """
    Preview the extracted pattern from a transaction description.

    Takes a raw description and returns the generated pattern that would
    be used for a description-based categorization rule.
    """
    pattern = extract_pattern(request.description)
    return PatternPreviewResponse(original=request.description, pattern=pattern)


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
