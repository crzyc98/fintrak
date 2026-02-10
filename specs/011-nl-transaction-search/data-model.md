# Data Model: Natural Language Transaction Search

**Feature**: 011-nl-transaction-search
**Date**: 2026-02-09

## Overview

No new database tables or schema changes are required. This feature introduces new Pydantic models for the API request/response layer and a structured representation of AI-interpreted filters.

## New Models

### NLSearchRequest

Request body for the NL search endpoint.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | str (1-500 chars) | Yes | The natural language search query text |
| account_id | str | No | Manual account filter (takes precedence over NL) |
| category_id | str | No | Manual category filter (takes precedence over NL) |
| date_from | date | No | Manual start date filter (takes precedence over NL) |
| date_to | date | No | Manual end date filter (takes precedence over NL) |
| amount_min | int | No | Manual minimum amount in cents (takes precedence over NL) |
| amount_max | int | No | Manual maximum amount in cents (takes precedence over NL) |
| reviewed | bool | No | Manual review status filter |
| limit | int (1-200, default 50) | No | Pagination limit |
| offset | int (>=0, default 0) | No | Pagination offset |

### InterpretedFilters

Structured representation of what Gemini extracted from the NL query. All fields optional since any given query may only reference some dimensions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| date_from | date | No | Extracted start date |
| date_to | date | No | Extracted end date |
| amount_min | int | No | Extracted minimum amount (cents) |
| amount_max | int | No | Extracted maximum amount (cents) |
| category_ids | list[str] | No | Matched category IDs from user's category list |
| merchant_keywords | list[str] | No | Merchant name keywords including common abbreviations |
| description_keywords | list[str] | No | General search terms from the query |
| summary | str | No | Human-readable interpretation (e.g., "Coffee purchases, last 30 days") |

**Validation rules**:
- `date_from` must be <= `date_to` if both present
- `amount_min` must be <= `amount_max` if both present
- `category_ids` must be a subset of the user's actual category IDs (invalid IDs silently discarded)
- `merchant_keywords` and `description_keywords` each limited to 10 items, each item max 100 chars

### NLSearchResponse

Response from the NL search endpoint. Extends the existing `TransactionListResponse` with interpretation metadata.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | list[TransactionResponse] | Yes | Matching transactions |
| total | int | Yes | Total matching count |
| limit | int | Yes | Applied pagination limit |
| offset | int | Yes | Applied pagination offset |
| has_more | bool | Yes | Whether more results exist |
| interpretation | InterpretedFilters | No | What the AI understood (null on fallback) |
| fallback | bool | Yes | Whether basic text search was used instead of AI |
| fallback_reason | str | No | Why fallback was triggered (e.g., "AI service unavailable") |

## Existing Models (unchanged)

### TransactionFilters

Used internally to execute the merged query. No changes needed — the NL search service builds a `TransactionFilters` instance from the merged manual + AI filters.

### TransactionResponse

Returned within `NLSearchResponse.items`. No changes needed.

## Entity Relationships

```
NLSearchRequest (from frontend)
    │
    ├── query text → Gemini AI → InterpretedFilters
    │
    ├── manual filters ─┐
    │                    ├── merge (manual wins) → TransactionFilters
    │                    │
    └── InterpretedFilters ─┘
                                    │
                                    ↓
                            transaction_service.get_all(filters)
                                    │
                                    ↓
                            NLSearchResponse (items + interpretation metadata)
```
