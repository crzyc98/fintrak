# Quickstart: AI Spending Insights

**Feature Branch**: `009-ai-spending-insights`
**Date**: 2026-02-10

## Prerequisites

- Python 3.12, Node.js with npm
- `GEMINI_API_KEY` environment variable set
- Existing transaction data in DuckDB (categorized transactions required)

## Setup

```bash
# Switch to feature branch
git checkout 009-ai-spending-insights

# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

## Development

```bash
# Start both servers
./fintrak

# Or individually:
cd backend && uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev
```

## Feature Files

### Backend (new)
- `backend/app/routers/insights.py` — POST /api/insights/generate endpoint
- `backend/app/services/insights_service.py` — Data aggregation + Gemini prompt orchestration
- `backend/app/models/insights.py` — Pydantic request/response models

### Backend (modified)
- `backend/app/main.py` — Register insights router
- `backend/app/services/gemini_client.py` — May add a non-JSON invoke variant for natural language

### Frontend (new)
- `frontend/components/SpendingInsights.tsx` — Dashboard card component

### Frontend (modified)
- `frontend/components/Dashboard.tsx` — Add SpendingInsights card to grid
- `frontend/src/services/api.ts` — Add `generateInsights()` API function and types

## Testing

```bash
# Backend unit tests
cd backend && pytest tests/test_insights_service.py -v

# Backend endpoint tests
cd backend && pytest tests/test_insights_router.py -v

# Frontend type checking
cd frontend && npx tsc --noEmit

# Manual E2E test
# 1. Ensure you have 5+ categorized transactions for the current month
# 2. Open dashboard at http://localhost:5173
# 3. Find the Insights card
# 4. Click "Generate Insights"
# 5. Verify summary text appears with correct category data
# 6. Try clicking again immediately — should see cooldown indicator
```

## API Quick Test

```bash
# Generate a summary
curl -X POST http://localhost:8000/api/insights/generate \
  -H "Content-Type: application/json" \
  -d '{"period": "current_month", "type": "summary"}'

# Generate a full report
curl -X POST http://localhost:8000/api/insights/generate \
  -H "Content-Type: application/json" \
  -d '{"period": "last_month", "type": "report"}'
```

## Key Implementation Notes

- All amounts in the database are **integer cents** — divide by 100 for display
- Transaction amounts: negative = expenses, positive = income
- Only use `category_id IS NOT NULL` transactions for insights
- Anomaly threshold: transaction amount > 3x category average over past 3 months
- Gemini is called with `response_mime_type="application/json"` for structured output
- 30-second cooldown between generations (enforced client-side with disabled button + countdown)
