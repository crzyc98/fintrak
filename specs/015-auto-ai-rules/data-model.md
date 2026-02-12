# Data Model: Auto-Create Rules from AI Classifications

## Schema Changes

### Table: `categorization_rules` (existing — add column)

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| source | VARCHAR(10) | DEFAULT 'manual' | New column. Values: `'manual'`, `'ai'` |

### Table: `description_pattern_rules` (existing — add column)

| Column | Type | Constraint | Notes |
|--------|------|-----------|-------|
| source | VARCHAR(10) | DEFAULT 'manual' | New column. Values: `'manual'`, `'ai'` |

## Migration

Both tables need an `ALTER TABLE ADD COLUMN` in `init_db()`. DuckDB supports `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, so this is safe to run on existing databases. Existing rows will get the default value `'manual'`.

## Configuration

### New environment variable

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| AUTO_RULE_CONFIDENCE_THRESHOLD | float | 0.9 | Minimum AI confidence to auto-create a rule |

## Model Changes

### `CategorizationRuleCreate` — add optional field

- `source: Optional[str] = "manual"` — Rule origin (`"manual"` or `"ai"`)

### `DescriptionPatternRuleCreate` — add optional field

- `source: Optional[str] = "manual"` — Rule origin (`"manual"` or `"ai"`)

### `CategorizationRuleResponse` — add field

- `source: str = "manual"` — Rule origin for display/filtering

### `DescriptionPatternRuleResponse` — add field

- `source: str = "manual"` — Rule origin for display/filtering

## Entity Relationships (unchanged)

```
categorization_rules.category_id → categories.id
description_pattern_rules.category_id → categories.id
description_pattern_rules.account_id → accounts.id
```
