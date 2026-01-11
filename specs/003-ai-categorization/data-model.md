# Data Model: AI-Powered Transaction Categorization

**Feature**: 003-ai-categorization
**Date**: 2026-01-11

## Entity Overview

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────────┐
│   Transaction   │──────▶│    Category     │◀──────│ CategorizationRule  │
│   (extended)    │       │   (existing)    │       │      (new)          │
└─────────────────┘       └─────────────────┘       └─────────────────────┘
         │
         ▼
┌─────────────────────┐
│ CategorizationBatch │
│      (new)          │
└─────────────────────┘
```

## Entities

### Transaction (Extended)

Existing entity with new fields for categorization tracking.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Existing |
| account_id | UUID | FK → accounts | Existing |
| date | DATE | NOT NULL | Existing |
| description | VARCHAR(500) | NOT NULL | Existing - display name |
| original_description | VARCHAR(500) | | Existing - immutable original from import |
| amount | INTEGER | NOT NULL | Existing - amount in cents |
| category_id | UUID | FK → categories, NULLABLE | Existing |
| reviewed | BOOLEAN | DEFAULT false | Existing |
| notes | TEXT | | Existing |
| created_at | TIMESTAMP | DEFAULT NOW | Existing |
| updated_at | TIMESTAMP | | Existing |
| **normalized_merchant** | VARCHAR(255) | NULLABLE | **NEW** - Cleaned merchant name for matching |
| **confidence_score** | DECIMAL(3,2) | NULLABLE, 0.00-1.00 | **NEW** - AI confidence when auto-categorized |
| **categorization_source** | VARCHAR(10) | NULLABLE | **NEW** - How category was assigned |

**categorization_source values**:
- `rule` - Matched a learned rule
- `ai` - Assigned by AI with confidence >= threshold
- `manual` - User explicitly set the category
- `none` / NULL - Not yet categorized

**Validation Rules**:
- confidence_score: Must be between 0.00 and 1.00 when present
- categorization_source: Must be one of the enum values when present
- normalized_merchant: Derived from original_description during import/categorization

**State Transitions**:
```
[Imported] → [Rule Matched] → category_id set, source='rule'
          → [AI Categorized] → category_id set, source='ai', confidence_score set
          → [Uncategorized] → category_id NULL, source='none'

[Any State] → [User Override] → category_id changed, source='manual', creates rule
```

---

### CategorizationRule (New)

Stores learned mappings from user corrections.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| merchant_pattern | VARCHAR(255) | NOT NULL, UNIQUE | Normalized merchant text to match |
| category_id | UUID | FK → categories, NOT NULL | Target category |
| created_at | TIMESTAMP | DEFAULT NOW | When rule was learned |

**Validation Rules**:
- merchant_pattern: Non-empty, trimmed, stored lowercase for case-insensitive matching
- category_id: Must reference existing category
- Uniqueness on merchant_pattern prevents duplicate rules

**Matching Behavior** (per clarification):
- Substring/contains matching: Rule matches if `merchant_pattern` is found within transaction's `normalized_merchant`
- Case-insensitive comparison
- Most recently created rule wins on conflict (ORDER BY created_at DESC)

**Lifecycle**:
1. User changes transaction category manually
2. System extracts normalized_merchant from transaction
3. If normalized_merchant is non-empty, create/update rule
4. On future imports, rules checked before AI invocation

---

### CategorizationBatch (New)

Tracks processing metrics for observability.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| import_id | UUID | NULLABLE | Links to import batch (future feature) |
| transaction_count | INTEGER | NOT NULL | Total transactions in batch |
| success_count | INTEGER | NOT NULL, DEFAULT 0 | Successfully categorized |
| failure_count | INTEGER | NOT NULL, DEFAULT 0 | Failed to categorize (parse errors) |
| rule_match_count | INTEGER | NOT NULL, DEFAULT 0 | Categorized by rules |
| ai_match_count | INTEGER | NOT NULL, DEFAULT 0 | Categorized by AI |
| skipped_count | INTEGER | NOT NULL, DEFAULT 0 | Below confidence threshold |
| duration_ms | INTEGER | NULLABLE | Total processing time |
| error_message | TEXT | NULLABLE | Error details if batch failed |
| started_at | TIMESTAMP | DEFAULT NOW | When processing began |
| completed_at | TIMESTAMP | NULLABLE | When processing finished |

**Validation Rules**:
- success_count + failure_count + skipped_count <= transaction_count
- duration_ms: Calculated as (completed_at - started_at) in milliseconds
- error_message: Only populated on batch-level failures

**Lifecycle**:
1. Batch created when categorization triggered
2. Counters updated as transactions processed
3. completed_at and duration_ms set when finished

---

### Category (Existing - No Changes)

Reference for completeness.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(100) | NOT NULL | Display name |
| emoji | VARCHAR(10) | | Visual indicator |
| parent_id | UUID | FK → categories | For subcategories |
| group_name | VARCHAR(50) | | CategoryGroup enum |
| budget_amount | INTEGER | | Monthly budget in cents |
| created_at | TIMESTAMP | DEFAULT NOW | |

---

## Relationships

| From | To | Cardinality | Description |
|------|-----|-------------|-------------|
| Transaction | Category | N:1 | Many transactions per category |
| CategorizationRule | Category | N:1 | Many rules per category |
| Transaction | CategorizationBatch | N:1 | Many transactions per batch (implicit via timing) |

---

## Indexes

```sql
-- Existing indexes (preserved)
CREATE INDEX idx_transactions_account_date ON transactions(account_id, date);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_reviewed ON transactions(reviewed);

