# Data Model: Transactions Core

**Feature**: 002-transactions-core
**Date**: 2026-01-11

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────────────────────┐       ┌─────────────────┐
│    accounts     │       │           transactions              │       │   categories    │
├─────────────────┤       ├─────────────────────────────────────┤       ├─────────────────┤
│ id (PK)         │───1:N─│ id (PK)                             │───N:1─│ id (PK)         │
│ name            │       │ account_id (FK) NOT NULL            │       │ name            │
│ type            │       │ date                                │       │ emoji           │
│ institution     │       │ description                         │       │ parent_id (FK)  │
│ is_asset        │       │ original_description                │       │ group_name      │
│ created_at      │       │ amount                              │       │ budget_amount   │
└─────────────────┘       │ category_id (FK) NULLABLE           │       │ created_at      │
                          │ reviewed                            │       └─────────────────┘
                          │ reviewed_at                         │
                          │ notes                               │
                          │ created_at                          │
                          └─────────────────────────────────────┘
```

## Transaction Entity

### Database Schema (DuckDB)

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36) NOT NULL,
    date DATE NOT NULL,
    description VARCHAR(500) NOT NULL,
    original_description VARCHAR(500) NOT NULL,
    amount INTEGER NOT NULL,  -- Stored in cents (e.g., $10.50 = 1050)
    category_id VARCHAR(36),
    reviewed BOOLEAN NOT NULL DEFAULT FALSE,
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (account_id) REFERENCES accounts(id),
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_transactions_account_date
    ON transactions(account_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_category
    ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_reviewed
    ON transactions(reviewed);
```

### Field Specifications

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID v4 identifier |
| account_id | VARCHAR(36) | NOT NULL, FK | Reference to accounts table |
| date | DATE | NOT NULL | Transaction date (YYYY-MM-DD) |
| description | VARCHAR(500) | NOT NULL | User-editable description |
| original_description | VARCHAR(500) | NOT NULL | Original description from import (immutable) |
| amount | INTEGER | NOT NULL | Amount in cents, negative for expenses |
| category_id | VARCHAR(36) | FK, NULLABLE | Reference to categories table |
| reviewed | BOOLEAN | NOT NULL, DEFAULT FALSE | Whether user has reviewed |
| reviewed_at | TIMESTAMP | NULLABLE | Timestamp when marked reviewed |
| notes | TEXT | NULLABLE | User notes/memo |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Record creation timestamp |

### Validation Rules

1. **account_id**: Must reference existing account (referential integrity)
2. **category_id**: Must reference existing category OR be null
3. **date**: Valid date, not in future (warning only, not enforced)
4. **description**: 1-500 characters, trimmed whitespace
5. **original_description**: 1-500 characters, set once on creation, immutable
6. **amount**: Non-zero integer (-999999999 to 999999999 cents)
7. **reviewed_at**: Auto-set when reviewed=true, auto-cleared when reviewed=false

### State Transitions

```
┌─────────────────┐
│   Unreviewed    │ (reviewed=false, reviewed_at=null)
│   (default)     │
└────────┬────────┘
         │ Toggle reviewed
         ▼
┌─────────────────┐
│    Reviewed     │ (reviewed=true, reviewed_at=timestamp)
└────────┬────────┘
         │ Toggle reviewed
         ▼
┌─────────────────┐
│   Unreviewed    │ (reviewed=false, reviewed_at=null)
└─────────────────┘
```

## Pydantic Models (Python)

### TransactionCreate

```python
class TransactionCreate(BaseModel):
    """Model for creating a new transaction (used by CSV import, not direct API)"""
    account_id: str
    date: date
    description: str = Field(..., min_length=1, max_length=500)
    original_description: str = Field(..., min_length=1, max_length=500)
    amount: int = Field(..., ge=-999999999, le=999999999, ne=0)
    category_id: str | None = None
    reviewed: bool = False
    notes: str | None = None
```

### TransactionUpdate

```python
class TransactionUpdate(BaseModel):
    """Model for updating a transaction (partial update)"""
    description: str | None = Field(None, min_length=1, max_length=500)
    category_id: str | None = None  # Can be set to null to uncategorize
    reviewed: bool | None = None
    notes: str | None = None  # Can be set to null to clear notes

    class Config:
        # Allow explicit None values for clearing fields
        extra = "forbid"
```

### TransactionResponse

```python
class TransactionResponse(BaseModel):
    """Model for transaction in API responses"""
    id: str
    account_id: str
    date: date
    description: str
    original_description: str
    amount: int
    category_id: str | None
    reviewed: bool
    reviewed_at: datetime | None
    notes: str | None
    created_at: datetime

    # Joined fields (optional, populated when needed)
    account_name: str | None = None
    category_name: str | None = None
    category_emoji: str | None = None
```

### TransactionListResponse

```python
class TransactionListResponse(BaseModel):
    """Paginated list response"""
    items: list[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool
```

### TransactionFilters

```python
class TransactionFilters(BaseModel):
    """Query parameters for filtering transactions"""
    account_id: str | None = None
    category_id: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    amount_min: int | None = None
    amount_max: int | None = None
    reviewed: bool | None = None
    search: str | None = Field(None, max_length=100)
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
```

## TypeScript Types (Frontend)

```typescript
// Transaction entity
export interface Transaction {
  id: string;
  account_id: string;
  date: string;  // ISO date string YYYY-MM-DD
  description: string;
  original_description: string;
  amount: number;  // Integer cents
  category_id: string | null;
  reviewed: boolean;
  reviewed_at: string | null;  // ISO datetime string
  notes: string | null;
  created_at: string;  // ISO datetime string

  // Joined fields
  account_name?: string;
  category_name?: string;
  category_emoji?: string;
}

// For update requests (partial)
export interface TransactionUpdate {
  description?: string;
  category_id?: string | null;
  reviewed?: boolean;
  notes?: string | null;
}

// Paginated response
export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Filter parameters
export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  reviewed?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
}
```

## Relationships

### Transaction → Account (Many-to-One, Required)

- Every transaction belongs to exactly one account
- Account deletion is blocked if transactions exist
- Used for: filtering by account, display grouping

### Transaction → Category (Many-to-One, Optional)

- Transaction may have zero or one category
- Category deletion sets transaction.category_id to NULL
- Used for: expense categorization, budget tracking

## Data Lifecycle

1. **Creation**: Transactions created via CSV import (future spec) with all required fields
2. **Update**: Users update category_id, reviewed, notes, and description via API
3. **Delete**: Soft delete not implemented; hard delete removes record
4. **Archive**: Not in scope; transactions remain indefinitely

## Integrity Constraints

| Constraint | Behavior |
|------------|----------|
| Delete account with transactions | BLOCKED (400 error) |
| Delete category with transactions | SET NULL on category_id |
| Update non-existent transaction | 404 error |
| Update with invalid category_id | 400 error |
| Update with invalid account_id | Not allowed (account_id immutable) |
