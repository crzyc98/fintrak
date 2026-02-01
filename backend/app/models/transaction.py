from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    """Model for creating a new transaction (used by CSV import)"""
    account_id: str
    date: date
    description: str = Field(..., min_length=1, max_length=500)
    original_description: str = Field(..., min_length=1, max_length=500)
    amount: int = Field(..., ge=-999999999, le=999999999)
    category_id: Optional[str] = None
    reviewed: bool = False
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    """Model for updating a transaction (partial update)"""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    category_id: Optional[str] = None
    reviewed: Optional[bool] = None
    notes: Optional[str] = None

    class Config:
        extra = "forbid"


class TransactionResponse(BaseModel):
    """Model for transaction in API responses"""
    id: str
    account_id: str
    date: date
    description: str
    original_description: str
    amount: int
    category_id: Optional[str]
    reviewed: bool
    reviewed_at: Optional[datetime]
    notes: Optional[str]
    created_at: datetime

    # Categorization fields
    normalized_merchant: Optional[str] = None
    confidence_score: Optional[float] = None
    categorization_source: Optional[str] = None  # 'rule', 'ai', 'manual', 'none'

    # Joined fields (optional, populated when needed)
    account_name: Optional[str] = None
    category_name: Optional[str] = None
    category_emoji: Optional[str] = None

    class Config:
        from_attributes = True


class TransactionFilters(BaseModel):
    """Query parameters for filtering transactions"""
    account_id: Optional[str] = None
    category_id: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    amount_min: Optional[int] = None
    amount_max: Optional[int] = None
    reviewed: Optional[bool] = None
    search: Optional[str] = Field(None, max_length=100)
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class TransactionListResponse(BaseModel):
    """Paginated list response"""
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class SpendingDataPoint(BaseModel):
    """A single data point for the spending chart"""
    day: int  # Day of month (1-31)
    amount: int  # Cumulative spending in cents (negative = expenses)
    pace: int  # Expected pace line in cents


class MonthlySpendingResponse(BaseModel):
    """Monthly spending data for the dashboard"""
    chart_data: list[SpendingDataPoint]
    current_month_total: int  # Total spending this month in cents
    last_month_total: int  # Total spending last month in cents
    last_month_same_point: int  # Spending at same day last month in cents
    days_in_month: int  # Total days in current month
    current_day: int  # Current day of month
    month_label: str  # e.g., "January 2026"