-- New indexes for categorization feature
CREATE INDEX idx_transactions_normalized_merchant ON transactions(normalized_merchant);
CREATE INDEX idx_transactions_categorization_source ON transactions(categorization_source);
CREATE INDEX idx_categorization_rules_category ON categorization_rules(category_id);
CREATE INDEX idx_categorization_batches_started ON categorization_batches(started_at);
```

---

## Migration Strategy

**Phase 1: Schema Extension**
```sql
-- Add new columns to transactions (nullable for backward compatibility)
ALTER TABLE transactions ADD COLUMN normalized_merchant VARCHAR(255);
ALTER TABLE transactions ADD COLUMN confidence_score DECIMAL(3,2);
ALTER TABLE transactions ADD COLUMN categorization_source VARCHAR(10);

-- Create new tables
CREATE TABLE categorization_rules (...);
CREATE TABLE categorization_batches (...);

-- Create indexes
CREATE INDEX idx_transactions_normalized_merchant ...;
```

**Phase 2: Data Backfill (Optional)**
- Existing transactions can be normalized on-demand or via background job
- categorization_source for existing manually-categorized transactions: set to 'manual'
- No blocking migration required

---

## Pydantic Models

### CategorizationRuleCreate
```python
class CategorizationRuleCreate(BaseModel):
    merchant_pattern: str = Field(..., min_length=1, max_length=255)
    category_id: str = Field(..., pattern=UUID_PATTERN)
```

### CategorizationRuleResponse
```python
class CategorizationRuleResponse(BaseModel):
    id: str
    merchant_pattern: str
    category_id: str
    category_name: str  # Joined from categories table
    created_at: datetime
```

### CategorizationBatchResponse
```python
class CategorizationBatchResponse(BaseModel):
    id: str
    transaction_count: int
    success_count: int
    failure_count: int
    rule_match_count: int
    ai_match_count: int
    skipped_count: int
    duration_ms: int | None
    started_at: datetime
    completed_at: datetime | None
```

### CategorizationResult (Internal)
```python
class CategorizationResult(BaseModel):
    transaction_id: str
    category_id: str
    confidence: float = Field(..., ge=0.0, le=1.0)
```

### TransactionUpdate (Extended)
```python
class TransactionUpdate(BaseModel):
    description: str | None = None
    category_id: str | None = None
    reviewed: bool | None = None
    notes: str | None = None
    # Note: normalized_merchant, confidence_score, categorization_source
    # are system-managed, not user-editable via this model
```
