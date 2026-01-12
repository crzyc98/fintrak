from enum import Enum
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.models.csv_import import CsvColumnMapping


class AccountType(str, Enum):
    CHECKING = "Checking"
    SAVINGS = "Savings"
    CREDIT = "Credit"
    INVESTMENT = "Investment"
    LOAN = "Loan"
    REAL_ESTATE = "Real Estate"
    CRYPTO = "Crypto"


ASSET_ACCOUNT_TYPES = {
    AccountType.CHECKING,
    AccountType.SAVINGS,
    AccountType.INVESTMENT,
    AccountType.REAL_ESTATE,
    AccountType.CRYPTO,
}


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: AccountType
    institution: Optional[str] = Field(None, max_length=200)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[AccountType] = None
    institution: Optional[str] = Field(None, max_length=200)
    csv_column_mapping: Optional["CsvColumnMapping"] = None


class AccountResponse(BaseModel):
    id: str
    name: str
    type: AccountType
    institution: Optional[str]
    is_asset: bool
    current_balance: Optional[int] = None
    csv_column_mapping: Optional["CsvColumnMapping"] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Import for forward reference resolution
from app.models.csv_import import CsvColumnMapping
AccountUpdate.model_rebuild()
AccountResponse.model_rebuild()
