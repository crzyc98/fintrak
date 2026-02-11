# Feature Specification: Fix Enrichment Update Failure

**Feature Branch**: `013-fix-enrichment-update`
**Created**: 2026-02-11
**Status**: Draft
**Input**: User description: "Fix DuckDB enrichment update causing duplicate key constraint violations — the enrichment service fails to update transactions because the database internally converts UPDATE into DELETE+INSERT, which conflicts with multiple indexes on the transactions table."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enrichment Completes Successfully (Priority: P1)

As a user, when I trigger transaction enrichment (either manually or automatically), the system successfully updates each transaction with its AI-generated merchant name, subcategory, and discretionary classification — without database errors silently dropping the results.

**Why this priority**: This is the core bug. Enrichment currently fails 100% of the time due to a database constraint error, meaning no transactions ever get enriched. Fixing this restores the primary value of the enrichment feature.

**Independent Test**: Can be fully tested by triggering enrichment on one or more unenriched transactions and verifying the enriched fields are persisted to the database.

**Acceptance Scenarios**:

1. **Given** a transaction with no enrichment data (enrichment_source IS NULL), **When** the enrichment service processes it, **Then** the transaction's normalized_merchant, subcategory, is_discretionary, and enrichment_source fields are updated in the database.
2. **Given** a batch of 10 unenriched transactions, **When** enrichment is triggered, **Then** all 10 transactions are enriched successfully with 0 failures reported.
3. **Given** a transaction that already has enrichment data (enrichment_source = 'ai'), **When** enrichment is triggered, **Then** the transaction is skipped (not re-processed).

---

### User Story 2 - Enrichment Reports Accurate Results (Priority: P2)

As a user, when enrichment completes, the response summary accurately reflects what happened — showing correct counts of successful, failed, and skipped transactions.

**Why this priority**: When the update silently fails, the system logs a warning but reports 0 successes, which is confusing. Accurate reporting lets users know whether enrichment is working.

**Independent Test**: Can be tested by triggering enrichment and comparing the reported success/failure counts against actual database state.

**Acceptance Scenarios**:

1. **Given** 5 unenriched transactions, **When** enrichment completes successfully for all 5, **Then** the response shows success_count=5 and failure_count=0.
2. **Given** 3 unenriched transactions where 1 has an empty description, **When** enrichment runs, **Then** the response shows success_count=2, skipped_count=1, and failure_count=0.

---

### Edge Cases

- What happens when the same transaction is enriched concurrently by two overlapping requests?
- What happens when the AI returns a normalized_merchant that exceeds the column's character limit?
- What happens when a transaction is deleted between the time it's queried for enrichment and the time the update is applied?
- What happens when the database connection is interrupted mid-batch (e.g., during a batch of 50 updates)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST successfully persist enrichment data (normalized_merchant, subcategory, is_discretionary, enrichment_source) to transactions without triggering database constraint violations.
- **FR-002**: System MUST update only the enrichment-related columns on existing transaction records, not re-insert the entire record.
- **FR-003**: System MUST handle partial batch failures gracefully — if one transaction update fails, the remaining transactions in the batch MUST still be attempted.
- **FR-004**: System MUST log clear, actionable error messages when an individual transaction update fails, including the transaction ID and error details.
- **FR-005**: System MUST work reliably regardless of how many indexes exist on the transactions table.

### Key Entities

- **Transaction**: The primary record being updated. Key enrichment attributes: normalized_merchant, subcategory, is_discretionary, enrichment_source. The transaction has a UUID primary key and multiple secondary indexes that must not interfere with updates.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of enrichment update operations complete without database constraint errors.
- **SC-002**: Enrichment triggered on a batch of transactions results in all processable transactions being enriched (success_count matches the number of non-skipped transactions).
- **SC-003**: Enrichment operations remain reliable as the number of indexes on the transactions table grows (no regressions when new indexes are added in future features).
- **SC-004**: All existing enrichment-related tests continue to pass after the fix.

## Assumptions

- The root cause is a known limitation in the embedded database engine where UPDATE operations on tables with multiple indexes can trigger spurious primary key constraint violations.
- The fix should be purely in the data persistence layer — no changes needed to the AI enrichment logic, prompt building, or API endpoints.
- The existing test suite adequately covers the enrichment workflow and will validate the fix.
