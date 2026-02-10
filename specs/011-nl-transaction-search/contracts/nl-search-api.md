# API Contract: Natural Language Transaction Search

**Feature**: 011-nl-transaction-search
**Date**: 2026-02-09

## Endpoints

### POST /api/transactions/nl-search

Interpret a natural language query and return matching transactions.

#### Request

**Content-Type**: `application/json`

```json
{
  "query": "coffee purchases last month",
  "account_id": null,
  "category_id": null,
  "date_from": null,
  "date_to": null,
  "amount_min": null,
  "amount_max": null,
  "reviewed": null,
  "limit": 50,
  "offset": 0
}
```

| Field | Type | Required | Validation | Description |
|-------|------|----------|------------|-------------|
| query | string | Yes | 1-500 chars, non-empty | Natural language search query |
| account_id | string | No | Valid UUID | Manual account filter |
| category_id | string | No | Valid UUID or "__uncategorized__" | Manual category filter |
| date_from | string | No | ISO date (YYYY-MM-DD) | Manual start date |
| date_to | string | No | ISO date (YYYY-MM-DD) | Manual end date |
| amount_min | integer | No | Cents | Manual minimum amount |
| amount_max | integer | No | Cents | Manual maximum amount |
| reviewed | boolean | No | | Manual review status filter |
| limit | integer | No | 1-200, default 50 | Results per page |
| offset | integer | No | >= 0, default 0 | Pagination offset |

#### Response (200 OK)

```json
{
  "items": [
    {
      "id": "abc-123",
      "account_id": "acc-456",
      "date": "2026-01-15",
      "description": "STARBUCKS COFFEE #1234",
      "original_description": "STARBUCKS COFFEE #1234",
      "amount": -550,
      "category_id": "cat-789",
      "reviewed": false,
      "reviewed_at": null,
      "notes": null,
      "created_at": "2026-01-15T10:30:00",
      "normalized_merchant": "Starbucks",
      "confidence_score": 0.95,
      "categorization_source": "ai",
      "account_name": "Chase Sapphire",
      "category_name": "Coffee & Tea",
      "category_emoji": "☕"
    }
  ],
  "total": 12,
  "limit": 50,
  "offset": 0,
  "has_more": false,
  "interpretation": {
    "date_from": "2026-01-01",
    "date_to": "2026-01-31",
    "amount_min": null,
    "amount_max": null,
    "category_ids": ["cat-789"],
    "merchant_keywords": ["starbucks", "coffee", "sbux", "peets", "blue bottle"],
    "description_keywords": ["coffee"],
    "summary": "Coffee purchases in January 2026"
  },
  "fallback": false,
  "fallback_reason": null
}
```

#### Response (200 OK — Fallback Mode)

When AI is unavailable, returns basic text search results:

```json
{
  "items": [...],
  "total": 5,
  "limit": 50,
  "offset": 0,
  "has_more": false,
  "interpretation": null,
  "fallback": true,
  "fallback_reason": "AI service unavailable — showing basic text search results"
}
```

#### Response (422 Unprocessable Entity)

Validation errors on the request body:

```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

#### Error Codes

| Status | Condition | Response |
|--------|-----------|----------|
| 200 | Success (AI or fallback) | NLSearchResponse |
| 422 | Invalid request body | Pydantic validation errors |
| 500 | Unexpected server error | `{"detail": "Internal server error"}` |

**Note**: AI failures do NOT produce error status codes. They trigger fallback mode and return 200 with `fallback: true`. This ensures the user always sees results.

## Filter Merge Behavior

When manual filters overlap with AI-interpreted filters:

| Scenario | Manual | NL-extracted | Applied |
|----------|--------|-------------|---------|
| Date conflict | date_from=2026-03-01 | date_from=2026-01-01 | 2026-03-01 (manual) |
| Amount conflict | amount_min=5000 | amount_min=10000 | 5000 (manual) |
| Category conflict | category_id=cat-1 | category_ids=[cat-2, cat-3] | cat-1 (manual) |
| No conflict | (none) | date_from=2026-01-01 | 2026-01-01 (NL) |
| Mixed | account_id=acc-1 | date_from=2026-01-01, keywords=["coffee"] | account_id=acc-1 (manual) + date + keywords (NL) |

Date range is treated as a single dimension: if either `date_from` or `date_to` is set manually, both NL date values are ignored.

Amount range is treated as a single dimension: if either `amount_min` or `amount_max` is set manually, both NL amount values are ignored.
