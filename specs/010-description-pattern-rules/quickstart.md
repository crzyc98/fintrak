# Quickstart: Description-Based Pattern Rules

**Feature**: 010-description-pattern-rules
**Date**: 2026-02-10

## Overview

Add description-based pattern rules as a fallback categorization method for transactions that lack a normalized merchant name. When a user manually corrects a transaction's category, the system extracts a generalized pattern from the description and saves it as an account-scoped rule for future imports.

## Architecture

```
Categorization Pipeline (priority order):
  1. Merchant-based rules (existing) — match on normalized_merchant
  2. Description-based rules (NEW) — match on description, scoped per account
  3. AI categorization (existing) — Gemini API fallback
```

## Key Files to Modify

### Backend

| File | Change |
| ---- | ------ |
| `backend/app/database.py` | Add `description_pattern_rules` table DDL |
| `backend/app/models/categorization.py` | Add Pydantic models for description rules; extend response models with `rule_type` |
| `backend/app/services/pattern_extractor.py` | **NEW** — Pattern extraction algorithm (description → wildcard pattern) |
| `backend/app/services/desc_rule_service.py` | **NEW** — CRUD + matching for description pattern rules |
| `backend/app/services/transaction_service.py` | Add description-rule creation fallback in `_create_rule_from_correction` flow |
| `backend/app/services/categorization_service.py` | Add description-rule matching step in `_apply_rules` |
| `backend/app/routers/categorization.py` | Extend rule endpoints to handle both types; add preview-pattern endpoint |
| `backend/tests/` | Tests for pattern extraction, rule CRUD, matching, pipeline integration |

### Frontend

| File | Change |
| ---- | ------ |
| `frontend/src/services/api.ts` | Update TypeScript interfaces and API functions for new fields |
| Rules display component (TBD) | Show `rule_type`, `account_name`, `description_pattern` in rules list |

## Implementation Order

1. **Pattern extractor** (`pattern_extractor.py`) — pure function, independently testable
2. **Database table** — DDL for `description_pattern_rules`
3. **Description rule service** — CRUD operations + matching logic
4. **Transaction service integration** — trigger description-rule creation on manual correction
5. **Categorization pipeline integration** — apply description rules as fallback
6. **API endpoints** — extend existing + add preview-pattern
7. **Frontend updates** — display description rules in rules list

## Dev Commands

```bash
# Run backend tests
cd backend && pytest

# Type check frontend
cd frontend && npx tsc --noEmit

# Start app for manual testing
./fintrak start -d
```

## Testing Strategy

- **Unit tests**: Pattern extraction with various description formats
- **Unit tests**: Description rule CRUD (create, upsert, delete, list)
- **Unit tests**: Pattern matching (case-insensitive, wildcard, account scoping)
- **Integration tests**: Full pipeline — manual correction → rule creation → next import auto-categorized
- **Integration tests**: Priority ordering — merchant rules beat description rules
