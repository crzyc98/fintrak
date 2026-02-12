# Research: Auto-Create Rules from AI Classifications

## R1: Where to hook rule creation into the AI flow

**Decision**: Add rule creation inside `apply_unified_results()` in `categorization_service.py`, after the successful `safe_update_transaction()` call (after line 342).

**Rationale**: At this point, confidence has already been validated, the transaction has been written to DB, and we have access to both the AI result (with `normalized_merchant`, `confidence`, `category_name`) and the original transaction data (with `account_id`, `description`).

**Alternatives considered**:
- After `_process_ai_batches()` completes: Would require passing all results back up — more complex, no benefit.
- In a separate post-processing step: Would add a second DB pass — wasteful.

## R2: How to handle duplicate rules

**Decision**: Check for existing rules before creating. If any rule exists for the merchant (regardless of source), skip. Do not upsert.

**Rationale**: The existing `create_rule()` methods have upsert behavior (update category + timestamp if pattern exists). This is dangerous for AI auto-rules — it would silently overwrite manual corrections. Instead, we check first and skip if any rule exists, preserving manual rules (FR-004).

**Alternatives considered**:
- Use existing upsert with source-aware logic: More complex, requires changing core `create_rule()` behavior.
- Only skip if existing rule is "manual": Adds complexity with minimal benefit — if an AI rule already exists, re-creating it is wasteful anyway.

## R3: How to add source tracking to rules

**Decision**: Add a `source VARCHAR(10) DEFAULT 'manual'` column to both `categorization_rules` and `description_pattern_rules` tables. Add migration logic in `init_db()` to add the column to existing databases.

**Rationale**: Both rule tables currently lack a source field. The default of `'manual'` ensures backward compatibility — existing rules are treated as manually created. New AI-created rules will be inserted with `source='ai'`.

**Alternatives considered**:
- Separate "ai_rules" table: Over-engineered, duplicates schema, complicates rule matching.
- Track in a metadata table: Indirect, adds joins, no benefit.

## R4: Confidence threshold for auto-rule creation

**Decision**: Use a configurable `AUTO_RULE_CONFIDENCE_THRESHOLD` environment variable defaulting to `0.9`, separate from the existing `CATEGORIZATION_CONFIDENCE_THRESHOLD` (0.7).

**Rationale**: Rule creation requires higher confidence than simply applying a category to a transaction. A rule persists and affects all future transactions, so the bar should be higher. 0.9 is conservative enough to avoid bad rules while still capturing most clear-cut cases.

## R5: Handling same-merchant conflicts within a batch

**Decision**: Collect rule candidates during batch processing, deduplicate by merchant (keeping highest confidence), then create rules after the batch loop completes.

**Rationale**: Processing inside the per-result loop would create a rule from the first high-confidence result, potentially missing a higher-confidence result for the same merchant later in the batch. Collecting and deduplicating ensures FR-007 compliance.

## R6: Description pattern validation

**Decision**: Reuse existing `extract_pattern()` from `pattern_extractor.py`. Skip rule creation if the extracted pattern is empty, is just `*`, or is shorter than 3 characters after stripping wildcards.

**Rationale**: The existing pattern extractor already handles token normalization. Adding a minimum-specificity check prevents overly generic patterns (FR-008) without reinventing the extraction logic.
