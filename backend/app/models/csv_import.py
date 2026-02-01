from enum import Enum
from typing import Literal
from pydantic import BaseModel, model_validator


class AmountMode(str, Enum):
    SINGLE = "single"
    SPLIT = "split"


class CsvColumnMapping(BaseModel):
    date_column: str
    description_column: str
    amount_mode: AmountMode
    amount_column: str | None = None
    debit_column: str | None = None
    credit_column: str | None = None
    date_format: str = "YYYY-MM-DD"
    category_column: str | None = None

    @model_validator(mode='after')
    def validate_amount_columns(self):
        if self.amount_mode == AmountMode.SINGLE:
            if not self.amount_column:
                raise ValueError("amount_column required when amount_mode is single")
        else:
            if not self.debit_column or not self.credit_column:
                raise ValueError("debit_column and credit_column required when amount_mode is split")
        return self


class CsvPreviewRequest(BaseModel):
    file_content: str


class CsvPreviewResponse(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]
    row_count: int
    suggested_mapping: CsvColumnMapping | None = None


class CsvParseRequest(BaseModel):
    account_id: str
    file_content: str
    mapping: CsvColumnMapping


class ParsedTransaction(BaseModel):
    row_number: int
    date: str
    description: str
    amount: int
    status: Literal["valid", "warning", "error", "duplicate"]
    status_reason: str | None = None
    csv_category: str | None = None
    category_id: str | None = None
    category_name: str | None = None
    category_emoji: str | None = None


class CsvParseResponse(BaseModel):
    transactions: list[ParsedTransaction]
    valid_count: int
    warning_count: int
    error_count: int
    unmatched_categories: list[str] = []


class BulkTransactionCreateRequest(BaseModel):
    account_id: str
    transactions: list[ParsedTransaction]
    save_mapping: bool = True
    mapping: CsvColumnMapping | None = None


class BulkTransactionCreateResponse(BaseModel):
    created_count: int
    account_id: str
