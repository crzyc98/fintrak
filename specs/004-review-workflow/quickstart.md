# Quickstart: Transactions Review Workflow

**Feature**: 004-review-workflow
**Date**: 2026-01-11

## Overview

This guide covers how to implement and test the transaction review workflow feature.

---

## Prerequisites

- Backend server running (`cd backend && uvicorn app.main:app --reload`)
- Frontend dev server running (`cd frontend && npm run dev`)
- DuckDB database initialized with transactions

---

## Backend Implementation

### 1. Add Pydantic Models

Create `backend/app/models/review.py`:

```python
from enum import Enum
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, Field, model_validator

class BulkOperationType(str, Enum):
    MARK_REVIEWED = "mark_reviewed"
    SET_CATEGORY = "set_category"
    ADD_NOTE = "add_note"

class BulkOperationRequest(BaseModel):
    transaction_ids: list[str] = Field(..., min_length=1, max_length=500)
    operation: BulkOperationType
    category_id: Optional[str] = None
    note: Optional[str] = Field(None, max_length=1000)

    @model_validator(mode='after')
    def validate_payload(self) -> 'BulkOperationRequest':
        if self.operation == BulkOperationType.SET_CATEGORY and not self.category_id:
            raise ValueError("category_id required for set_category operation")
        if self.operation == BulkOperationType.ADD_NOTE and not self.note:
            raise ValueError("note required for add_note operation")
        return self

class BulkOperationResponse(BaseModel):
    success: bool
    affected_count: int
    operation: BulkOperationType
    transaction_ids: list[str]
```

### 2. Extend Transaction Router

Add to `backend/app/routers/transactions.py`:

```python
@router.get("/review-queue")
async def get_review_queue(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """Get unreviewed transactions grouped by day"""
    return review_service.get_review_queue(limit, offset)

@router.get("/review-queue/count")
async def get_review_queue_count():
    """Get count of unreviewed transactions"""
    count = transaction_service.count(TransactionFilters(reviewed=False))
    return {"count": count}

@router.post("/bulk", response_model=BulkOperationResponse)
async def bulk_update_transactions(request: BulkOperationRequest):
    """Perform bulk operations atomically"""
    return review_service.bulk_update(request)
```

### 3. Create Review Service

Create `backend/app/services/review_service.py`:

```python
from datetime import date, datetime, timedelta
from app.database import get_db
from app.models.review import BulkOperationRequest, BulkOperationType

class ReviewService:
    def get_review_queue(self, limit: int, offset: int):
        # Implementation with day grouping
        pass

    def bulk_update(self, request: BulkOperationRequest):
        with get_db() as conn:
            conn.execute("BEGIN TRANSACTION")
            try:
                # Validate all IDs exist
                # Execute operation
                # Commit
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise

review_service = ReviewService()
```

---

## Frontend Implementation

### 1. Add API Functions

Add to `frontend/src/services/api.ts`:

```typescript
// Review Queue Types
export interface DateGroupedTransactions {
  date_label: string;
  date: string;
  transactions: TransactionData[];
}

export interface ReviewQueueResponse {
  groups: DateGroupedTransactions[];
  total_count: number;
  displayed_count: number;
  has_more: boolean;
}

export interface BulkOperationRequest {
  transaction_ids: string[];
  operation: 'mark_reviewed' | 'set_category' | 'add_note';
  category_id?: string;
  note?: string;
}

export interface BulkOperationResponse {
  success: boolean;
  affected_count: number;
  operation: string;
  transaction_ids: string[];
}

// API Functions
export async function fetchReviewQueue(
  limit = 50,
  offset = 0
): Promise<ReviewQueueResponse> {
  return fetchApi(`/api/transactions/review-queue?limit=${limit}&offset=${offset}`);
}

export async function fetchReviewQueueCount(): Promise<{ count: number }> {
  return fetchApi('/api/transactions/review-queue/count');
}

export async function bulkUpdateTransactions(
  request: BulkOperationRequest
): Promise<BulkOperationResponse> {
  return fetchApi('/api/transactions/bulk', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}
```

### 2. Update TransactionReview Component

Replace mock data with real API calls:

```typescript
const [queue, setQueue] = useState<ReviewQueueResponse | null>(null);
const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

useEffect(() => {
  fetchReviewQueue(5).then(setQueue);
}, []);

const handleBulkReview = async () => {
  await bulkUpdateTransactions({
    transaction_ids: Array.from(selectedIds),
    operation: 'mark_reviewed',
  });
  // Refresh queue
  setSelectedIds(new Set());
  fetchReviewQueue(5).then(setQueue);
};
```

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/test_review_queue.py -v
pytest tests/test_bulk_operations.py -v
```

Key test cases:
- Review queue returns grouped transactions
- Bulk mark_reviewed updates all atomically
- Bulk set_category validates category exists
- Bulk add_note appends to existing notes
- Operations rollback on failure

### Manual Testing

1. **Review Queue**
   ```bash
   curl http://localhost:8000/api/transactions/review-queue?limit=10
   ```

2. **Bulk Mark Reviewed**
   ```bash
   curl -X POST http://localhost:8000/api/transactions/bulk \
     -H "Content-Type: application/json" \
     -d '{"transaction_ids": ["id1", "id2"], "operation": "mark_reviewed"}'
   ```

3. **Bulk Set Category**
   ```bash
   curl -X POST http://localhost:8000/api/transactions/bulk \
     -H "Content-Type: application/json" \
     -d '{"transaction_ids": ["id1"], "operation": "set_category", "category_id": "cat-uuid"}'
   ```

---

## Routing Setup

Add to `frontend/App.tsx`:

```typescript
import ReviewPage from './components/ReviewPage';

// In routes
<Route path="/review" element={<ReviewPage />} />
```

Add sidebar navigation link to Review page.

---

## Key Implementation Notes

1. **Atomicity**: All bulk operations must be wrapped in transactions
2. **Date Labels**: Use `date.today()` comparison for "Today"/"Yesterday"
3. **Notes Append**: Use `\n` separator when appending to existing notes
4. **Indeterminate Checkbox**: Use `ref.current.indeterminate = true`
5. **Max Limit**: Enforce 500 transaction limit on bulk operations

---

## File Checklist

Backend:
- [ ] `backend/app/models/review.py` - New models
- [ ] `backend/app/services/review_service.py` - New service
- [ ] `backend/app/routers/transactions.py` - Extended endpoints
- [ ] `backend/tests/test_review_queue.py` - Tests
- [ ] `backend/tests/test_bulk_operations.py` - Tests

Frontend:
- [ ] `frontend/src/services/api.ts` - Extended API functions
- [ ] `frontend/components/TransactionReview.tsx` - Updated widget
- [ ] `frontend/components/ReviewPage.tsx` - New page
- [ ] `frontend/components/ReviewActionBar.tsx` - New component
- [ ] `frontend/App.tsx` - Add route
