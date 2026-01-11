"""
Pydantic models for AI categorization feature.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Categorization Rule Models
# ============================================================================


class CategorizationRuleCreate(BaseModel):
    """Model for creating a categorization rule"""
    merchant_pattern: str = Field(..., min_length=1, max_length=255)
    category_id: str


class CategorizationRuleResponse(BaseModel):
    """Model for categorization rule in API responses"""
    id: str
    merchant_pattern: str
    category_id: str
    category_name: Optional[str] = None  # Joined from categories table
    created_at: datetime

    class Config:
        from_attributes = True


class CategorizationRuleListResponse(BaseModel):
    """Paginated list of categorization rules"""
    rules: list[CategorizationRuleResponse]
    total: int
    has_more: bool


# ============================================================================
# Categorization Batch Models
# ============================================================================


class CategorizationBatchResponse(BaseModel):
    """Model for categorization batch in API responses"""
    id: str
    import_id: Optional[str] = None
    transaction_count: int
    success_count: int
    failure_count: int
    rule_match_count: int
    ai_match_count: int
    skipped_count: int
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CategorizationBatchListResponse(BaseModel):
    """Paginated list of categorization batches"""
    batches: list[CategorizationBatchResponse]
    total: int
    has_more: bool


# ============================================================================
# Internal Models (used within services)
# ============================================================================


class CategorizationResult(BaseModel):
    """Result from AI categorization for a single transaction"""
    transaction_id: str
    category_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)


# ============================================================================
# Request/Response Models for API
# ============================================================================


class CategorizationTriggerRequest(BaseModel):
    """Request body for triggering categorization"""
    transaction_ids: Optional[list[str]] = None
    force_ai: bool = False


class NormalizationRequest(BaseModel):
    """Request body for normalization preview"""
    description: str


class NormalizationResponse(BaseModel):
    """Response for normalization preview"""
    original: str
    normalized: str
    tokens_removed: list[str] = []
