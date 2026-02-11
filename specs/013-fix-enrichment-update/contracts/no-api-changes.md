# API Contracts: Fix Enrichment Update Failure

**Feature**: 013-fix-enrichment-update
**Date**: 2026-02-11

## No API Changes Required

This feature is a **backend-only bug fix** in the data access layer. No API endpoints, request schemas, or response schemas are modified.

### Affected Endpoints (behavior fix only — same contracts)

| Endpoint | Method | Change |
| -------- | ------ | ------ |
| `/api/enrichment/trigger` | POST | No contract change. Will now return accurate `success_count` instead of 0. |
| `/api/categorization/trigger` | POST | No contract change. Will now succeed on heavily-indexed tables. |
| `/api/transactions/bulk/review` | POST | No contract change. Protected against future index additions. |
| `/api/transactions/bulk/category` | POST | No contract change. Protected against future index additions. |
| `/api/transactions/bulk/note` | POST | No contract change. Protected against future index additions. |

### Response Schema (unchanged)

The `EnrichmentBatchResponse` schema remains:
```json
{
  "total_count": 1,
  "success_count": 1,
  "failure_count": 0,
  "skipped_count": 0,
  "duration_ms": 4065,
  "error_message": null
}
```

The only observable change is that `success_count` will now correctly reflect successful updates instead of always being 0.
