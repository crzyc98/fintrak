# Quickstart: Transactions Core

**Feature**: 002-transactions-core
**Date**: 2026-01-11

## Prerequisites

- Docker and Docker Compose installed
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)
- Git

## Development Setup

### 1. Start the Development Environment

```bash
# From repository root
docker-compose up -d

# Or run services separately:
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### 2. Verify Services

```bash
# Backend health check
curl http://localhost:8000/api/health

# Frontend (open in browser)
open http://localhost:5173
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run only transaction tests
pytest tests/test_transactions.py -v

# Run specific test
pytest tests/test_transactions.py::test_list_transactions -v
```

### Frontend Tests

```bash
cd frontend

# Run tests (when configured)
npm test

# Type checking
npm run typecheck
```

## API Testing Examples

### List Transactions

```bash
# All transactions (paginated)
curl "http://localhost:8000/api/transactions"

# Filter by account
curl "http://localhost:8000/api/transactions?account_id=<uuid>"

# Filter by date range
curl "http://localhost:8000/api/transactions?date_from=2026-01-01&date_to=2026-01-31"

# Filter by amount range (in cents)
curl "http://localhost:8000/api/transactions?amount_min=-10000&amount_max=0"

# Search by description
curl "http://localhost:8000/api/transactions?search=grocery"

# Filter unreviewed only
curl "http://localhost:8000/api/transactions?reviewed=false"

# Pagination
curl "http://localhost:8000/api/transactions?limit=20&offset=40"

# Combined filters
curl "http://localhost:8000/api/transactions?account_id=<uuid>&reviewed=false&limit=100"
```

### Get Single Transaction

```bash
curl "http://localhost:8000/api/transactions/<transaction_id>"
```

### Update Transaction

```bash
# Update category
curl -X PUT "http://localhost:8000/api/transactions/<transaction_id>" \
  -H "Content-Type: application/json" \
  -d '{"category_id": "<category_uuid>"}'

# Mark as reviewed
curl -X PUT "http://localhost:8000/api/transactions/<transaction_id>" \
  -H "Content-Type: application/json" \
  -d '{"reviewed": true}'

# Add notes
curl -X PUT "http://localhost:8000/api/transactions/<transaction_id>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Reimbursed by employer"}'

# Clear category (uncategorize)
curl -X PUT "http://localhost:8000/api/transactions/<transaction_id>" \
  -H "Content-Type: application/json" \
  -d '{"category_id": null}'

# Multiple updates at once
curl -X PUT "http://localhost:8000/api/transactions/<transaction_id>" \
  -H "Content-Type: application/json" \
  -d '{"category_id": "<uuid>", "reviewed": true, "notes": "Monthly subscription"}'
```

### Delete Transaction

```bash
curl -X DELETE "http://localhost:8000/api/transactions/<transaction_id>"
```

## Database Access

### DuckDB CLI

```bash
# Connect to database (Docker)
docker exec -it fintrak-backend duckdb /data/fintrak.duckdb

# Or locally
duckdb backend/data/fintrak.duckdb
```

### Useful Queries

```sql
-- List all transactions
SELECT * FROM transactions ORDER BY date DESC LIMIT 10;

-- Count transactions by account
SELECT a.name, COUNT(t.id) as count
FROM accounts a
LEFT JOIN transactions t ON t.account_id = a.id
GROUP BY a.id, a.name;

-- Sum by category
SELECT c.name, c.emoji, SUM(t.amount) / 100.0 as total
FROM transactions t
JOIN categories c ON t.category_id = c.id
GROUP BY c.id, c.name, c.emoji
ORDER BY total;

-- Unreviewed transactions
SELECT date, description, amount / 100.0 as dollars
FROM transactions
WHERE reviewed = false
ORDER BY date DESC;

-- Check indexes
SELECT * FROM duckdb_indexes();
```

## File Structure Reference

```
backend/app/
├── models/
│   └── transaction.py      # Pydantic models
├── services/
│   └── transaction_service.py  # Business logic
├── routers/
│   └── transactions.py     # API endpoints
├── database.py             # Schema (transactions table)
└── main.py                 # Router registration

frontend/
├── components/
│   ├── TransactionsView.tsx    # Main list view
│   └── forms/
│       └── TransactionEditForm.tsx  # Edit modal/popover
├── src/services/
│   └── api.ts              # API client functions
└── types.ts                # TypeScript types
```

## Common Development Tasks

### Add Test Data

```python
# In Python REPL or test file
from app.services.transaction_service import TransactionService
from app.models.transaction import TransactionCreate
from datetime import date

service = TransactionService()

# Create test transaction
tx = TransactionCreate(
    account_id="<existing_account_uuid>",
    date=date.today(),
    description="Test Transaction",
    original_description="TEST TRANSACTION 12345",
    amount=-1500,  # -$15.00
    category_id=None,
    reviewed=False,
    notes=None
)
result = service.create(tx)
print(f"Created: {result.id}")
```

### Reset Database

```bash
# Remove and recreate database
rm backend/data/fintrak.duckdb
# Restart backend to reinitialize tables
```

### View API Documentation

Open http://localhost:8000/docs for interactive Swagger UI (auto-generated by FastAPI).

## Troubleshooting

### "Foreign key constraint failed"

- Ensure account_id references an existing account
- Ensure category_id references an existing category (or is null)

### "Transaction not found" on update/delete

- Verify the transaction ID exists
- Check for typos in UUID format

### Slow queries

- Check that indexes exist: `SELECT * FROM duckdb_indexes();`
- Verify server-side filtering is being used (check query params in network tab)

### Frontend not updating after edit

- Check browser console for API errors
- Verify the PUT request returns 200
- Check that state is being updated after successful response
