# Quickstart: Batch AI Classification

**Feature Branch**: `014-batch-classify`

## What This Feature Does

Adds a Settings page with a batch classification panel that lets users trigger AI categorization on all unclassified transactions at once, with configurable batch sizes and real-time progress tracking.

## Architecture Overview

```
┌─────────────────┐     poll /progress      ┌──────────────────────┐
│  SettingsView    │ ◄──────────────────────►│  GET /batches/{id}/  │
│  (new React      │                         │  progress             │
│   component)     │     POST /trigger       │                      │
│                  │ ───────────────────────► │  POST /trigger       │
│  - batch size    │     (returns 202 +      │  (extended w/        │
│    input         │      batch_id)          │   batch_size)        │
│  - trigger btn   │                         │                      │
│  - progress bar  │     GET /unclassified   │  GET /unclassified   │
│  - summary       │ ───────────────────────►│  -count              │
└─────────────────┘                         └──────────┬───────────┘
                                                       │
                                            ┌──────────▼───────────┐
                                            │  CategorService      │
                                            │  (extended)          │
                                            │                      │
                                            │  - in-memory job     │
                                            │    state tracking    │
                                            │  - background thread │
                                            │  - concurrency lock  │
                                            │  - batch_size param  │
                                            └──────────┬───────────┘
                                                       │
                                            ┌──────────▼───────────┐
                                            │  Gemini API          │
                                            │  (existing)          │
                                            └──────────────────────┘
```

## Key Files to Modify

### Backend (Python/FastAPI)

| File | Change |
|------|--------|
| `backend/app/models/categorization.py` | Add `batch_size` to request model; add `BatchProgressResponse`, `UnclassifiedCountResponse`, `BatchTriggerResponse` models |
| `backend/app/services/categorization_service.py` | Add job state tracking, background processing, concurrency lock, batch_size passthrough, remove 1000 limit for batch classify |
| `backend/app/routers/categorization.py` | Add `/unclassified-count` and `/batches/{id}/progress` endpoints; change trigger to return 202 for background jobs |

### Frontend (React/TypeScript)

| File | Change |
|------|--------|
| `frontend/src/services/api.ts` | Add `getUnclassifiedCount()`, `getBatchProgress()` functions; update `CategorizationTriggerRequestData` type |
| `frontend/components/SettingsView.tsx` | NEW — Settings page with batch classification panel |
| `frontend/App.tsx` | Add "Settings" tab routing |
| `frontend/components/Sidebar.tsx` | Wire up existing Settings button placeholder |

## Implementation Order

1. **Backend models** — Add new Pydantic models (no behavior change)
2. **Backend service** — Add job state, concurrency lock, background processing, batch_size param
3. **Backend endpoints** — Add count + progress endpoints, modify trigger response
4. **Frontend API layer** — Add new API functions and types
5. **Frontend Settings page** — Build the UI with batch size input, trigger button, progress display
6. **Frontend navigation** — Wire Settings tab into App.tsx and Sidebar.tsx
7. **Backend tests** — Test concurrency, progress tracking, batch size override
8. **Integration test** — End-to-end trigger + poll + verify results

## How to Test Manually

1. Import a CSV with 100+ transactions (do NOT trigger auto-categorize)
2. Navigate to Settings page
3. Verify unclassified count shows correctly
4. Set batch size to 25
5. Click "Classify All"
6. Watch progress update every 2 seconds
7. Verify summary shows rule matches + AI matches + skipped = total
8. Check that transactions now have categories assigned
