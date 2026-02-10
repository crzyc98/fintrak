# API Contract: Live Net Worth Dashboard

**Feature**: 008-live-networth | **Date**: 2026-02-09

## Overview

This feature requires **no new API endpoints**. It consumes the existing `GET /api/accounts` endpoint. This document records the contract for reference during implementation.

---

## Existing Endpoint: GET /api/accounts

**Router**: `backend/app/routers/accounts.py`
**URL**: `GET /api/accounts`
**Auth**: None (single-user app)

### Response

**Status**: `200 OK`
**Content-Type**: `application/json`
**Body**: `AccountResponse[]`

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Main Checking",
    "type": "Checking",
    "institution": "Chase",
    "is_asset": true,
    "current_balance": 1000000,
    "csv_column_mapping": null,
    "created_at": "2026-01-15T10:30:00"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Visa Card",
    "type": "Credit",
    "institution": "Capital One",
    "is_asset": false,
    "current_balance": 300000,
    "csv_column_mapping": null,
    "created_at": "2026-01-15T10:31:00"
  }
]
```

### Fields Used by NetWorth Component

| Field | Type | Usage |
|-------|------|-------|
| `is_asset` | boolean | Filter accounts into assets vs debts |
| `current_balance` | number \| null | Sum to compute totals (null → 0) |

### Error Responses

| Status | Condition | Frontend Handling |
|--------|-----------|-------------------|
| 200 | Success, empty array | Show $0 for all totals |
| 200 | Success, some null balances | Coalesce null to 0 in sum |
| 500 | Server error | Show error message in component |
| Network error | Backend unreachable | Show error message in component |

---

## Frontend API Function (Existing)

**File**: `frontend/src/services/api.ts`

```typescript
export async function fetchAccounts(): Promise<AccountData[]> {
  return fetchApi<AccountData[]>('/api/accounts');
}
```

No modifications needed.
