# Research: Description-Based Pattern Rules

**Feature**: 010-description-pattern-rules
**Date**: 2026-02-10

## R-001: New Table vs. Extending Existing `categorization_rules`

**Decision**: Create a new `description_pattern_rules` table rather than adding columns to `categorization_rules`.

**Rationale**:
- The existing `categorization_rules` table has a `UNIQUE` constraint on `merchant_pattern`. Description rules need a `UNIQUE(account_id, description_pattern)` constraint — fundamentally different uniqueness semantics.
- Description rules are account-scoped; merchant rules are global. Mixing them in one table requires nullable `account_id` and complex conditional logic.
- Separate tables keep each rule type's query logic clean and independently optimizable.
- The `_apply_rules` method in `categorization_service.py` can call description rule matching as a distinct fallback step, preserving clear priority ordering.

**Alternatives considered**:
- Adding `account_id`, `pattern_type`, `description_pattern` columns to `categorization_rules` — rejected because it complicates the UNIQUE constraint, requires migration of existing data, and mixes global/scoped semantics.

## R-002: Pattern Extraction Algorithm

**Decision**: Use regex-based generalization that replaces sequences of 3+ digits (and adjacent alphanumeric fragments that end in digits) with `*` wildcards, then normalize to lowercase for storage.

**Rationale**:
- Bank descriptions typically vary only in trailing numeric IDs (account numbers, check numbers, reference codes). Examples:
  - `DIRECT DEPOSIT Fidelity Bro461026 (Cash)` → `DIRECT DEPOSIT Fidelity Bro* (Cash)`
  - `CHECK #1234 DEPOSIT` → `CHECK #* DEPOSIT`
  - `DIVIDEND REINVEST 98765` → `DIVIDEND REINVEST *`
- Replacing 3+ digit sequences (not 1-2 digits, which may be meaningful like "Route 66") provides good generalization without over-matching.
- Storing patterns lowercase enables case-insensitive matching via simple string comparison.

**Alternatives considered**:
- Exact description matching (no generalization) — rejected because descriptions vary in trailing IDs, defeating the purpose.
- N-gram or fuzzy matching — rejected as over-engineered for the current use case; simple wildcard patterns are sufficient and debuggable.

## R-003: Pattern Matching Strategy

**Decision**: Convert stored wildcard patterns to regex at match time. Pattern `DIRECT DEPOSIT Fidelity Bro* (Cash)` becomes regex `^direct deposit fidelity bro.* \(cash\)$` for matching.

**Rationale**:
- Wildcard `*` is user-visible and intuitive (displayed in rules UI).
- Converting to regex at match time allows precise anchored matching (start-to-end), preventing substring false positives.
- Both the stored pattern and the incoming description are lowercased for comparison.
- Performance: regex compilation can be cached per-rule if needed; with <1000 rules this is negligible.

**Alternatives considered**:
- Substring/contains matching (like current merchant rules) — rejected because description patterns are longer and substring matching would produce too many false positives.
- Store patterns as regex directly — rejected because raw regex is not user-friendly for display/management.

## R-004: Integration Point in Categorization Pipeline

**Decision**: Insert description-rule matching between merchant-rule matching and AI categorization in `categorization_service._apply_rules()`.

**Rationale**:
- This preserves FR-005 (merchant rules take priority) while ensuring description rules are applied before the more expensive AI call.
- Transactions that fail merchant-rule matching AND have an `account_id` are checked against description pattern rules.
- The categorization source is tracked as `'desc_rule'` to distinguish from merchant-rule matches.

**Alternatives considered**:
- Separate pipeline step outside `_apply_rules` — rejected because it would require restructuring the trigger flow; the fallback naturally belongs inside the same method.

## R-005: Frontend Display Strategy

**Decision**: Extend the existing rules list endpoint and frontend to return description rules alongside merchant rules, with a `rule_type` discriminator.

**Rationale**:
- FR-007 requires description rules to appear alongside merchant rules. A unified list with a type indicator is simpler than a separate UI section.
- The existing `listRules()` API and frontend components can be extended with minimal changes.
- Description rules display the account name for context (merchant rules show "All accounts").

**Alternatives considered**:
- Separate API endpoint and UI tab for description rules — rejected as over-engineered; users benefit from seeing all rules in one view.

## R-006: Categorization Source Value

**Decision**: Use `'desc_rule'` as the new `categorization_source` value.

**Rationale**:
- The existing `categorization_source` field is `VARCHAR(10)`, and `'desc_rule'` fits within the 10-char limit.
- Distinguishes description-rule matches from merchant-rule matches (`'rule'`) for analytics and debugging.
- No schema change needed — just a new value in an existing field.

**Alternatives considered**:
- Reusing `'rule'` for both types — rejected because it makes it impossible to debug which type of rule matched.
- Using `'pattern'` — rejected as too vague; could be confused with merchant patterns.
