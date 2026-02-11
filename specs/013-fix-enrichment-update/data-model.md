# Data Model: Fix Enrichment Update Failure

**Feature**: 013-fix-enrichment-update
**Date**: 2026-02-11

## Entities

### Transaction (existing — no schema changes)

The `transactions` table is not modified by this feature. The fix is purely in the data access layer (Python service code).

| Field | Type | Notes |
| ----- | ---- | ----- |
| id | VARCHAR(36) | PK, UUID |
| account_id | VARCHAR(36) | FK → accounts |
| date | DATE | Transaction date |
| description | VARCHAR(500) | Display description |
| original_description | VARCHAR(500) | Raw imported description |
| amount | INTEGER | Amount in cents |
| category_id | VARCHAR(36) | FK → categories, nullable |
| reviewed | BOOLEAN | Default FALSE |
| reviewed_at | TIMESTAMP | Nullable |
| notes | TEXT | Nullable |
| normalized_merchant | VARCHAR(255) | AI-normalized merchant name |
| confidence_score | DECIMAL(3,2) | AI categorization confidence |
| categorization_source | VARCHAR(10) | 'ai', 'rule', 'manual' |
| subcategory | VARCHAR(100) | AI-assigned subcategory |
| is_discretionary | BOOLEAN | AI-classified essential/discretionary |
| enrichment_source | VARCHAR(10) | 'ai' when enriched |
| created_at | TIMESTAMP | Auto-set on insert |

### Indexes on transactions (existing — no changes)

1. PRIMARY KEY on `id`
2. `idx_transactions_account_date` on `(account_id, date DESC)`
3. `idx_transactions_category` on `(category_id)`
4. `idx_transactions_reviewed` on `(reviewed)`
5. `idx_transactions_normalized_merchant` on `(normalized_merchant)`
6. `idx_transactions_categorization_source` on `(categorization_source)`
7. `idx_transactions_enrichment_source` on `(enrichment_source)`

## State Transitions

No state transitions affected. The enrichment flow remains:
1. Transaction starts with `enrichment_source IS NULL`
2. After enrichment: `enrichment_source = 'ai'`, plus `subcategory`, `is_discretionary`, and optionally `normalized_merchant` are set

## Schema Changes

**None.** This is a code-only fix in the data access layer.
