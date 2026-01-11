# Feature Specification: AI-Powered Transaction Categorization

**Feature Branch**: `003-ai-categorization`
**Created**: 2026-01-11
**Status**: Draft
**Input**: User description: "Add AI-powered transaction categorization to FinTrack using Claude Code in headless mode, optimized for batching and zero API cost."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Categorization on Import (Priority: P1)

As a FinTrack user, when I import a CSV file of bank transactions, I want the system to automatically categorize my transactions so that I don't have to manually assign categories to each one.

**Why this priority**: This is the core value proposition of the feature. Without automatic categorization, users gain no benefit from the AI integration. This delivers immediate time savings on the most common user workflow.

**Independent Test**: Can be fully tested by importing a CSV with 50+ uncategorized transactions and verifying that high-confidence transactions receive category assignments automatically.

**Acceptance Scenarios**:

1. **Given** a user has imported a CSV file with 100 transactions and the system has 10 predefined categories, **When** the import completes successfully, **Then** transactions are automatically categorized where confidence exceeds the threshold (default 0.7)
2. **Given** a user imports transactions and the AI assigns categories, **When** the categorization completes, **Then** the user sees which transactions were auto-categorized and which remain uncategorized
3. **Given** a user imports transactions, **When** the AI service is unavailable or times out, **Then** the import still completes successfully with transactions left uncategorized and the user is notified of the categorization issue

---

### User Story 2 - Manual Override with Learning (Priority: P2)

As a FinTrack user, when I manually change a transaction's category, I want the system to learn from my correction so that similar transactions are categorized correctly in the future without AI involvement.

**Why this priority**: This creates a feedback loop that improves accuracy over time and reduces dependency on the AI service. Users who invest time in corrections see compounding returns.

**Independent Test**: Can be fully tested by manually re-categorizing a transaction, then importing new transactions with the same merchant to verify the rule is applied without AI.

**Acceptance Scenarios**:

1. **Given** a transaction from "STARBUCKS #1234" was auto-categorized as "Restaurants", **When** the user changes it to "Coffee & Snacks", **Then** the system records a rule mapping the normalized merchant to "Coffee & Snacks"
2. **Given** a learned rule exists for "STARBUCKS" -> "Coffee & Snacks", **When** a new import contains a transaction from "STARBUCKS #5678", **Then** the transaction is categorized as "Coffee & Snacks" without invoking the AI
3. **Given** multiple learned rules exist, **When** the user imports transactions, **Then** rule-based categorization happens first, and only remaining uncategorized transactions are sent to AI

---

### User Story 3 - Merchant Name Normalization (Priority: P3)

As a FinTrack user, I want transaction descriptions cleaned up and normalized so that I see readable merchant names instead of cryptic bank codes, and so the AI can more accurately categorize similar transactions.

**Why this priority**: Normalization improves both user experience (readable names) and AI accuracy (consistent inputs). However, the feature works without it, just less elegantly.

**Independent Test**: Can be fully tested by importing transactions with noisy descriptions (e.g., "POS DEBIT 1234 AMAZON SEATTLE WA") and verifying the display shows "Amazon" while retaining the original.

**Acceptance Scenarios**:

1. **Given** a transaction has description "CHECKCARD 0315 WALMART SUPERCENTER DES MOINES IA", **When** it is processed, **Then** the normalized merchant displays as "Walmart Supercenter" while the original description is preserved
2. **Given** a transaction has description "ACH WITHDRAWAL NETFLIX.COM", **When** it is processed, **Then** the normalized merchant displays as "Netflix" (common noise tokens removed)
3. **Given** a transaction description cannot be reliably normalized, **When** it is processed, **Then** the original description is used as-is without data loss

---

### User Story 4 - Batch Processing Visibility (Priority: P4)

As a system administrator or power user, I want visibility into the categorization process including batch sizes, success rates, and timing so that I can monitor system health and tune configuration.

**Why this priority**: Operational visibility is important for troubleshooting but not essential for core functionality. Users can use the feature without logging, but debugging issues becomes harder.

**Independent Test**: Can be fully tested by importing transactions and reviewing logs to verify batch processing metrics are captured.

**Acceptance Scenarios**:

1. **Given** an import triggers AI categorization, **When** the process completes, **Then** logs show: batch count, total transactions processed, success/failure counts, and total duration
2. **Given** a batch exceeds the configured timeout, **When** the timeout occurs, **Then** the system logs the timeout event and proceeds with remaining transactions
3. **Given** AI response parsing fails, **When** the failure occurs, **Then** the system logs the malformed response (without sensitive data) and continues processing

---

### Edge Cases

