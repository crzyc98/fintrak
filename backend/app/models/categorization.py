"""
Pydantic models for AI categorization feature.
"""
from typing import Optional, Literal
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
    merchant_pattern: Optional[str] = None
    category_id: str
    category_name: Optional[str] = None  # Joined from categories table
    rule_type: Literal["merchant", "description"] = "merchant"
    description_pattern: Optional[str] = None
    account_id: Optional[str] = None
    account_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CategorizationRuleListResponse(BaseModel):
    """Paginated list of categorization rules (merchant + description)"""
    rules: list[CategorizationRuleResponse]
    total: int
    has_more: bool


# ============================================================================
# Description Pattern Rule Models
# ============================================================================


class DescriptionPatternRuleCreate(BaseModel):
    """Model for creating a description-based pattern rule"""
    description_pattern: str = Field(..., min_length=1, max_length=500)
    account_id: str
    category_id: str


class DescriptionPatternRuleResponse(BaseModel):
    """Model for description pattern rule in API responses"""
    id: str
    account_id: str
    account_name: Optional[str] = None
    description_pattern: str
    category_id: str
    category_name: Optional[str] = None
    rule_type: Literal["description"] = "description"
    created_at: datetime

    class Config:
        from_attributes = True


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
    desc_rule_match_count: int = 0
    ai_match_count: int
    skipped_count: int
    categories_created_count: int = 0
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


class UnifiedAIResult(BaseModel):
    """Result from unified AI classification for a single transaction.
    AI returns category_name (string) instead of category_id (UUID) because
    it needs to be able to suggest new category names that don't exist yet."""
    transaction_id: str
    category_name: str
    category_group: str = "Other"
    subcategory: Optional[str] = None
    is_discretionary: Optional[bool] = None
    normalized_merchant: Optional[str] = None
    confidence: float = Field(0.0, ge=0.0, le=1.0)


# ============================================================================
# Request/Response Models for API
# ============================================================================


class CategorizationTriggerRequest(BaseModel):
    """Request body for triggering categorization"""
    transaction_ids: Optional[list[str]] = None
    force_ai: bool = False
    batch_size: Optional[int] = Field(None, ge=10, le=200)


class BatchTriggerResponse(BaseModel):
    """Response from triggering a background batch classification job"""
    batch_id: str
    total_transactions: int
    status: Literal["running", "completed"]


class UnclassifiedCountResponse(BaseModel):
    """Response for unclassified transaction count"""
    count: int


class BatchProgressResponse(BaseModel):
    """Real-time progress of a batch classification job"""
    batch_id: str
    status: Literal["running", "completed", "failed"]
    total_transactions: int
    processed_transactions: int
    success_count: int
    failure_count: int
    skipped_count: int
    rule_match_count: int
    desc_rule_match_count: int
    ai_match_count: int
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class NormalizationRequest(BaseModel):
    """Request body for normalization preview"""
    description: str


class NormalizationResponse(BaseModel):
    """Response for normalization preview"""
    original: str
    normalized: str
    tokens_removed: list[str] = []


class PatternPreviewRequest(BaseModel):
    """Request body for description pattern preview"""
    description: str


class PatternPreviewResponse(BaseModel):
    """Response for description pattern preview"""
    original: str
    pattern: str
