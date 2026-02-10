# API Contract: Spending Insights

**Feature Branch**: `009-ai-spending-insights`
**Date**: 2026-02-10

## POST /api/insights/generate

Generate AI-powered spending insights for a given time period.

### Request

```json
{
  "period": "current_month",
  "type": "summary"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| period | string | Yes | One of: `current_month`, `last_month`, `custom` |
| type | string | Yes | One of: `summary` (P1 quick summary), `report` (P3 full report) |
| date_from | string (YYYY-MM-DD) | Only if period=custom | Custom period start date |
| date_to | string (YYYY-MM-DD) | Only if period=custom | Custom period end date |

### Response (200 OK)

```json
{
  "period_start": "2026-02-01",
  "period_end": "2026-02-10",
  "total_spending_cents": 245000,
  "total_transactions": 47,
  "uncategorized_count": 3,
  "summary": "This month, you've spent $2,450.00 across 8 categories. Your top spending category is Dining at $680.00, followed by Groceries at $520.00. Compared to January, your overall spending is up 12%, driven primarily by a 35% increase in Dining.",
  "top_categories": [
    {
      "category_id": "cat-123",
      "category_name": "Dining",
      "category_emoji": "🍽️",
      "total_amount_cents": 68000,
      "transaction_count": 12,
      "previous_period_amount_cents": 50370,
      "change_percentage": 35.0
    },
    {
      "category_id": "cat-456",
      "category_name": "Groceries",
      "category_emoji": "🛒",
      "total_amount_cents": 52000,
      "transaction_count": 8,
      "previous_period_amount_cents": 48000,
      "change_percentage": 8.3
    }
  ],
  "anomalies": [
    {
      "transaction_id": "txn-789",
      "transaction_date": "2026-02-05",
      "description": "Best Buy Electronics",
      "merchant": "Best Buy",
      "amount_cents": 45000,
      "category_name": "Shopping",
      "category_avg_cents": 12000,
      "deviation_factor": 3.75
    }
  ],
  "anomaly_explanations": "You had an unusually large purchase of $450.00 at Best Buy — your average Shopping transaction over the past 3 months is $120.00.",
  "suggestions": [
    "Consider reviewing your Dining spending — it's up 35% from last month.",
    "You have 3 uncategorized transactions this month. Categorizing them will improve future insights."
  ],
  "generated_at": "2026-02-10T14:30:00Z"
}
```

### Response (200 OK — Insufficient Data)

When fewer than 5 categorized transactions exist for the period:

```json
{
  "period_start": "2026-02-01",
  "period_end": "2026-02-10",
  "total_spending_cents": 15000,
  "total_transactions": 3,
  "uncategorized_count": 0,
  "summary": null,
  "top_categories": [],
  "anomalies": [],
  "anomaly_explanations": null,
  "suggestions": [],
  "generated_at": "2026-02-10T14:30:00Z",
  "insufficient_data": true,
  "insufficient_data_message": "You have only 3 categorized transactions this month. We need at least 5 to generate meaningful insights. Keep adding transactions and check back soon!"
}
```

### Response (422 Validation Error)

When `period=custom` but `date_from` or `date_to` is missing:

```json
{
  "detail": [
    {
      "loc": ["body", "date_from"],
      "msg": "date_from is required when period is 'custom'",
      "type": "value_error"
    }
  ]
}
```

### Response (503 Service Unavailable)

When Gemini API is unavailable after retries:

```json
{
  "detail": "AI service is temporarily unavailable. Please try again in a few minutes."
}
```

### Response (429 Too Many Requests)

When cooldown period has not elapsed (within 30 seconds of last request):

```json
{
  "detail": "Please wait before generating new insights.",
  "retry_after_seconds": 18
}
```

## Frontend API Function

```typescript
// Types
interface InsightRequest {
  period: 'current_month' | 'last_month' | 'custom';
  type: 'summary' | 'report';
  date_from?: string;
  date_to?: string;
}

interface CategorySpending {
  category_id: string;
  category_name: string;
  category_emoji: string;
  total_amount_cents: number;
  transaction_count: number;
  previous_period_amount_cents: number | null;
  change_percentage: number | null;
}

interface Anomaly {
  transaction_id: string;
  transaction_date: string;
  description: string;
  merchant: string;
  amount_cents: number;
  category_name: string;
  category_avg_cents: number;
  deviation_factor: number;
}

interface InsightResponse {
  period_start: string;
  period_end: string;
  total_spending_cents: number;
  total_transactions: number;
  uncategorized_count: number;
  summary: string | null;
  top_categories: CategorySpending[];
  anomalies: Anomaly[];
  anomaly_explanations: string | null;
  suggestions: string[];
  generated_at: string;
  insufficient_data?: boolean;
  insufficient_data_message?: string;
}

// API function
async function generateInsights(request: InsightRequest): Promise<InsightResponse> {
  // POST /api/insights/generate
}
```