- What happens when the AI returns a category_id that doesn't exist in the system? The transaction remains uncategorized and the invalid response is logged.
- What happens when a transaction matches multiple learned rules? The most recently created rule takes precedence (last user correction wins).
- What happens when the AI service returns an empty response? Transactions remain uncategorized; logged as AI service error.
- How does the system handle transactions with empty descriptions? They are skipped for AI categorization and logged as "unprocessable."
- What happens when batch size exceeds available transactions? The system processes all available transactions in a single smaller batch.
- How does the system handle extremely long transaction descriptions? Descriptions are truncated to a reasonable limit (500 characters) for AI processing while preserving the full original.

## Requirements *(mandatory)*

### Functional Requirements

**Categorization Flow**
- **FR-001**: System MUST automatically trigger categorization for uncategorized transactions after a successful CSV import
- **FR-002**: System MUST batch transactions for categorization processing with a configurable batch size (default: 50 transactions per batch)
- **FR-003**: System MUST include normalized merchant name, raw description, transaction type (expense vs income based on amount sign), and available category list in categorization requests
- **FR-004**: System MUST only apply automatic categorization when confidence score meets or exceeds the configured threshold (default: 0.7)

**Merchant Normalization**
- **FR-005**: System MUST normalize transaction descriptions by trimming whitespace and collapsing multiple spaces
- **FR-006**: System MUST remove common bank noise tokens from descriptions (e.g., "POS DEBIT", "CHECKCARD", "ACH WITHDRAWAL", "PURCHASE")
- **FR-007**: System MUST extract likely merchant names from normalized descriptions
- **FR-008**: System MUST store both original_description and normalized_merchant for each transaction

**Response Handling**
- **FR-009**: System MUST parse AI responses to extract transaction_id, category_id, and confidence score for each categorization
- **FR-010**: System MUST handle malformed AI responses gracefully without crashing; affected transactions remain uncategorized
- **FR-011**: System MUST extract valid responses from potential markdown formatting or code blocks

**Learning System**
- **FR-012**: System MUST record a categorization rule when a user manually changes a transaction's category
- **FR-013**: System MUST store rules mapping normalized merchant names to category_ids, using substring/contains matching (a rule matches if its merchant pattern is found within the transaction's normalized merchant)
- **FR-014**: System MUST apply learned rules before invoking AI categorization on new imports
- **FR-015**: System MUST skip AI invocation for transactions that match existing rules

**Safety & Privacy**
- **FR-016**: System MUST NOT include account numbers, card numbers, or other sensitive identifiers in categorization requests
- **FR-017**: System MUST enforce configurable timeout limits on AI service calls (default: 120 seconds)
- **FR-018**: System MUST implement retry logic with exponential backoff for transient failures (3 retries max with delays of 2s, 4s, 8s)

**Configuration**
- **FR-019**: System MUST support configuration via environment variables for: AI service path, batch size, confidence threshold, and timeout duration
- **FR-020**: System MUST use sensible defaults when environment variables are not set

**Reliability**
- **FR-021**: System MUST complete imports successfully even when AI categorization fails; transactions remain uncategorized
- **FR-022**: System MUST log categorization metrics: batch count, transaction count, success/failure counts, and duration

### Key Entities

- **Transaction**: Financial record with original_description, normalized_merchant, amount, category_id (nullable), confidence_score (nullable), and categorization_source (rule/ai/manual/none)
- **Category**: Classification for transactions with id and name; predefined set available for categorization
- **CategorizationRule**: User-learned mapping with normalized_merchant pattern, target category_id, and creation timestamp
- **CategorizationBatch**: Processing record with batch_id, transaction_count, success_count, failure_count, duration_ms, and timestamp

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 80% of imported transactions with identifiable merchants receive automatic category assignments on first import
- **SC-002**: Users spend 50% less time manually categorizing transactions compared to no automation
- **SC-003**: After 30 days of use, 60% of new transactions are categorized by learned rules without AI invocation
- **SC-004**: Categorization accuracy (user acceptance rate of AI suggestions) exceeds 85%
- **SC-005**: Import operations complete within 30 seconds for batches of up to 500 transactions, regardless of AI availability
- **SC-006**: Zero data loss or import failures due to AI categorization issues (graceful degradation)

## Clarifications

### Session 2026-01-11

- Q: How should learned rules match against transaction merchants? → A: Substring/contains match (rule merchant found within transaction merchant)
- Q: What retry behavior for transient AI failures? → A: 3 retries max with exponential backoff (2s, 4s, 8s delays)

## Assumptions

- The CSV import pipeline already exists and this feature integrates with it as a post-import step
- Categories are predefined in the system and available for the AI to choose from
- Claude Code CLI (`claude -p`) is installed and accessible on the system where FinTrack runs
- Users have sufficient permissions to configure environment variables for their deployment
- Transaction descriptions from banks contain enough information to identify merchants in most cases
- The confidence threshold of 0.7 provides a reasonable balance between automation and accuracy; this can be tuned
