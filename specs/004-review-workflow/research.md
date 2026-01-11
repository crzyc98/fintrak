# Research: Transactions Review Workflow

**Feature**: 004-review-workflow
**Date**: 2026-01-11

## Overview

Research findings for implementing the transaction review workflow. All technical decisions are informed by existing codebase patterns.

---

## 1. DuckDB Atomic Transactions for Bulk Operations

**Decision**: Use DuckDB's native transaction support with `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`

**Rationale**:
- DuckDB supports ACID transactions natively
- Existing codebase uses context manager pattern (`get_db()`) which can be extended
- Aligns with FR-007 requirement for atomic bulk operations

**Alternatives considered**:
- Application-level rollback (manually reverting changes) - Rejected: error-prone, doesn't handle crashes
- No transaction wrapping - Rejected: violates atomicity requirement

**Implementation pattern**:
```python
with get_db() as conn:
    conn.execute("BEGIN TRANSACTION")
    try:
        # bulk operations
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
```

---

## 2. Date Grouping Strategy (Today/Yesterday/Date)

**Decision**: Compute date groups server-side, return grouped response structure

**Rationale**:
- Reduces client-side computation
- Server has access to consistent timezone (can use UTC or configured timezone)
- Aligns with existing API patterns (server does heavy lifting)

**Alternatives considered**:
- Client-side grouping - Rejected: duplicates logic, timezone inconsistencies
- SQL-level grouping with labels - Considered but complex; hybrid approach preferred

**Implementation pattern**:
- Query returns transactions ordered by date DESC
- Service layer groups by date and assigns labels:
  - Today: `date == today`
  - Yesterday: `date == today - 1`
  - Others: formatted as "Jan 8", "Jan 7", etc.

---

## 3. Bulk Operation Request/Response Design

**Decision**: Single endpoint with operation discriminator, typed payloads

**Rationale**:
- Single endpoint (`POST /api/transactions/bulk`) is cleaner than multiple endpoints
- Discriminator pattern (`operation` field) is well-understood
- Matches spec requirement for unified bulk operations

**Alternatives considered**:
- Separate endpoints per operation (`/bulk-review`, `/bulk-category`) - Rejected: violates single-responsibility for bulk actions
- GraphQL mutations - Rejected: project uses REST

**Request schema**:
```json
{
  "transaction_ids": ["uuid1", "uuid2"],
  "operation": "mark_reviewed" | "set_category" | "add_note",
  "payload": {
    "category_id": "uuid",  // for set_category
    "note": "string"        // for add_note
  }
}
```

---

## 4. Frontend State Management for Selections

**Decision**: Local component state with `Set<string>` for selected IDs

**Rationale**:
- Existing TransactionsView.tsx uses local state pattern successfully
- Selection state is ephemeral (doesn't need persistence)
- Keeps component self-contained

**Alternatives considered**:
- Redux/global state - Rejected: overkill for ephemeral selection state
- URL params for selection - Rejected: selection is transient, not shareable

**Implementation pattern**:
```typescript
const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
const toggleSelection = (id: string) => {
  setSelectedIds(prev => {
    const next = new Set(prev);
    next.has(id) ? next.delete(id) : next.add(id);
    return next;
  });
};
```

---

## 5. Indeterminate Checkbox State

**Decision**: Native HTML `indeterminate` property via ref

**Rationale**:
- HTML checkboxes support `indeterminate` natively
- React requires ref to set this property (not available as prop)
- Clean visual indicator for partial selection

**Implementation pattern**:
```typescript
const checkboxRef = useRef<HTMLInputElement>(null);
useEffect(() => {
  if (checkboxRef.current) {
    checkboxRef.current.indeterminate = someSelected && !allSelected;
  }
}, [someSelected, allSelected]);
```

---

## 6. Review Queue Pagination Strategy

**Decision**: Offset-based pagination matching existing transaction list pattern

**Rationale**:
- Consistent with existing `TransactionListResponse` pattern
- Simple to implement with SQL `LIMIT/OFFSET`
- Adequate for expected scale (hundreds of transactions in review queue)

**Alternatives considered**:
- Cursor-based pagination - Rejected: adds complexity, not needed at this scale
- Load-all with virtual scrolling - Rejected: violates FR-003 limit requirement

---

## 7. Dashboard Widget vs Full Page: Shared Components

**Decision**: Extract shared `ReviewTransactionList` component, compose differently

**Rationale**:
- DRY principle: selection logic, transaction rendering shared
- Widget shows condensed view (5 items, no bulk actions)
- Full page shows complete view (50+ items, full action bar)

**Component hierarchy**:
```
ReviewTransactionList (shared)
├── used by TransactionReview (widget) - limited items, navigation link
└── used by ReviewPage (full) - pagination, action bar
```

---

## 8. Notes Append Behavior

**Decision**: Server-side append with newline separator

**Rationale**:
- FR-022 specifies newline separator for appending
- Server handles null checks and formatting
- Consistent behavior regardless of client

**Implementation**:
```python
if existing_notes:
    new_notes = f"{existing_notes}\n{new_note}"
else:
    new_notes = new_note
```

---

## Summary

All research items resolved. No blocking unknowns remain. Implementation can proceed with:

1. Backend: Extend transaction service with bulk operations, add review queue endpoint
2. Frontend: Refactor existing TransactionReview widget, create dedicated ReviewPage
3. Testing: Unit tests for bulk atomicity, integration tests for full workflow
