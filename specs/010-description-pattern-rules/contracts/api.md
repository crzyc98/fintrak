# API Contracts: Description-Based Pattern Rules

**Feature**: 010-description-pattern-rules
**Date**: 2026-02-10

## Modified Endpoints

### PUT /api/transactions/{transaction_id}

**Change**: When category changes and `normalized_merchant` is null/empty, extract a description pattern and create a description pattern rule (in addition to existing behavior).

**No request/response schema changes** — the side effect happens internally.

**New side effect flow**:
1. Category changed? Yes
2. `normalized_merchant` present? → Create merchant rule (existing behavior)
3. `normalized_merchant` absent? → Extract pattern from `description`, create description pattern rule scoped to `account_id`

---

### GET /api/categorization/rules

**Change**: Response includes description pattern rules alongside merchant rules, with a new `rule_type` discriminator.

**Updated Response Model** — `CategorizationRuleListResponse`:

```json
{
  "rules": [
    {
      "id": "uuid",
      "merchant_pattern": "amazon",
      "category_id": "uuid",
      "category_name": "Shopping",
      "rule_type": "merchant",
      "account_id": null,
      "account_name": null,
      "created_at": "2026-02-10T12:00:00Z"
    },
    {
      "id": "uuid",
      "merchant_pattern": null,
      "description_pattern": "direct deposit fidelity bro* (cash)",
      "category_id": "uuid",
      "category_name": "Income",
      "rule_type": "description",
      "account_id": "uuid",
      "account_name": "Fidelity Cash",
      "created_at": "2026-02-10T12:00:00Z"
    }
  ],
  "total": 2,
  "has_more": false
}
```

**New fields on rule items**:
- `rule_type`: `"merchant"` | `"description"` — discriminator
- `description_pattern`: The wildcard pattern (null for merchant rules)
- `account_id`: The scoped account (null for merchant rules)
- `account_name`: Display name of the scoped account (null for merchant rules)

**New query parameter**:
- `rule_type` (optional): `"merchant"` | `"description"` | omit for both

---

### POST /api/categorization/rules

**Change**: Accept optional description pattern fields for manual rule creation.

**Updated Request Model** — `CategorizationRuleCreate`:

```json
{
  "merchant_pattern": "amazon",
  "category_id": "uuid"
}
```

OR (for description rules):

```json
{
  "description_pattern": "direct deposit fidelity bro* (cash)",
  "account_id": "uuid",
  "category_id": "uuid"
}
```

**Validation**:
- Exactly one of `merchant_pattern` or `description_pattern` must be provided
- `account_id` is required when `description_pattern` is provided
- `account_id` must be null/absent when `merchant_pattern` is provided

---

### DELETE /api/categorization/rules/{rule_id}

**Change**: Now also handles deletion of description pattern rules. The `rule_id` can refer to either a merchant rule or a description pattern rule.

**Lookup order**: Check `categorization_rules` first, then `description_pattern_rules`.

---

### POST /api/categorization/trigger

**Change**: The categorization pipeline now includes description-rule matching as a fallback step.

**Updated Response Model** — `CategorizationBatchResponse`:

```json
{
  "id": "uuid",
  "transaction_count": 100,
  "success_count": 80,
  "failure_count": 5,
  "rule_match_count": 30,
  "desc_rule_match_count": 15,
  "ai_match_count": 35,
  "skipped_count": 15,
  "duration_ms": 2500,
  "started_at": "2026-02-10T12:00:00Z",
  "completed_at": "2026-02-10T12:00:02Z"
}
```

**New field**: `desc_rule_match_count` — number of transactions matched by description pattern rules.

---

## New Endpoint

### POST /api/categorization/preview-pattern

**Purpose**: Preview the description pattern that would be extracted from a given description. Useful for debugging and understanding pattern extraction behavior.

**Request**:
```json
{
  "description": "DIRECT DEPOSIT Fidelity Bro461026 (Cash)"
}
```

**Response**:
```json
{
  "original": "DIRECT DEPOSIT Fidelity Bro461026 (Cash)",
  "pattern": "direct deposit fidelity bro* (cash)"
}
```
