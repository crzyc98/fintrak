# Quickstart: AI-Powered Transaction Categorization

**Feature**: 003-ai-categorization
**Date**: 2026-01-11

## Prerequisites

1. **FinTrack backend running** (FastAPI on port 8000)
2. **Claude Code CLI installed** and accessible as `claude` in PATH
3. **Categories exist** in the system (at least one category for testing)
4. **Transactions imported** (at least some uncategorized transactions)

## Environment Setup

```bash
# Optional: Configure via environment variables (defaults shown)
export CLAUDE_CODE_PATH="claude"
export CATEGORIZATION_BATCH_SIZE="50"
export CATEGORIZATION_CONFIDENCE_THRESHOLD="0.7"
export CATEGORIZATION_TIMEOUT_SECONDS="120"
```

## Quick Test

### 1. Verify Claude CLI Access

```bash
# Should return a response (any response confirms CLI is working)
echo "Say hello" | claude -p
```

### 2. Check Uncategorized Transactions

```bash
# List transactions without categories
curl "http://localhost:8000/api/transactions?category_id=null&limit=5" | jq
```

### 3. Trigger Categorization

```bash
# Trigger AI categorization for all uncategorized transactions
curl -X POST "http://localhost:8000/api/categorization/trigger" | jq
```

Expected response:
```json
{
  "id": "batch-uuid",
  "transaction_count": 10,
  "success_count": 8,
  "failure_count": 0,
  "rule_match_count": 2,
  "ai_match_count": 6,
  "skipped_count": 2,
  "duration_ms": 5432,
  "started_at": "2026-01-11T10:00:00Z",
  "completed_at": "2026-01-11T10:00:05Z"
}
```

### 4. Verify Categorization Results

```bash
# Check that transactions now have categories
curl "http://localhost:8000/api/transactions?limit=5" | jq '.transactions[] | {description, category_name, categorization_source, confidence_score}'
```

### 5. Test Rule Learning

```bash
# Update a transaction's category (creates a rule)
curl -X PUT "http://localhost:8000/api/transactions/{transaction_id}" \
  -H "Content-Type: application/json" \
  -d '{"category_id": "your-category-uuid"}'

# Verify rule was created
curl "http://localhost:8000/api/categorization/rules" | jq
```

### 6. Test Merchant Normalization

```bash
# Preview normalization for a raw description
curl -X POST "http://localhost:8000/api/categorization/normalize" \
  -H "Content-Type: application/json" \
  -d '{"description": "POS DEBIT 1234 STARBUCKS #5678 SEATTLE WA 98101"}' | jq

# Expected output:
# {
#   "original": "POS DEBIT 1234 STARBUCKS #5678 SEATTLE WA 98101",
#   "normalized": "starbucks",
#   "tokens_removed": ["POS DEBIT", "1234", "#5678", "SEATTLE WA 98101"]
# }
```

## Common Workflows

### Import → Auto-Categorize Flow

1. Import CSV via existing import endpoint (when implemented)
2. System automatically triggers categorization post-import
3. Rules are applied first (instant, no AI call)
4. Remaining transactions sent to AI in batches of 50
5. Results logged to categorization_batches table

### Manual Correction Flow

1. User views transaction in UI
2. User changes category from "Restaurants" to "Coffee"
3. System records rule: `starbucks` → `Coffee` category
4. Future imports with "STARBUCKS" auto-categorize without AI

### View Processing History

```bash
# Get last 10 categorization batches
curl "http://localhost:8000/api/categorization/batches?limit=10" | jq
```

### Manage Rules

```bash
# List all rules
curl "http://localhost:8000/api/categorization/rules" | jq

# Delete a rule
curl -X DELETE "http://localhost:8000/api/categorization/rules/{rule_id}"

# Create a rule manually
curl -X POST "http://localhost:8000/api/categorization/rules" \
  -H "Content-Type: application/json" \
  -d '{"merchant_pattern": "amazon", "category_id": "shopping-category-uuid"}'
```

## Troubleshooting

### AI Categorization Not Working

1. **Check Claude CLI**: `which claude` and `claude --version`
2. **Check timeout**: Increase `CATEGORIZATION_TIMEOUT_SECONDS` if batches are timing out
3. **Check logs**: Backend logs show batch processing details
4. **Check batch history**: `GET /api/categorization/batches` shows error_message for failures

### Low Confidence Scores

1. **Improve prompts**: Category names should be descriptive
2. **Add category descriptions**: Help AI understand category intent
3. **Lower threshold**: Reduce `CATEGORIZATION_CONFIDENCE_THRESHOLD` (not recommended below 0.5)

### Rules Not Matching

1. **Check normalization**: Use `/api/categorization/normalize` to see how merchants are normalized
2. **Verify rule pattern**: Rule patterns are substring matches, case-insensitive
3. **Check rule order**: Most recent rule wins on conflicts

## Testing

```bash
# Run backend tests
cd backend
pytest tests/test_categorization.py -v
pytest tests/test_merchant_normalizer.py -v
pytest tests/test_claude_client.py -v
```

## Performance Notes

- **Batch size 50**: Balances prompt length vs. number of API calls
- **120s timeout**: Accommodates large batches with complex categories
- **Rules first**: Deterministic rules bypass AI entirely, improving speed
- **Graceful degradation**: AI failures don't block import completion
