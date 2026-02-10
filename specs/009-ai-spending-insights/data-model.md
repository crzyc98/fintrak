# Data Model: AI Spending Insights

**Feature Branch**: `009-ai-spending-insights`
**Date**: 2026-02-10

## Overview

This feature does **not** introduce new database tables. Insights are ephemeral (generated fresh per request, never persisted). All data comes from existing tables: `transactions`, `categories`, and `accounts`.

## Existing Entities Used

### transactions (existing table)
| Field | Type | Usage in Insights |
|-------|------|-------------------|
| id | VARCHAR(36) PK | Anomaly reference |
| account_id | VARCHAR(36) FK | Scoping queries |
| date | DATE | Period filtering |
| description | VARCHAR(500) | Anomaly display |
| amount | INTEGER (cents) | Spending aggregation |
| category_id | VARCHAR(36) FK | Category grouping |
| reviewed | BOOLEAN | Not used directly |
| normalized_merchant | VARCHAR(255) | Merchant identification in anomalies |
| categorization_source | VARCHAR(10) | Filter to categorized only |

### categories (existing table)
| Field | Type | Usage in Insights |
|-------|------|-------------------|
| id | VARCHAR(36) PK | Join with transactions |
| name | VARCHAR(100) | Category labels in summaries |
| emoji | VARCHAR(10) | Display alongside category names |
| parent_id | VARCHAR(36) FK | Group subcategories under parent |
| group_name | VARCHAR(20) | Distinguish INCOME vs ESSENTIAL/LIFESTYLE/etc. |

### accounts (existing table)
| Field | Type | Usage in Insights |
|-------|------|-------------------|
| id | VARCHAR(36) PK | Join with transactions |
| name | VARCHAR(100) | Account context in anomalies |
| is_asset | BOOLEAN | Filter to spending accounts (non-asset) |

## Computed Data Structures (In-Memory Only)

### CategorySpendingSummary
Aggregated per category for a given period.

| Field | Type | Description |
|-------|------|-------------|
| category_id | string | Category identifier |
| category_name | string | Display name |
| category_emoji | string | Emoji for display |
| total_amount_cents | integer | Total spending in cents (absolute value of negative transactions) |
| transaction_count | integer | Number of transactions |
| previous_period_amount_cents | integer | Same metric for prior period (null if no prior data) |
| change_percentage | float | Percentage change from prior period (null if no prior data) |

### AnomalyCandidate
Individual transactions flagged as unusual.

| Field | Type | Description |
|-------|------|-------------|
| transaction_id | string | Reference to transaction |
| transaction_date | date | When it occurred |
| description | string | Transaction description |
| merchant | string | Normalized merchant name |
| amount_cents | integer | Transaction amount |
| category_name | string | Category the transaction belongs to |
| category_avg_cents | integer | Average transaction in this category (past 3 months) |
| deviation_factor | float | How many times above average (e.g., 3.5x) |

### InsightResponse
The structured response returned by the API endpoint.

| Field | Type | Description |
|-------|------|-------------|
| period_start | date | Start of analyzed period |
| period_end | date | End of analyzed period |
| total_spending_cents | integer | Total spending for the period |
| total_transactions | integer | Count of categorized transactions |
| uncategorized_count | integer | Count of uncategorized transactions (for warning) |
| summary | string | AI-generated plain-English spending summary |
| top_categories | CategorySpendingSummary[] | Top 5 categories by spending amount |
| anomalies | AnomalyCandidate[] | Transactions flagged as unusual (may be empty) |
| anomaly_explanations | string | AI-generated explanation of anomalies (null if none) |
| suggestions | string[] | AI-generated actionable suggestions |
| generated_at | datetime | Timestamp of generation |

## Key SQL Queries

### Category spending totals for a period
```sql
SELECT
    t.category_id,
    c.name AS category_name,
    c.emoji AS category_emoji,
    SUM(ABS(t.amount)) AS total_amount_cents,
    COUNT(*) AS transaction_count
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.date >= ? AND t.date <= ?
  AND t.amount < 0  -- expenses only
  AND t.category_id IS NOT NULL
GROUP BY t.category_id, c.name, c.emoji
ORDER BY total_amount_cents DESC
```

### Category averages over past 3 months (for anomaly detection)
```sql
SELECT
    t.category_id,
    c.name AS category_name,
    AVG(ABS(t.amount)) AS avg_amount_cents
FROM transactions t
JOIN categories c ON t.category_id = c.id
WHERE t.date >= ? AND t.date <= ?
  AND t.amount < 0
  AND t.category_id IS NOT NULL
GROUP BY t.category_id, c.name
HAVING COUNT(*) >= 3  -- need enough data for meaningful average
```

### Anomaly candidates (transactions exceeding 3x category average)
```sql
WITH category_avgs AS (
    SELECT category_id, AVG(ABS(amount)) AS avg_amount
    FROM transactions
    WHERE date >= ? AND date <= ?
      AND amount < 0
      AND category_id IS NOT NULL
    GROUP BY category_id
    HAVING COUNT(*) >= 3
)
SELECT
    t.id, t.date, t.description, t.normalized_merchant,
    t.amount, t.category_id,
    c.name AS category_name,
    ca.avg_amount AS category_avg,
    ABS(t.amount) / ca.avg_amount AS deviation_factor
FROM transactions t
JOIN categories c ON t.category_id = c.id
JOIN category_avgs ca ON t.category_id = ca.category_id
WHERE t.date >= ? AND t.date <= ?
  AND t.amount < 0
  AND ABS(t.amount) > ca.avg_amount * 3
ORDER BY deviation_factor DESC
LIMIT 10
```

### Uncategorized transaction count
```sql
SELECT COUNT(*)
FROM transactions
WHERE date >= ? AND date <= ?
  AND category_id IS NULL
```
