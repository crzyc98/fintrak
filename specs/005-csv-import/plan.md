# Implementation Plan: CSV Import

**Branch**: `005-csv-import` | **Date**: 2026-01-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-csv-import/spec.md`

## Summary

Per-account CSV column mapping with drag & drop import. Users configure column mappings once per account, then drag & drop CSV files to import transactions. Features visual column mapper for first-time setup, auto-detection of common column names, support for both single Amount and separate Debit/Credit columns, duplicate detection in preview, and date format configuration.

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, Pydantic 2.10.4, React 19.2.3, Vite 6.2.0
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
**Testing**: pytest 8.3.4 with FastAPI TestClient (backend), Vite test runner (frontend)
**Target Platform**: Web application (localhost development, Linux server deployment)
**Project Type**: web (frontend + backend)
**Performance Goals**: Preview within 2 seconds for 1,000 rows; handle up to 10,000 transactions per import
**Constraints**: File parsing client-side or via base64 upload; CSV files typically under 1MB
**Scale/Scope**: Single-user personal finance app; one account selected at a time

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file contains placeholder template content (not project-specific principles). No specific gates to evaluate. Proceeding with standard best practices:

- [x] Feature follows existing codebase patterns (service layer, Pydantic models, FastAPI routers)
- [x] New functionality is additive (extends Account entity, adds new router/service)
- [x] Testing approach matches existing (pytest with TestClient)
- [x] No new external dependencies required for core functionality

## Project Structure

### Documentation (this feature)

```text
specs/005-csv-import/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── csv-import-api.yaml
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── account.py        # Extend with csv_column_mapping field
│   │   └── csv_import.py     # NEW: CSV import models
│   ├── routers/
│   │   └── csv_import.py     # NEW: CSV import endpoints
│   ├── services/
│   │   ├── account_service.py  # Update for csv_column_mapping
│   │   └── csv_import_service.py  # NEW: CSV parsing logic
│   └── database.py           # Add csv_column_mapping column to accounts
└── tests/
    └── test_csv_import.py    # NEW: CSV import tests

frontend/
├── components/
│   ├── AccountsView.tsx      # Add drop zone integration
│   ├── CsvDropZone.tsx       # NEW: Drag & drop component
│   ├── CsvColumnMapper.tsx   # NEW: Column mapping modal
│   └── CsvImportPreview.tsx  # NEW: Import preview modal
└── src/
    └── services/
        └── api.ts            # Add CSV import API functions
```

**Structure Decision**: Web application structure (Option 2). This matches the existing fintrak codebase with separate backend/ and frontend/ directories. All new code follows established patterns.

## Complexity Tracking

No constitution violations. Feature complexity is justified by user requirements:
- Multiple components needed for UX flow (drop zone → mapper → preview)
- New service layer for CSV parsing logic
- Database schema change (single column addition)
