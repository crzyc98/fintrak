# Implementation Plan: Auto-Create Rules from AI Classifications

**Branch**: `015-auto-ai-rules` | **Date**: 2026-02-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-auto-ai-rules/spec.md`

## Summary

After AI classification completes, automatically create categorization rules from high-confidence results (>= 0.9). This makes the system self-improving — merchants classified by AI once are handled by rules on all future runs, dramatically reducing API usage without requiring manual user corrections.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastAPI 0.115.6, Pydantic 2.10.4, google-genai (Gemini)
**Storage**: DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
**Testing**: pytest with in-memory DuckDB
**Target Platform**: Local web application (macOS/Linux)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Rule creation adds negligible overhead to existing batch processing
**Constraints**: Must not break existing rule matching or manual correction flows
**Scale/Scope**: Up to 50 transactions per AI batch, each potentially creating 1 rule

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

No constitution defined — no gates to check. Proceeding.

## Project Structure

### Documentation (this feature)

```text
specs/015-auto-ai-rules/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0: Research decisions
├── data-model.md        # Phase 1: Schema changes
├── quickstart.md        # Phase 1: How to test
├── contracts/           # Phase 1: API contract updates
│   └── rules-api.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (files to modify)

```text
backend/
├── app/
│   ├── config.py                          # Add AUTO_RULE_CONFIDENCE_THRESHOLD
│   ├── database.py                        # Add source column migration
│   ├── models/
│   │   └── categorization.py              # Add source field to models
│   └── services/
│       ├── categorization_service.py      # Core change: auto-rule creation in apply_unified_results()
│       ├── rule_service.py                # Accept source param in create_rule()
│       └── desc_rule_service.py           # Accept source param in create_rule()
└── tests/
    └── test_auto_rule_creation.py         # New: integration tests
```

**Structure Decision**: Backend-only change. No frontend modifications needed — the existing rules list endpoint already returns all rules, and the `source` field will be included automatically via the updated response models.

## Implementation Steps

### Step 1: Schema migration — add `source` column

**File**: `backend/app/database.py`

Add `ALTER TABLE` statements in `init_db()` after table creation:
```sql
ALTER TABLE categorization_rules ADD COLUMN IF NOT EXISTS source VARCHAR(10) DEFAULT 'manual';
ALTER TABLE description_pattern_rules ADD COLUMN IF NOT EXISTS source VARCHAR(10) DEFAULT 'manual';
```

### Step 2: Configuration — add threshold

**File**: `backend/app/config.py`

```python
AUTO_RULE_CONFIDENCE_THRESHOLD = float(
    os.getenv("AUTO_RULE_CONFIDENCE_THRESHOLD", "0.9")
)
```

### Step 3: Update Pydantic models

**File**: `backend/app/models/categorization.py`

- Add `source: Optional[str] = "manual"` to `CategorizationRuleCreate` and `DescriptionPatternRuleCreate`
- Add `source: str = "manual"` to `CategorizationRuleResponse` and `DescriptionPatternRuleResponse`

### Step 4: Update rule services to accept and store source

**File**: `backend/app/services/rule_service.py`
- Modify `create_rule()` to include `source` in the INSERT statement
- Read `data.source` (defaults to `"manual"`)

**File**: `backend/app/services/desc_rule_service.py`
- Same changes as rule_service

### Step 5: Update rule list queries to include source

**File**: `backend/app/services/rule_service.py`
- Update SELECT queries in `get_all_rules()` to include `source` column

**File**: `backend/app/services/desc_rule_service.py`
- Update SELECT queries to include `source` column

### Step 6: Core logic — auto-create rules from AI results

**File**: `backend/app/services/categorization_service.py`

Add a new method `_create_rules_from_ai_results()` and call it from `apply_unified_results()`.

**Logic**:
1. After the main result-application loop, collect rule candidates:
   - Filter results where `confidence >= AUTO_RULE_CONFIDENCE_THRESHOLD`
   - Filter results where category was actually assigned (not just enrichment)
2. Deduplicate merchant candidates — keep highest confidence per `normalized_merchant`
3. For each merchant candidate:
   - Check if a rule already exists via `rule_service.find_matching_rule()`
   - If not, create rule via `rule_service.create_rule(source="ai")`
4. For each non-merchant candidate (no `normalized_merchant`):
   - Extract pattern via `extract_pattern(description)`
   - Validate pattern is specific enough (not empty, not just `*`, length > 2 after stripping wildcards)
   - Check if rule exists via `desc_rule_service.find_matching_rule()`
   - If not, create rule via `desc_rule_service.create_rule(source="ai")`
5. Log summary: "Auto-created X merchant rules and Y description rules"

### Step 7: Tests

**File**: `backend/tests/test_auto_rule_creation.py`

Test cases:
- High-confidence AI result creates merchant rule
- Low-confidence AI result does not create rule
- Duplicate merchant does not create second rule
- Existing manual rule is not overwritten
- Same merchant in batch with different categories uses highest confidence
- Description pattern rule created when no merchant
- Empty/generic patterns are skipped
- End-to-end: classify → rules created → re-classify → rules used

## Complexity Tracking

No constitution violations. This is a focused backend change touching 6 existing files + 1 new test file.
