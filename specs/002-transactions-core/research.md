# Research: Transactions Core

**Feature**: 002-transactions-core
**Date**: 2026-01-11

## Research Tasks

Based on technical context analysis and feature requirements, the following decisions were researched and resolved.

---

## 1. Pagination Strategy

**Decision**: Offset-based pagination with `limit` and `offset` parameters

**Rationale**:
- Simpler implementation matching user mental model (page 1, page 2, etc.)
- Adequate performance for target scale (10K transactions per account)
- DuckDB OFFSET/LIMIT is efficient with proper indexing
- Existing codebase has no cursor-based patterns to follow

**Alternatives Considered**:
- **Cursor-based (keyset)**: Better for real-time data or infinite scroll, but adds complexity with multi-column sorting. Overkill for this use case.
- **No pagination**: Would violate SC-001 (2s page load) with large datasets.

**Implementation**:
```sql
SELECT * FROM transactions
WHERE [filters]
ORDER BY date DESC, id DESC
LIMIT :limit OFFSET :offset
```

---

## 2. Filter Implementation

**Decision**: Server-side SQL WHERE clauses with parameterized queries

**Rationale**:
- Required by FR-011 (server-side filtering for fast response)
- DuckDB query optimizer handles combined filters efficiently
- Parameterized queries prevent SQL injection
- Matches existing service layer patterns

**Filter Parameters**:
| Filter | SQL Clause |
|--------|-----------|
| account_id | `account_id = :account_id` |
| category_id | `category_id = :category_id` |
| date_from | `date >= :date_from` |
| date_to | `date <= :date_to` |
| amount_min | `amount >= :amount_min` |
| amount_max | `amount <= :amount_max` |
| reviewed | `reviewed = :reviewed` |
| search | `LOWER(description) LIKE LOWER(:search)` |

**Alternatives Considered**:
- **Client-side filtering**: Would require loading all data, violating performance requirements
- **Elasticsearch**: Overkill for single-user app with 10K records

---

## 3. Inline Editing UX Pattern

**Decision**: Click-to-edit with immediate save on blur/selection

**Rationale**:
- Matches FR-012 (inline edit without navigation)
- Matches FR-013 (immediate UI reflection)
- Consistent with existing AccountsView/CategoriesView patterns
- Category dropdown on click, text input for notes, checkbox for reviewed

**Implementation Details**:
- Category: Click shows dropdown, select saves immediately
- Notes: Click shows text input, blur saves
- Reviewed: Checkbox toggle saves immediately
- All edits call PUT /api/transactions/{id} with partial update

**Alternatives Considered**:
- **Edit mode per row**: More complex state management, slower UX
- **Modal for all edits**: Violates "inline" requirement

---

## 4. ID Generation

**Decision**: UUID v4 (string format)

**Rationale**:
- Consistent with existing accounts/categories tables
- No collisions without central coordination
- Works well with DuckDB VARCHAR(36) type

**Implementation**:
```python
import uuid
transaction_id = str(uuid.uuid4())
```

---

## 5. Amount Storage Format

**Decision**: Integer cents (e.g., $10.50 = 1050)

**Rationale**:
- Consistent with existing balance_snapshots table
- Avoids floating-point precision issues
- Easy arithmetic for aggregations
- Frontend formats for display

**Data Flow**:
- API accepts/returns integer cents
- Frontend formats with `(amount / 100).toFixed(2)`
- Currency symbol added in display layer

---

## 6. Date Handling

**Decision**: DATE type in DuckDB, ISO 8601 string (YYYY-MM-DD) in API

**Rationale**:
- DATE type is efficient for date range queries
- ISO format is unambiguous and sortable
- Consistent with JavaScript Date parsing

**Implementation**:
- DuckDB: `date DATE NOT NULL`
- API: `date: str` with format "2026-01-11"
- Validation: Pydantic date type with string serialization

---

## 7. Search Implementation

**Decision**: Case-insensitive LIKE query on description field

**Rationale**:
- Simple and adequate for text search within 10K records
- DuckDB LIKE with LOWER() function
- Searches user-editable `description` (not original_description)

**Query Pattern**:
```sql
WHERE LOWER(description) LIKE LOWER('%' || :search || '%')
```

**Alternatives Considered**:
- **Full-text search**: DuckDB has FTS extension but overkill for simple substring matching
- **Search on both description fields**: Could confuse users; keep simple

---

## 8. Referential Integrity

**Decision**: Foreign key constraints with cascade behavior

**Rationale**:
- FR-002/FR-003 require referential integrity
- Account deletion should be blocked if transactions exist (consistent with balance_snapshots)
- Category deletion should set category_id to NULL (soft reference)

**Implementation**:
```sql
CREATE TABLE transactions (
    ...
    account_id VARCHAR(36) NOT NULL REFERENCES accounts(id),
    category_id VARCHAR(36) REFERENCES categories(id) ON DELETE SET NULL,
    ...
);
```

---

## 9. Index Strategy

**Decision**: Composite index on (account_id, date DESC) for common query pattern

**Rationale**:
- Most common query: list transactions for an account sorted by date
- Filter queries benefit from indexed columns
- DuckDB creates indexes implicitly for PRIMARY KEY and UNIQUE

**Indexes**:
```sql
CREATE INDEX idx_transactions_account_date ON transactions(account_id, date DESC);
CREATE INDEX idx_transactions_category ON transactions(category_id);
```

---

## 10. Response Shape for List Endpoint

**Decision**: Paginated response with metadata

**Rationale**:
- Client needs total count for pagination UI
- Include page metadata for navigation

**Response Shape**:
```json
{
  "items": [...],
  "total": 1234,
  "limit": 50,
  "offset": 0,
  "has_more": true
}
```

---

## Summary

All technical decisions align with:
- Existing codebase patterns (service layer, Pydantic, DuckDB)
- Feature requirements (FR-001 through FR-016)
- Success criteria (SC-001 through SC-007)
- Performance constraints (10K+ transactions)

No NEEDS CLARIFICATION items remain. Ready for Phase 1 design artifacts.
