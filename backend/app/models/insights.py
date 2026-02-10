from typing import Optional
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator


class InsightPeriod(str, Enum):
    CURRENT_MONTH = "current_month"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    CUSTOM = "custom"


class InsightType(str, Enum):
    SUMMARY = "summary"
    REPORT = "report"


class InsightRequest(BaseModel):
    period: InsightPeriod
    type: InsightType
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    @model_validator(mode="after")
    def validate_custom_period(self):
        if self.period == InsightPeriod.CUSTOM:
            if not self.date_from or not self.date_to:
                raise ValueError(
                    "date_from and date_to are required when period is 'custom'"
                )
            if self.date_from > self.date_to:
                raise ValueError("date_from must be before date_to")
        return self


class CategorySpendingResponse(BaseModel):
    category_id: str
    category_name: str
    category_emoji: Optional[str] = None
    total_amount_cents: int
    transaction_count: int
    previous_period_amount_cents: Optional[int] = None
    change_percentage: Optional[float] = None


class AnomalyResponse(BaseModel):
    transaction_id: str
    transaction_date: date
    description: str
    merchant: Optional[str] = None
    amount_cents: int
    category_name: str
    category_avg_cents: int
    deviation_factor: float


class InsightResponse(BaseModel):
    period_start: date
    period_end: date
    total_spending_cents: int
    total_transactions: int
    uncategorized_count: int
    summary: Optional[str] = None
    top_categories: list[CategorySpendingResponse] = Field(default_factory=list)
    anomalies: list[AnomalyResponse] = Field(default_factory=list)
    anomaly_explanations: Optional[str] = None
    suggestions: list[str] = Field(default_factory=list)
    generated_at: datetime
    insufficient_data: bool = False
    insufficient_data_message: Optional[str] = None
