# API Contracts: Rules (updated)

No new endpoints are needed. The existing endpoints are updated to include the `source` field.

## GET /api/categorization/rules

**Response** (updated — adds `source` field to each rule):

```json
[
  {
    "id": "uuid",
    "merchant_pattern": "starbucks",
    "category_id": "uuid",
    "category_name": "Dining Out",
    "rule_type": "merchant",
    "source": "ai",
    "created_at": "2026-02-11T12:00:00"
  },
  {
    "id": "uuid",
    "description_pattern": "transfer to *",
    "account_id": "uuid",
    "account_name": "Checking",
    "category_id": "uuid",
    "category_name": "Transfers",
    "rule_type": "description",
    "source": "manual",
    "created_at": "2026-02-11T12:00:00"
  }
]
```

## POST /api/categorization/rules

**Request** (unchanged — `source` defaults to `"manual"` for user-created rules):

```json
{
  "merchant_pattern": "starbucks",
  "category_id": "uuid"
}
```

## Batch stats (existing response — no changes needed)

The `categorization_batches` table already tracks `rule_matches` and `ai_matches`. Auto-created rules will naturally increase `rule_matches` on subsequent runs.
