# Feature Specification: Auto-Create Rules from AI Classifications

**Feature Branch**: `015-auto-ai-rules`
**Created**: 2026-02-11
**Status**: Implemented
**Input**: User description: "Auto-create categorization rules from high-confidence AI classification results to reduce API usage"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Automatic Rule Learning from AI Results (Priority: P1)

As a user, when I run AI classification on my transactions, the system automatically creates merchant-based categorization rules from high-confidence results. The next time I import transactions from the same merchants, they are categorized instantly by rules without needing another AI call.

**Why this priority**: This is the core value of the feature — making the system self-improving so AI costs decrease over time without requiring manual user corrections.

**Independent Test**: Can be tested by running AI classification on a batch of transactions, then importing new transactions from the same merchants and verifying they are categorized by rules (not AI).

**Acceptance Scenarios**:

1. **Given** the AI classifies a transaction for "Starbucks" with confidence 0.95, **When** the classification completes, **Then** a merchant rule is automatically created mapping "Starbucks" to the assigned category.
2. **Given** a merchant rule was auto-created from a previous AI run, **When** new transactions from the same merchant are imported and classification is triggered, **Then** those transactions are categorized by the rule without making an AI call.
3. **Given** the AI classifies a transaction with confidence 0.75 (below the auto-rule threshold), **When** the classification completes, **Then** no rule is automatically created for that merchant.

---

### User Story 2 - Description Pattern Rule Learning (Priority: P2)

As a user, when AI classifies transactions that have no normalized merchant (e.g., bank transfers, direct debits), the system automatically creates description pattern rules from high-confidence results. Future similar transactions are categorized by these patterns without AI.

**Why this priority**: Extends the rule-learning benefit to transactions without clear merchant names, covering a secondary but meaningful portion of transactions.

**Independent Test**: Can be tested by running AI classification on transactions with no merchant info, then importing similar transactions and verifying pattern-based rule matching.

**Acceptance Scenarios**:

1. **Given** the AI classifies a transaction with description "TRANSFER TO SAVINGS" (no normalized merchant) with confidence 0.92, **When** the classification completes, **Then** a description pattern rule is created for that pattern and account.
2. **Given** a description pattern rule was auto-created, **When** a new transaction with a similar description is imported for the same account, **Then** it is categorized by the pattern rule without AI.

---

### User Story 3 - Rule Deduplication (Priority: P2)

As a user, I don't want duplicate rules cluttering the system. If a rule already exists for a merchant or pattern, the system should not create another one when AI classifies similar transactions again.

**Why this priority**: Prevents rule table bloat and potential conflicts. Essential for system health but not the primary value driver.

**Independent Test**: Can be tested by running AI classification twice on overlapping transaction sets and verifying no duplicate rules are created.

**Acceptance Scenarios**:

1. **Given** a merchant rule already exists for "Starbucks" mapping to "Dining Out", **When** the AI classifies another Starbucks transaction with high confidence, **Then** no new rule is created.
2. **Given** a merchant rule exists for "Starbucks" mapping to "Dining Out" and AI classifies a Starbucks transaction to a different category, **When** the classification completes, **Then** the existing rule is preserved (not overwritten) since manual corrections take precedence.

---

### User Story 4 - Distinguishable Rule Sources (Priority: P3)

As a user, I want to know which rules were created automatically by AI versus which I created through manual corrections, so I can audit and manage my rules confidently.

**Why this priority**: Provides transparency and auditability but doesn't affect core categorization functionality.

**Independent Test**: Can be tested by creating rules via both methods and verifying each has the correct source identifier.

**Acceptance Scenarios**:

1. **Given** a rule is auto-created from an AI classification, **When** viewing rules, **Then** it is identifiable as AI-generated (distinct from manually created rules).
2. **Given** a user manually corrects a transaction's category, **When** a rule is created from that correction, **Then** it retains the "manual" source designation.

---

### Edge Cases

- What happens when the AI assigns different categories to the same merchant across different transactions in the same batch? The system uses the highest-confidence result for rule creation.
- What happens when a user has previously created a manual rule for a merchant and then AI tries to auto-create a rule for the same merchant? The existing manual rule takes precedence; no AI rule is created.
- What happens when AI returns a new category that doesn't exist yet? The category is created first (existing behavior), then the rule is created referencing that new category.
- What happens when description pattern extraction yields an empty or overly generic pattern? No rule is created to avoid false matches.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST automatically create merchant-based categorization rules when AI classifies a transaction with confidence at or above the auto-rule threshold and the transaction has a normalized merchant name.
- **FR-002**: System MUST automatically create description pattern rules when AI classifies a transaction with confidence at or above the auto-rule threshold and the transaction has no normalized merchant but has a description.
- **FR-003**: System MUST NOT create a rule if one already exists for the same merchant pattern or description pattern (within the same account scope for description rules).
- **FR-004**: System MUST NOT overwrite or conflict with rules previously created through manual user corrections.
- **FR-005**: System MUST mark auto-created rules with a distinct source identifier to differentiate them from manually created rules.
- **FR-006**: The confidence threshold for automatic rule creation MUST default to 0.9 and be configurable.
- **FR-007**: When multiple AI results in the same batch map the same merchant to different categories, the system MUST use the result with the highest confidence for rule creation.
- **FR-008**: System MUST NOT create description pattern rules from overly generic or empty patterns.

### Key Entities

- **Categorization Rule**: A merchant-to-category mapping used for instant, deterministic transaction classification. Key attributes: merchant pattern, category, source (manual vs. AI-generated), creation date.
- **Description Pattern Rule**: An account-scoped description pattern-to-category mapping for transactions without clear merchant names. Key attributes: pattern, account, category, source, creation date.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After the first AI classification run on a dataset, at least 80% of recurring merchants have auto-created rules, reducing AI calls needed for the second run by 70% or more.
- **SC-002**: No duplicate rules are created across multiple classification runs on overlapping data.
- **SC-003**: Manual rules are never overwritten or conflicted with by auto-created AI rules.
- **SC-004**: Users can identify which rules were auto-created versus manually created.

## Assumptions

- The existing confidence scoring from the Gemini API is reliable enough at the 0.9 threshold to produce accurate rules without user verification.
- The existing rule creation service interfaces are sufficient for auto-rule creation without modification to their core logic.
- The existing pattern extraction logic produces sufficiently specific patterns for auto-rule creation.
- Rule creation volume from a single AI batch (up to 50 transactions) will not cause performance issues.
