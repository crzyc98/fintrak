"""
API endpoints for AI-powered transaction enrichment.

DEPRECATED: Enrichment is now handled by the unified classification pipeline.
This endpoint delegates to categorization_service.trigger_categorization() and
maps the response to the legacy EnrichmentBatchResponse format.
"""
from typing import Optional
from fastapi import APIRouter

from app.models.enrichment import EnrichmentTriggerRequest, EnrichmentBatchResponse
from app.models.categorization import CategorizationTriggerRequest
from app.services.categorization_service import categorization_service

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


@router.post(
    "/trigger",
    response_model=EnrichmentBatchResponse,
    deprecated=True,
    summary="Trigger AI enrichment (deprecated — use /api/categorization/trigger instead)",
)
async def trigger_enrichment(
    request: Optional[EnrichmentTriggerRequest] = None,
) -> EnrichmentBatchResponse:
    """
    Trigger AI enrichment for unenriched transactions.

    **Deprecated**: This endpoint now delegates to the unified classification
    pipeline which handles both categorization and enrichment in a single AI call.
    Use POST /api/categorization/trigger instead.
    """
    # Map enrichment request to categorization request
    cat_request = None
    if request and request.transaction_ids:
        cat_request = CategorizationTriggerRequest(
            transaction_ids=request.transaction_ids,
        )

    result = categorization_service.trigger_categorization(cat_request)

    # Map categorization response to enrichment response format
    return EnrichmentBatchResponse(
        total_count=result.transaction_count,
        success_count=result.success_count,
        failure_count=result.failure_count,
        skipped_count=result.skipped_count,
        duration_ms=result.duration_ms or 0,
        error_message=result.error_message,
    )
