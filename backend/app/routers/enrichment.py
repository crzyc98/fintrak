"""
API endpoints for AI-powered transaction enrichment.
"""
from typing import Optional
from fastapi import APIRouter

from app.models.enrichment import EnrichmentTriggerRequest, EnrichmentBatchResponse
from app.services.enrichment_service import enrichment_service

router = APIRouter(prefix="/api/enrichment", tags=["enrichment"])


@router.post("/trigger", response_model=EnrichmentBatchResponse)
async def trigger_enrichment(
    request: Optional[EnrichmentTriggerRequest] = None,
) -> EnrichmentBatchResponse:
    """
    Trigger AI enrichment for unenriched transactions.

    Enrichment normalizes merchant names, assigns subcategories,
    and classifies transactions as essential vs. discretionary.

    Args:
        request: Optional request body with specific transaction IDs and limit

    Returns:
        EnrichmentBatchResponse with processing results
    """
    return enrichment_service.trigger_enrichment(request)
