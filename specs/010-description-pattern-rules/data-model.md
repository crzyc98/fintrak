# Data Model: Description-Based Pattern Rules

**Feature**: 010-description-pattern-rules
**Date**: 2026-02-10

## New Entity: `description_pattern_rules`

| Field               | Type           | Constraints                                          | Description                                         |
| ------------------- | -------------- | ---------------------------------------------------- | --------------------------------------------------- |
| id                  | VARCHAR(36)    | PRIMARY KEY                                          | UUID identifier                                     |
| account_id          | VARCHAR(36)    | NOT NULL, FK → accounts(id)                          | The account this rule is scoped to                  |
| description_pattern | VARCHAR(500)   | NOT NULL                                             | Generalized pattern with `*` wildcards (lowercase)  |
| category_id         | VARCHAR(36)    | NOT NULL, FK → categories(id)                        | Target category for matching transactions           |
| created_at          | TIMESTAMP      | NOT NULL, DEFAULT CURRENT_TIMESTAMP                  | When the rule was created or last updated           |

**Unique constraint**: `UNIQUE(account_id, description_pattern)`

**Indexes**:
- `idx_desc_pattern_rules_account` on `(account_id)` — for efficient lookup during categorization
- `idx_desc_pattern_rules_category` on `(category_id)` — for filtering rules by category

## Modified Entity: `transactions`

No schema changes. The existing `categorization_source VARCHAR(10)` field gains a new allowed value:

| Value       | Meaning                                        |
| ----------- | ---------------------------------------------- |
| `'rule'`    | Matched a merchant-based categorization rule   |
| `'ai'`      | AI categorization (Gemini)                     |
| `'manual'`  | User manually set category                     |
| `'import'`  | Category came from CSV import mapping          |
| `'desc_rule'` | **NEW** — Matched a description pattern rule |

## Relationships

```
accounts (1) ──→ (many) description_pattern_rules
categories (1) ──→ (many) description_pattern_rules
description_pattern_rules ──→ categorizes → transactions (via matching)
```

## Pattern Format

- Patterns are stored **lowercase** for case-insensitive matching.
- The `*` character represents a wildcard matching any sequence of characters.
- Examples:
  - `direct deposit fidelity bro* (cash)` — matches any "DIRECT DEPOSIT Fidelity Bro[numbers] (Cash)"
  - `check #* deposit` — matches any "CHECK #[number] DEPOSIT"
  - `atm` — exact match (no variable portions)

## Lifecycle

1. **Creation**: When a user manually corrects a transaction's category AND the transaction has no `normalized_merchant`, extract a pattern from the `description` field and create/update a rule scoped to the transaction's `account_id`.
2. **Matching**: During categorization, after merchant-rule matching fails, check the transaction's `description` against all description pattern rules for its `account_id`. First match (most recently created) wins.
3. **Update**: If a user re-categorizes a transaction that produces the same pattern + account_id, the existing rule's `category_id` and `created_at` are updated (upsert).
4. **Deletion**: User can delete a rule via API. Already-categorized transactions are not affected.
