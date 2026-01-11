# Data Model: Transactions Review Workflow

**Feature**: 004-review-workflow
**Date**: 2026-01-11

## Overview

This feature primarily extends existing entities rather than creating new database tables. The Transaction entity already has all required fields (`reviewed`, `reviewed_at`, `category_id`, `notes`, `categorization_source`).

---

## Existing Entities (No Changes Required)

### Transaction (existing)

The existing `transactions` table fully supports the review workflow:

| Field | Type | Description |
|-------|------|-------------|
| id | VARCHAR(36) | Primary key (UUID) |
| account_id | VARCHAR(36) | FK to accounts |
| date | DATE | Transaction date |
| description | VARCHAR(500) | User-editable description |
| original_description | VARCHAR(500) | Raw bank description |
| amount | INTEGER | Amount in cents |
| category_id | VARCHAR(36) | FK to categories (nullable) |
| **reviewed** | BOOLEAN | Review status (default FALSE) |
| **reviewed_at** | TIMESTAMP | When marked reviewed (nullable) |
| **notes** | TEXT | User notes (nullable) |
| normalized_merchant | VARCHAR(255) | AI-normalized merchant name |
| confidence_score | DECIMAL(3,2) | AI confidence (0.00-1.00) |
| **categorization_source** | VARCHAR(10) | 'rule', 'ai', 'manual', 'none' |
| created_at | TIMESTAMP | Record creation time |

**Relevant indexes** (already exist):
- `idx_transactions_reviewed` on `reviewed` - supports review queue queries
- `idx_transactions_account_date` on `(account_id, date DESC)` - supports date ordering

### Category (existing, read-only for this feature)

Used for category dropdown in bulk set_category operation.

| Field | Type | Description |
|-------|------|-------------|
| id | VARCHAR(36) | Primary key |
| name | VARCHAR(100) | Category name |
| emoji | VARCHAR(10) | Display emoji |

---

## New API Models (Pydantic)

### BulkOperationRequest

Request model for bulk operations endpoint.

```python
class BulkOperationType(str, Enum):
    MARK_REVIEWED = "mark_reviewed"
    SET_CATEGORY = "set_category"
    ADD_NOTE = "add_note"

class BulkOperationRequest(BaseModel):
    transaction_ids: list[str] = Field(..., min_length=1, max_length=500)
    operation: BulkOperationType
    category_id: Optional[str] = None  # Required for SET_CATEGORY
    note: Optional[str] = Field(None, max_length=1000)  # Required for ADD_NOTE

    @model_validator(mode='after')
    def validate_payload(self) -> 'BulkOperationRequest':
        if self.operation == BulkOperationType.SET_CATEGORY and not self.category_id:
            raise ValueError("category_id required for set_category operation")
        if self.operation == BulkOperationType.ADD_NOTE and not self.note:
            raise ValueError("note required for add_note operation")
        return self
```

**Validation rules**:
- `transaction_ids`: 1-500 items (FR-010a)
- `category_id`: Required when operation is `set_category`
- `note`: Required when operation is `add_note`, max 1000 chars

### BulkOperationResponse

Response model for successful bulk operations.

```python
class BulkOperationResponse(BaseModel):
    success: bool
    affected_count: int
    operation: BulkOperationType
    transaction_ids: list[str]
```

### DateGroupedTransactions

Grouped transactions for review queue response.

```python
class DateGroupedTransactions(BaseModel):
    date_label: str  # "Today", "Yesterday", "Jan 8", etc.
    date: date  # Actual date for sorting
    transactions: list[TransactionResponse]
```

### ReviewQueueResponse

Response model for review queue endpoint.

```python
class ReviewQueueResponse(BaseModel):
    groups: list[DateGroupedTransactions]
    total_count: int
    displayed_count: int
    has_more: bool
```

---

## State Transitions

### Transaction Review State

```
┌─────────────────┐
│   reviewed=false │  (default state after import/AI categorization)
│   reviewed_at=null│
└────────┬────────┘
         │ mark_reviewed (bulk or individual)
         ▼
┌─────────────────┐
│   reviewed=true  │
│   reviewed_at=now│
└────────┬────────┘
         │ mark_unreviewed (toggle)
         ▼
┌─────────────────┐
│   reviewed=false │
│   reviewed_at=null│
└─────────────────┘
```

### Categorization Source State

When category is changed via bulk `set_category`:

```
┌─────────────────────────────────────┐
│ categorization_source = 'ai'/'rule' │  (before user correction)
└────────────────┬────────────────────┘
                 │ bulk set_category
                 ▼
┌─────────────────────────────────────┐
│ categorization_source = 'manual'    │  (after user correction)
└─────────────────────────────────────┘
```

---

## Query Patterns

### Review Queue Query

```sql
SELECT t.*, a.name as account_name, c.name as category_name, c.emoji as category_emoji
FROM transactions t
LEFT JOIN accounts a ON t.account_id = a.id
LEFT JOIN categories c ON t.category_id = c.id
WHERE t.reviewed = false
ORDER BY t.date DESC, t.created_at DESC
LIMIT ? OFFSET ?
```

### Review Queue Count

```sql
SELECT COUNT(*) FROM transactions WHERE reviewed = false
```

### Bulk Mark Reviewed

```sql
UPDATE transactions
SET reviewed = true, reviewed_at = ?
WHERE id IN (?, ?, ...)
```

### Bulk Set Category

```sql
UPDATE transactions
SET category_id = ?, categorization_source = 'manual'
WHERE id IN (?, ?, ...)
```

### Bulk Add Note (append)

```sql
UPDATE transactions
SET notes = CASE
    WHEN notes IS NOT NULL AND notes != ''
    THEN notes || '\n' || ?
    ELSE ?
END
WHERE id IN (?, ?, ...)
```

---

## Indexes

No new indexes required. Existing `idx_transactions_reviewed` efficiently supports:
- `WHERE reviewed = false` filter
- Combined with date ordering via sequential scan (acceptable for expected volume)

If performance becomes an issue with large unreviewed queues, consider:
```sql
CREATE INDEX idx_transactions_review_queue
ON transactions(date DESC, created_at DESC)
WHERE reviewed = false;
```
