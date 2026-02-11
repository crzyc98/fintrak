# Implementation Plan: Batch AI Classification

**Branch**: `014-batch-classify` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-batch-classify/spec.md`

## Summary

Add a Settings page with a batch classification panel that lets users trigger AI categorization on all unclassified transactions at once. The backend extends the existing categorization service with background processing, in-memory progress tracking, configurable batch sizes, and concurrency control. The frontend provides a dedicated interface with an unclassified count display, batch size configuration, trigger button, real-time progress polling, and a completion summary.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, React 19.2.3, Pydantic 2.10.4, google-genai (Gemini)
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`) — no schema changes needed
**Testing**: pytest (backend), TypeScript type checking (frontend)
**Target Platform**: Web application (localhost dev)
**Project Type**: Web (backend + frontend)
**Performance Goals**: Progress feedback within 5 seconds of triggering; process 500 transactions in a single action
**Constraints**: Single-process FastAPI, no Redis/Celery/WebSocket infrastructure
**Scale/Scope**: Single user, up to ~1000 unclassified transactions per batch run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution not configured (template placeholders only). No gates to enforce. Proceeding.

**Post-design re-check**: N/A — no constitution principles defined.

## Project Structure

### Documentation (this feature)

```text
specs/014-batch-classify/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output — technical decisions
├── data-model.md        # Phase 1 output — entity/model design
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/
│   └── api.yaml         # Phase 1 output — OpenAPI contract
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── categorization.py    # MODIFY: Add BatchProgressResponse, UnclassifiedCountResponse, BatchTriggerResponse, batch_size field
│   ├── services/
│   │   └── categorization_service.py  # MODIFY: Add job state tracking, background thread, concurrency lock, batch_size passthrough
│   └── routers/
│       └── categorization.py    # MODIFY: Add /unclassified-count, /batches/{id}/progress, change trigger to 202
└── tests/                       # ADD: Tests for new endpoints and background processing

frontend/
├── components/
│   ├── SettingsView.tsx         # NEW: Settings page with batch classification panel
│   ├── Sidebar.tsx              # MODIFY: Wire up Settings button
│   └── App.tsx                  # MODIFY: Add Settings tab
└── src/
    └── services/
        └── api.ts               # MODIFY: Add getUnclassifiedCount(), getBatchProgress(), update trigger types
```

**Structure Decision**: Web application structure (existing). No new directories needed — all changes are additions to or modifications of existing files, plus one new frontend component.

## Design Decisions

### D1: Background Processing via Thread

The `/trigger` endpoint starts processing in a background thread and returns `202 Accepted` with the `batch_id`. The frontend polls `/batches/{batch_id}/progress` every 2 seconds.

**Why**: Synchronous processing would block for 30-120 seconds on large batches. No task queue (Celery/Redis) in the stack. A thread is the simplest mechanism that works with DuckDB's connection model.

### D2: In-Memory Job State

A module-level dict `_active_jobs: dict[str, BatchJobState]` tracks running/completed jobs. This state is transient (lost on restart), which is acceptable — the persisted `categorization_batches` table has the final results.

**Why**: Adding database columns for real-time progress would require frequent writes and complicate the existing batch service. In-memory state is sufficient for a single-process app.

### D3: Concurrency Lock

A `threading.Lock` prevents concurrent batch classify runs. The lock is acquired when a job starts and released when it completes/fails. API returns `409 Conflict` if a job is already running.

**Why**: DuckDB is single-writer, and running parallel AI batch jobs would be wasteful (rate limits) and confusing (duplicate categorizations).

### D4: Extend Existing Trigger Endpoint

Rather than creating a new endpoint, extend `POST /api/categorization/trigger` with an optional `batch_size` field and return `202` when processing will take time.

**Why**: Minimal API surface change. Existing callers (review page, CSV import) are unaffected since `batch_size` defaults to `None` (uses env config).

### D5: New Settings Page

Create a `SettingsView.tsx` component and add a "Settings" tab to the app navigation. The sidebar already has a placeholder Settings button.

**Why**: The user asked for an "advanced" or "backend" place. A Settings page is the natural home and opens the door for future admin features.

## Complexity Tracking

No constitution violations to justify. Feature uses existing patterns (polling, background threads, Pydantic models) and adds minimal new infrastructure.
