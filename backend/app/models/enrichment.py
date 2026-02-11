"""
Pydantic models for AI-powered transaction enrichment.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class EnrichmentTriggerRequest(BaseModel):
    """Request to trigger enrichment for transactions."""
    transaction_ids: Optional[list[str]] = None
    limit: int = Field(200, ge=1, le=1000)


class EnrichmentResult(BaseModel):
    """Per-transaction enrichment result from AI."""
    transaction_id: str
    normalized_merchant: Optional[str] = None
    subcategory: Optional[str] = None
    is_discretionary: Optional[bool] = None


class EnrichmentBatchResponse(BaseModel):
    """Response from enrichment batch processing."""
    total_count: int
    success_count: int
    failure_count: int
    skipped_count: int
    duration_ms: int
    error_message: Optional[str] = None
