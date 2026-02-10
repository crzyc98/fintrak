# Implementation Plan: Description-Based Pattern Rules

**Branch**: `010-description-pattern-rules` | **Date**: 2026-02-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-description-pattern-rules/spec.md`

## Summary

Add description-based pattern rules as a fallback categorization mechanism for transactions without a normalized merchant. When a user manually corrects a transaction's category, the system extracts a generalized pattern from the description (replacing variable numeric portions with wildcards) and stores it as an account-scoped rule. During future imports, the categorization pipeline applies these rules after merchant-based rules but before AI categorization. A new `description_pattern_rules` table stores these rules separately from existing merchant rules.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.8.2 (frontend)
**Primary Dependencies**: FastAPI 0.115.6, React 19.2.3, DuckDB 1.1.3, Pydantic 2.10.4
**Storage**: DuckDB (file-based: `fintrak.duckdb`) — new `description_pattern_rules` table
**Testing**: pytest (backend), npx tsc --noEmit (frontend type check)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Pattern matching across <1000 rules per account; negligible latency impact on import pipeline
**Constraints**: DuckDB single-writer; pattern extraction must be deterministic and fast (<1ms per description)
**Scale/Scope**: Hundreds of rules per account (typical), thousands of transactions per import batch

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No project constitution defined (template only). Gate passes by default — no violations to check.

**Post-Phase 1 re-check**: Design follows existing codebase patterns (separate service files, Pydantic models, DuckDB direct queries). No new dependencies introduced. No architectural deviations.

## Project Structure

### Documentation (this feature)

```text
specs/010-description-pattern-rules/
├── plan.md              # This file
├── research.md          # Phase 0 output — design decisions
├── data-model.md        # Phase 1 output — table schema
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — API contracts
│   └── api.md
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── database.py                          # ADD: description_pattern_rules table DDL
│   ├── models/
│   │   └── categorization.py                # MODIFY: add description rule models, extend responses
│   ├── services/
│   │   ├── pattern_extractor.py             # NEW: description → wildcard pattern extraction
│   │   ├── desc_rule_service.py             # NEW: CRUD + matching for description rules
│   │   ├── transaction_service.py           # MODIFY: add description-rule creation fallback
│   │   ├── categorization_service.py        # MODIFY: add description-rule matching step
│   │   └── rule_service.py                  # MINOR: no changes expected
│   └── routers/
│       └── categorization.py                # MODIFY: extend endpoints, add preview-pattern
└── tests/
    ├── test_pattern_extractor.py            # NEW: pattern extraction unit tests
    ├── test_desc_rule_service.py            # NEW: description rule CRUD + matching tests
    └── test_categorization_integration.py   # NEW: pipeline integration tests

frontend/
└── src/
    └── services/
        └── api.ts                           # MODIFY: update TypeScript interfaces
```

**Structure Decision**: Web application structure (backend/ + frontend/). All new backend code follows existing patterns: services as classes with module-level singletons, Pydantic models for request/response, direct DuckDB queries via `get_db()` context manager.

## Complexity Tracking

No constitution violations to justify.
