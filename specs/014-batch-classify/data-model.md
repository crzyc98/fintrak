# Data Model: Batch AI Classification

**Feature Branch**: `014-batch-classify`
**Date**: 2026-02-10

## Existing Entities (No Schema Changes)

### Transaction (existing)
Classification status is determined by existing nullable columns:
- `category_id IS NULL` → needs categorization
- `enrichment_source IS NULL` → needs enrichment
- Both conditions OR'd together = "unclassified"

No new columns needed on the transactions table.

### Categorization Batch (existing table: `categorization_batches`)
Already tracks all needed metrics:
- `id`, `import_id`, `transaction_count`
- `success_count`, `failure_count`, `skipped_count`
- `rule_match_count`, `desc_rule_match_count`, `ai_match_count`
- `duration_ms`, `error_message`
- `started_at`, `completed_at`

No schema changes needed. Batches triggered from the batch classify UI will use the same table with `import_id = NULL` to distinguish them from import-triggered batches.

## New In-Memory State (Not Persisted)

### BatchJobState
Tracks progress of a running batch classification job. Lives in-memory only (lost on server restart, which is acceptable since the job would also be interrupted).

**Fields:**
- `batch_id: str` — Links to the categorization_batches row
- `status: str` — One of: `running`, `completed`, `failed`
- `total_transactions: int` — Total to process
- `processed_transactions: int` — Processed so far (incremented per AI sub-batch)
- `success_count: int` — Running tally
- `failure_count: int` — Running tally
- `skipped_count: int` — Running tally
- `rule_match_count: int` — Running tally
- `ai_match_count: int` — Running tally
- `desc_rule_match_count: int` — Running tally
- `error_message: str | None` — Set on failure
- `started_at: datetime` — Job start time
- `completed_at: datetime | None` — Set when job completes or fails

**State Transitions:**
```
[not exists] → running (on trigger)
running → completed (all transactions processed)
running → failed (unrecoverable error)
```

## Extended API Models

### CategorizationTriggerRequest (extended)
Adds optional `batch_size` field to existing model:
- `transaction_ids: list[str] | None` (existing)
- `force_ai: bool` (existing, default False)
- `batch_size: int | None` (NEW, default None → uses env config, range 10-200)

### BatchProgressResponse (new)
Returned by the progress polling endpoint:
- `batch_id: str`
- `status: str` — running | completed | failed
- `total_transactions: int`
- `processed_transactions: int`
- `success_count: int`
- `failure_count: int`
- `skipped_count: int`
- `rule_match_count: int`
- `desc_rule_match_count: int`
- `ai_match_count: int`
- `error_message: str | None`
- `started_at: datetime`
- `completed_at: datetime | None`

### UnclassifiedCountResponse (new)
Returned by the count endpoint:
- `count: int` — Number of transactions needing classification
