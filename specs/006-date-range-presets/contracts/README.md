# API Contracts: Date Range Presets

## No New Contracts

This feature is **frontend-only** and uses existing API endpoints. No new contracts are defined.

## Existing Contract Used

The feature uses the existing transaction list endpoint with date filters:

```
GET /api/transactions?date_from={YYYY-MM-DD}&date_to={YYYY-MM-DD}
```

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `date_from` | string (YYYY-MM-DD) | Include transactions on or after this date |
| `date_to` | string (YYYY-MM-DD) | Include transactions on or before this date |

### Example Request

```
GET /api/transactions?date_from=2026-01-01&date_to=2026-01-31&limit=50
```

See `specs/002-transactions-core/contracts/transactions-api.yaml` for full API specification.
