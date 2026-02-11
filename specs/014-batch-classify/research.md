# Research: Batch AI Classification

**Feature Branch**: `014-batch-classify`
**Date**: 2026-02-10

## R1: Progress Feedback Mechanism

**Decision**: Use polling from the frontend against an in-memory job state on the backend.

**Rationale**: The current backend is a single-process FastAPI app with DuckDB (no Redis, no Celery, no WebSocket infrastructure). Adding WebSockets or SSE for a single feature is over-engineered. Instead:
- Backend tracks batch job state in memory (a dict keyed by batch_id)
- Frontend polls a new `/api/categorization/batches/{batch_id}/progress` endpoint every 2 seconds
- Progress is updated after each AI sub-batch completes within `_process_ai_batches()`

**Alternatives considered**:
- WebSockets: Too much infrastructure for one feature; requires additional dependency
- Server-Sent Events (SSE): Simpler than WS but still requires connection management and isn't needed
- No progress (just final result): Fails SC-002 (feedback within 5 seconds) for large batches

## R2: Concurrency Control

**Decision**: Use an in-memory lock (threading.Lock or asyncio equivalent) to prevent concurrent batch runs.

**Rationale**: DuckDB is single-writer and there's no external job queue. A simple flag + lock in the categorization service prevents double-triggering. The lock is scoped to the batch classify operation only.

**Alternatives considered**:
- Database-level lock row: Adds schema complexity for something that's process-local
- Redis distributed lock: No Redis in the stack
- No lock (rely on frontend disable): Insufficient — users could hit the API directly or race-click

## R3: Batch Size Parameter Passthrough

**Decision**: Extend `CategorizationTriggerRequest` with an optional `batch_size` field. Pass it through to `_process_ai_batches()` instead of always reading `CATEGORIZATION_BATCH_SIZE` from config.

**Rationale**: Minimal change. The config value becomes the default; the API parameter overrides it per-request. This preserves backward compatibility — existing callers (review page, CSV import) continue using the env default.

**Alternatives considered**:
- Separate endpoint with different request model: Unnecessary duplication
- Config-only (no API override): Doesn't satisfy FR-009 (user-configurable batch size)

## R4: Unclassified Transaction Count Endpoint

**Decision**: Add a `GET /api/categorization/unclassified-count` endpoint that returns the count of transactions needing classification.

**Rationale**: The frontend needs this count before the user triggers the job (FR-005). Reuses the same query logic from `get_unclassified_transactions()` but returns only the count, avoiding loading all transaction data.

**Alternatives considered**:
- Return count as part of the trigger response: Too late — user needs to see it before triggering
- Query from the frontend's existing transaction list: Would require filtering logic duplication and may not include enrichment-needing transactions

## R5: Frontend Placement

**Decision**: Create a new "Settings" page accessible from the sidebar, with a "Batch Classification" section as its primary content.

**Rationale**: The sidebar already has a non-functional "Settings" button placeholder. The user's request ("backend or advanced place") aligns with a settings/admin area. This keeps the main transaction and review views clean while providing a dedicated space for batch operations.

**Alternatives considered**:
- Add to Review page: Clutters an already-complex page; review is about individual transactions
- Add to Transactions page: Users may not think to look there for bulk operations
- Dashboard widget: Too condensed for configuration controls and progress display

## R6: Background Processing

**Decision**: Run batch classification in a background thread (using `asyncio.to_thread` or `threading.Thread`) so the API returns immediately with a batch_id, then the frontend polls for progress.

**Rationale**: The current `trigger_categorization()` is synchronous and blocks the request until completion. For 500 transactions at 100/batch, that's 5+ Gemini API calls taking 30-120 seconds total. A blocking request would time out or leave the user with no feedback. Background processing + polling satisfies FR-006 and SC-002.

**Alternatives considered**:
- Keep synchronous (block until done): Times out for large batches, no progress feedback
- Celery/task queue: Over-engineered; no Celery in the stack
- asyncio.create_task: Works but harder to manage state; thread is simpler with DuckDB's connection model

## R7: Removing the 1000-Transaction Limit

**Decision**: When triggered from the batch classify interface, remove the hardcoded `limit=1000` on `get_unclassified_transactions()` and process ALL unclassified transactions.

**Rationale**: The spec says "all unclassified transactions" (FR-002, SC-001). The current 1000 limit was a safety measure for the per-import trigger. For the explicit batch classify action, the user expects everything to be processed.

**Alternatives considered**:
- Keep the 1000 limit and require multiple triggers: Poor UX, fails SC-001
- Add a configurable limit: Over-complicates; users want "classify everything"
