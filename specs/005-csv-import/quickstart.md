# Quickstart: CSV Import

**Feature**: 005-csv-import | **Date**: 2026-01-12

## Prerequisites

- Python 3.11+ with pip
- Node.js 18+ with npm
- DuckDB database initialized (`fintrak.duckdb`)

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt

# Run migrations (add csv_column_mapping to accounts)
# Note: Schema change handled in database.py init_db()

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Quick Test

### 1. Create test CSV file

```csv
Date,Description,Amount
2024-01-15,Coffee Shop,-4.50
2024-01-15,Salary Deposit,3000.00
2024-01-16,Grocery Store,-45.23
```

### 2. Import via UI

1. Open http://localhost:5173
2. Navigate to Accounts tab
3. Select an account (or create one first)
4. Drag & drop the CSV file onto the drop zone
5. Configure column mapping (Date, Description, Amount)
6. Preview transactions
7. Confirm import

### 3. Import via API

```bash
# Preview CSV
curl -X POST http://localhost:8000/api/import/preview \
  -H "Content-Type: application/json" \
  -d '{"file_content": "RGF0ZSxEZXNjcmlwdGlvbixBbW91bnQKMjAyNC0wMS0xNSxDb2ZmZWUgU2hvcCwtNC41MAoyMDI0LTAxLTE1LFNhbGFyeSBEZXBvc2l0LDMwMDAuMDAKMjAyNC0wMS0xNixHcm9jZXJ5IFN0b3JlLC00NS4yMw=="}'

# Parse with mapping
curl -X POST http://localhost:8000/api/import/parse \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "YOUR_ACCOUNT_ID",
    "file_content": "RGF0ZSxEZXNjcmlwdGlvbixBbW91bnQKMjAyNC0wMS0xNSxDb2ZmZWUgU2hvcCwtNC41MAoyMDI0LTAxLTE1LFNhbGFyeSBEZXBvc2l0LDMwMDAuMDAKMjAyNC0wMS0xNixHcm9jZXJ5IFN0b3JlLC00NS4yMw==",
    "mapping": {
      "date_column": "Date",
      "description_column": "Description",
      "amount_mode": "single",
      "amount_column": "Amount",
      "date_format": "YYYY-MM-DD"
    }
  }'

# Create transactions
curl -X POST http://localhost:8000/api/import/transactions \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "YOUR_ACCOUNT_ID",
    "transactions": [...],
    "save_mapping": true,
    "mapping": {...}
  }'
```

## Key Files

| Purpose | Location |
|---------|----------|
| Import router | `backend/app/routers/csv_import.py` |
| Import service | `backend/app/services/csv_import_service.py` |
| Import models | `backend/app/models/csv_import.py` |
| Drop zone component | `frontend/components/CsvDropZone.tsx` |
| Column mapper | `frontend/components/CsvColumnMapper.tsx` |
| Import preview | `frontend/components/CsvImportPreview.tsx` |
| API client | `frontend/src/services/api.ts` |

## Common Issues

### "Invalid CSV format"
- Ensure file is UTF-8 encoded
- Check for consistent delimiter (comma, semicolon, tab)
- Verify all rows have same number of columns

### "Date parse error"
- Select correct date format in mapper
- Check for empty date cells in CSV

### "Duplicate detected"
- Review duplicates in preview
- Choose to include or exclude before confirming

## Running Tests

```bash
# Backend tests
cd backend
pytest tests/test_csv_import.py -v

# Frontend tests (when implemented)
cd frontend
npm test
```
