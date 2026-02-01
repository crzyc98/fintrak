"""
Pydantic models for category mapping feature.
Used during CSV import to map bank-specific categories to app categories.
"""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class CategoryMappingSuggestion(BaseModel):
    """AI-generated suggestion for mapping a source category to a target category."""
    source_category: str
    target_category_id: str | None = None
    target_category_name: str | None = None
    target_category_emoji: str | None = None
    confidence: float = 0.0


class CategoryMappingSuggestRequest(BaseModel):
    """Request to get AI-suggested mappings for source categories."""
    account_id: str
    source_categories: list[str]


class CategoryMappingSuggestResponse(BaseModel):
    """Response containing AI-suggested category mappings."""
    suggestions: list[CategoryMappingSuggestion]


class CategoryMappingSaveItem(BaseModel):
    """A single category mapping to save."""
    source_category: str
    target_category_id: str


class CategoryMappingSaveRequest(BaseModel):
    """Request to save category mappings."""
    account_id: str
    mappings: list[CategoryMappingSaveItem]


class CategoryMappingSaveResponse(BaseModel):
    """Response after saving category mappings."""
    saved_count: int


class CategoryMappingData(BaseModel):
    """A saved category mapping."""
    id: str
    account_id: str | None
    source_category: str
    target_category_id: str
    target_category_name: str | None = None
    target_category_emoji: str | None = None
    source: Literal["ai", "user"]
    created_at: datetime


class CategoryMappingListResponse(BaseModel):
    """Response containing a list of saved category mappings."""
    mappings: list[CategoryMappingData]
    total: int


class TransactionToCategorize(BaseModel):
    """A parsed transaction to categorize."""
    row_number: int
    description: str
    amount: int


class TransactionCategorizationRequest(BaseModel):
    """Request to categorize parsed transactions by description."""
    transactions: list[TransactionToCategorize]


class TransactionCategorySuggestion(BaseModel):
    """AI-suggested category for a transaction."""
    row_number: int
    category_id: str
    category_name: str
    category_emoji: str | None = None
    confidence: float


class TransactionCategorizationResponse(BaseModel):
    """Response containing AI-suggested categories for transactions."""
    suggestions: list[TransactionCategorySuggestion]
