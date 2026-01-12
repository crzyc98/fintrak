"""Models for transaction review workflow and bulk operations"""
from enum import Enum
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field, model_validator

from app.models.transaction import TransactionResponse


class BulkOperationType(str, Enum):
    """Types of bulk operations that can be performed on transactions"""
    MARK_REVIEWED = "mark_reviewed"
    SET_CATEGORY = "set_category"
    ADD_NOTE = "add_note"


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations on transactions"""
    transaction_ids: list[str] = Field(..., min_length=1, max_length=500)
    operation: BulkOperationType
    category_id: Optional[str] = None
    note: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode='after')
    def validate_payload(self) -> 'BulkOperationRequest':
        if self.operation == BulkOperationType.SET_CATEGORY and not self.category_id:
            raise ValueError("category_id required for set_category operation")
        if self.operation == BulkOperationType.ADD_NOTE and not self.note:
            raise ValueError("note required for add_note operation")
        return self

    class Config:
        extra = "forbid"


class BulkOperationResponse(BaseModel):
    """Response model for successful bulk operations"""
    success: bool
    affected_count: int
    operation: BulkOperationType
    transaction_ids: list[str]


class DateGroupedTransactions(BaseModel):
    """Transactions grouped by date for review queue"""
    date_label: str  # "Today", "Yesterday", "Jan 8", etc.
    date: date  # Actual date for sorting
    transactions: list[TransactionResponse]


class ReviewQueueResponse(BaseModel):
    """Response model for review queue endpoint"""
    groups: list[DateGroupedTransactions]
    total_count: int
    displayed_count: int
    has_more: bool


class ReviewQueueCountResponse(BaseModel):
    """Response model for review queue count endpoint"""
    count: int
