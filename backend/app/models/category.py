from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CategoryGroup(str, Enum):
    ESSENTIAL = "Essential"
    LIFESTYLE = "Lifestyle"
    INCOME = "Income"
    TRANSFER = "Transfer"
    OTHER = "Other"


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    emoji: Optional[str] = Field(None, max_length=10)
    parent_id: Optional[str] = None
    group_name: CategoryGroup
    budget_amount: Optional[int] = Field(None, ge=0)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    emoji: Optional[str] = Field(None, max_length=10)
    parent_id: Optional[str] = None
    group_name: Optional[CategoryGroup] = None
    budget_amount: Optional[int] = Field(None, ge=0)


class CategoryResponse(BaseModel):
    id: str
    name: str
    emoji: Optional[str]
    parent_id: Optional[str]
    group_name: CategoryGroup
    budget_amount: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class CategoryTree(BaseModel):
    id: str
    name: str
    emoji: Optional[str]
    parent_id: Optional[str]
    group_name: CategoryGroup
    budget_amount: Optional[int]
    created_at: datetime
    children: List["CategoryTree"] = []

    class Config:
        from_attributes = True


CategoryTree.model_rebuild()
