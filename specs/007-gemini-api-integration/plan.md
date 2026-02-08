# Implementation Plan: Gemini API Integration

**Branch**: `007-gemini-api-integration` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-gemini-api-integration/spec.md`

## Summary

Replace the existing Claude CLI subprocess-based AI categorization with Google Gemini API integration. The new gemini_client.py module will expose the same `invoke_and_parse(prompt: str) -> list[dict]` interface, use the google-generativeai package with JSON output mode, and include retry logic with exponential backoff. The existing claude_client.py is retained as a deprecated backup.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115.6, google-generativeai (to be added), Pydantic 2.10.4
**Storage**: DuckDB 1.1.3 (existing, unchanged)
**Testing**: pytest 8.3.4
**Target Platform**: Linux server (development container)
**Project Type**: Web application (backend API + frontend)
**Performance Goals**: API response within existing timeout (120s default), retry delays 2s/4s/8s
**Constraints**: Must maintain same interface as claude_client for drop-in replacement
**Scale/Scope**: Single-user personal finance app, batch processing up to 50 transactions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution is not yet configured (template placeholders only). No gates to enforce. Proceeding with standard best practices:

- [x] Feature scope is well-defined (single responsibility: AI client swap)
- [x] Testing approach: Unit tests for new gemini_client module
- [x] No new architectural patterns introduced (follows existing service pattern)
- [x] Backward compatibility maintained (same interface)

## Project Structure

### Documentation (this feature)

```text
specs/007-gemini-api-integration/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (minimal - no new data entities)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (internal API only)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── config.py           # Add GEMINI_API_KEY, GEMINI_MODEL
│   ├── services/
│   │   ├── gemini_client.py     # NEW: Gemini API client
│   │   ├── claude_client.py     # EXISTING: Mark deprecated, retain
│   │   └── categorization_service.py  # UPDATE: Import from gemini_client
│   └── ...
├── tests/
│   └── test_gemini_client.py    # NEW: Unit tests
└── requirements.txt        # Add google-generativeai

.env.example                # NEW: Add GEMINI_API_KEY entry
```

**Structure Decision**: Follows existing web application structure. Changes are isolated to backend/app/services/ with a new module and minimal updates to existing files.

## Complexity Tracking

No constitution violations. Simple module replacement with maintained interface.
