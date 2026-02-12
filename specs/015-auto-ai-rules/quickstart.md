# Quickstart: Auto-Create Rules from AI Classifications

## What this feature does

After running AI classification, the system automatically creates categorization rules from high-confidence results (confidence >= 0.9). On subsequent classification runs, these rules handle previously-seen merchants/patterns instantly, without AI calls.

## How to test

1. Start the app: `./fintrak`
2. Import a CSV with transactions from recognizable merchants (Starbucks, Amazon, etc.)
3. Run AI classification from the Settings page
4. Check the rules list — new rules should appear with source "ai"
5. Import another CSV with transactions from the same merchants
6. Run classification again — observe that those merchants are now handled by rules (check batch stats for `rule_matches` increase)

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| AUTO_RULE_CONFIDENCE_THRESHOLD | 0.9 | Minimum confidence to auto-create a rule |

## Key files

| File | Purpose |
|------|---------|
| `backend/app/services/categorization_service.py` | Main change — auto-rule creation in `apply_unified_results()` |
| `backend/app/config.py` | New threshold configuration |
| `backend/app/database.py` | Schema migration (add `source` column) |
| `backend/app/models/categorization.py` | Updated Pydantic models with `source` field |
| `backend/app/services/rule_service.py` | Updated `create_rule()` to accept `source` |
| `backend/app/services/desc_rule_service.py` | Updated `create_rule()` to accept `source` |
