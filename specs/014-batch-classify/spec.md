# Feature Specification: Batch AI Classification

**Feature Branch**: `014-batch-classify`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "could we setup an option maybe it would be in a backend or advanced place where i could have the AI classify run on large batches maybe 100 at a time of transactions that haven't yet been classified"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trigger Bulk Classification of Unclassified Transactions (Priority: P1)

As a user with many unclassified transactions (e.g., after a large CSV import), I want to navigate to an advanced settings or admin area and trigger AI classification on all unclassified transactions in large batches so that I can categorize hundreds of transactions without manually processing them one by one.

**Why this priority**: This is the core ask — the ability to run AI classification on a large volume of unclassified transactions from a single action. Without this, users must rely on per-transaction or small-batch classification, which is impractical after bulk imports.

**Independent Test**: Can be fully tested by importing a set of uncategorized transactions, navigating to the batch classify interface, clicking the trigger button, and verifying that all previously uncategorized transactions receive categories.

**Acceptance Scenarios**:

1. **Given** there are 250 unclassified transactions in the system, **When** the user triggers batch classification, **Then** all 250 transactions are processed through the classification pipeline (rules first, then AI) and assigned categories.
2. **Given** there are 0 unclassified transactions, **When** the user navigates to the batch classify interface, **Then** the system displays a message indicating there are no transactions to classify and the trigger action is disabled.
3. **Given** the user triggers batch classification while another batch is already in progress, **When** the second request is made, **Then** the system prevents duplicate runs and informs the user that classification is already underway.

---

### User Story 2 - Monitor Batch Classification Progress (Priority: P2)

As a user who has triggered a large batch classification, I want to see real-time progress of the classification job so that I know how many transactions have been processed, how many remain, and whether any errors occurred.

**Why this priority**: Large batches may take time to process. Without progress feedback, users don't know if the system is working, stuck, or finished. Progress visibility builds trust and helps users plan their workflow.

**Independent Test**: Can be tested by triggering classification on 100+ transactions and observing that the progress display updates as batches complete, showing counts of processed, remaining, succeeded, and failed transactions.

**Acceptance Scenarios**:

1. **Given** the user has triggered batch classification on 200 transactions, **When** the classification is running, **Then** the interface shows a progress indicator with the count of transactions processed so far, the total count, and the number of successful and failed classifications.
2. **Given** a batch classification completes, **When** all transactions have been processed, **Then** the interface shows a summary with total processed, success count, failure count, rule-matched count, and AI-matched count.
3. **Given** an error occurs during batch classification (e.g., AI service unavailable), **When** the batch partially completes, **Then** the interface displays the error and shows how many transactions were successfully processed before the failure.

---

### User Story 3 - Configure Batch Size (Priority: P3)

As a user, I want to choose the batch size (number of transactions sent per AI request) before triggering classification so that I can balance speed versus API rate limits based on my usage tier.

**Why this priority**: Different users may have different API rate limits or cost constraints. Allowing batch size configuration provides flexibility, but has a sensible default (100) that works for most users.

**Independent Test**: Can be tested by setting batch size to 25, triggering classification on 100 transactions, and verifying that the system makes 4 separate AI calls of 25 transactions each.

**Acceptance Scenarios**:

1. **Given** the user is on the batch classify interface, **When** they view the batch size setting, **Then** it defaults to 50 transactions per AI request (matching the environment default).
2. **Given** the user sets batch size to 50, **When** they trigger classification on 150 transactions, **Then** the system processes them in 3 batches of 50.
3. **Given** the user enters an invalid batch size (e.g., 0 or a negative number), **When** they attempt to trigger classification, **Then** the system rejects the input and displays a validation message.

---

### Edge Cases

- What happens when the AI service returns low-confidence results for some transactions? They are skipped based on the existing confidence threshold and reported as "skipped" in the summary.
- What happens if the user's AI API key is not configured? The system displays a clear error message indicating the API key is missing and classification cannot proceed.
- What happens if the user navigates away from the page while classification is running? The backend continues processing; when the user returns, they see the final result or current progress.
- What happens when rule-based matching classifies all transactions before AI is needed? The summary shows all transactions matched by rules, zero AI calls made, and the job completes quickly.
- What happens when some transactions have empty descriptions or only sensitive data? Those transactions are skipped by the AI classification and counted as skipped in the summary.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a dedicated interface accessible from an "Advanced" or "Settings" area for triggering batch AI classification.
- **FR-002**: System MUST identify all unclassified transactions (those without an assigned category or without enrichment data) when the user triggers batch classification.
- **FR-003**: System MUST apply rule-based matching (merchant rules, then description pattern rules) before sending remaining transactions to the AI service.
- **FR-004**: System MUST process AI classification in configurable batch sizes, defaulting to 50 transactions per AI request (matching the `CATEGORIZATION_BATCH_SIZE` environment default).
- **FR-005**: System MUST display the count of unclassified transactions before the user triggers the batch job.
- **FR-006**: System MUST show classification progress during execution, including transactions processed, remaining, succeeded, and failed.
- **FR-007**: System MUST display a completion summary showing total processed, rule-matched count, AI-matched count, skipped count, failure count, and duration.
- **FR-008**: System MUST prevent concurrent batch classification runs to avoid duplicate processing.
- **FR-009**: System MUST allow the user to configure the batch size (transactions per AI request) with a minimum of 10 and maximum of 200.
- **FR-010**: System MUST handle AI service errors gracefully, reporting partial results and allowing the user to retry failed transactions.

### Key Entities

- **Batch Classification Job**: Represents a single bulk classification run, including its configuration (batch size), progress state, and final results (success/failure/skip counts, duration).
- **Unclassified Transaction**: A transaction that either has no assigned category or is missing enrichment data (normalized merchant, subcategory, discretionary flag).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can classify 500 unclassified transactions in a single action without manual intervention for each transaction.
- **SC-002**: Users receive progress feedback within 5 seconds of triggering batch classification.
- **SC-003**: The batch classification interface clearly shows the number of unclassified transactions before the user decides to run the job.
- **SC-004**: Upon completion, users can see a summary that accounts for 100% of processed transactions (each transaction reported as rule-matched, AI-matched, skipped, or failed).
- **SC-005**: Users who trigger batch classification and encounter an error can understand what went wrong and retry without losing previously completed results.

## Assumptions

- The existing three-tier classification pipeline (merchant rules, description rules, AI) will be reused; this feature provides a new trigger point and UI, not a new classification algorithm.
- The user's AI API key is already configured in the environment; this feature does not add API key management.
- The default batch size of 100 is appropriate for most API usage tiers; users can adjust if they encounter rate limiting.
- Batch classification history is already tracked by the existing categorization batches system and does not need a separate history view.
- The "advanced" or "settings" area may be a new section in the UI or an addition to an existing settings page, depending on current frontend structure.
