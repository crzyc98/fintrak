# Data Model: CSV Import

**Feature**: 005-csv-import | **Date**: 2026-01-12

## Schema Changes

### accounts table (existing - modify)

Add column:
```sql
ALTER TABLE accounts ADD COLUMN csv_column_mapping JSON;
```

**csv_column_mapping** structure:
```json
{
  "date_column": "string",       // CSV header name for date
  "description_column": "string", // CSV header name for description
  "amount_mode": "single|split", // How amounts are represented
  "amount_column": "string|null", // Header when mode=single
  "debit_column": "string|null",  // Header when mode=split
  "credit_column": "string|null", // Header when mode=split
  "date_format": "string"         // e.g., "YYYY-MM-DD", "MM/DD/YYYY"
}
```

---

## Pydantic Models

### CsvColumnMapping (new)

```python
class AmountMode(str, Enum):
    SINGLE = "single"
    SPLIT = "split"

class CsvColumnMapping(BaseModel):
    date_column: str
    description_column: str
    amount_mode: AmountMode
    amount_column: str | None = None  # Required when mode=single
    debit_column: str | None = None   # Required when mode=split
    credit_column: str | None = None  # Required when mode=split
    date_format: str = "YYYY-MM-DD"

    @model_validator(mode='after')
    def validate_amount_columns(self):
        if self.amount_mode == AmountMode.SINGLE:
            if not self.amount_column:
                raise ValueError("amount_column required when amount_mode is single")
        else:
            if not self.debit_column or not self.credit_column:
                raise ValueError("debit_column and credit_column required when amount_mode is split")
        return self
```

### CsvPreviewRequest / CsvPreviewResponse

```python
class CsvPreviewRequest(BaseModel):
    file_content: str  # Base64 encoded CSV content

class CsvPreviewResponse(BaseModel):
    headers: list[str]
    sample_rows: list[list[str]]  # First 5 rows
    row_count: int
    suggested_mapping: CsvColumnMapping | None  # Auto-detected if possible
```

### CsvParseRequest / CsvParseResponse

```python
class CsvParseRequest(BaseModel):
    account_id: str
    file_content: str  # Base64 encoded CSV content
    mapping: CsvColumnMapping

class ParsedTransaction(BaseModel):
    row_number: int
    date: str  # ISO format
    description: str
    amount: int  # In cents
    status: Literal["valid", "warning", "error"]
    status_reason: str | None = None  # e.g., "Potential duplicate", "Invalid date"

class CsvParseResponse(BaseModel):
    transactions: list[ParsedTransaction]
    valid_count: int
    warning_count: int
    error_count: int
```

### BulkTransactionCreateRequest / BulkTransactionCreateResponse

```python
class BulkTransactionCreateRequest(BaseModel):
    account_id: str
    transactions: list[ParsedTransaction]  # Only valid/warning rows user selected
    save_mapping: bool = True  # Whether to save mapping to account

class BulkTransactionCreateResponse(BaseModel):
    created_count: int
    account_id: str
```

---

## Entity Updates

### Account (extend existing)

Add to `AccountResponse`:
```python
csv_column_mapping: CsvColumnMapping | None = None
```

Add to `AccountUpdate`:
```python
csv_column_mapping: CsvColumnMapping | None = None
```

---

## Validation Rules

| Field | Rule |
|-------|------|
| `file_content` | Must be valid base64; decoded content must be valid CSV |
| `date_column` | Must match a header in the CSV |
| `description_column` | Must match a header in the CSV |
| `amount_column` | Must match a header when mode=single |
| `debit_column`, `credit_column` | Must match headers when mode=split |
| `date_format` | Must be one of supported formats |
| `amount` values | Must be parseable as numbers |
| `date` values | Must match specified format |

---

## State Transitions

### Import Flow States

```
[No File]
    → file_dropped → [File Loaded]

[File Loaded]
    → has_mapping → [Parsing]
    → no_mapping → [Mapping Required]

[Mapping Required]
    → mapping_configured → [Parsing]
    → cancelled → [No File]

[Parsing]
    → parse_complete → [Preview]
    → parse_error → [Error Display]

[Preview]
    → confirmed → [Creating Transactions]
    → cancelled → [No File]

[Creating Transactions]
    → success → [Complete] → [No File]
    → error → [Error Display]
```

---

## Relationships

```
Account (1) ──────── (0..1) CsvColumnMapping
    │
    └── (1) ──────── (0..n) Transaction
                              │
                              └── created via CSV import
                                  with reviewed=false
```

---

## Data Volume Estimates

| Entity | Expected Volume | Notes |
|--------|-----------------|-------|
| Accounts | 5-20 per user | Each may have mapping |
| CSV files | <1MB typical | Up to 10,000 rows |
| Transactions per import | 50-500 typical | Monthly bank statements |
| Duplicate checks | Per-account scope | Index on (account_id, date, description, amount) recommended |
