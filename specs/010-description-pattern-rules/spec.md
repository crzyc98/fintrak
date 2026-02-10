# Feature Specification: Description-Based Pattern Rules for Transaction Categorization

**Feature Branch**: `010-description-pattern-rules`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "When a user manually categorizes a transaction, future imports with a similar description (in the same account) should automatically receive the same category — using description pattern matching as a fallback when no normalized merchant is available."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Auto-Learn Category from Manual Correction (Priority: P1)

A user imports transactions from their Fidelity brokerage account. One transaction reads "DIRECT DEPOSIT Fidelity Bro461026 (Cash)" and is uncategorized. The user manually sets its category to "Income." The system extracts a description pattern (e.g., `DIRECT DEPOSIT Fidelity Bro* (Cash)`) and saves it as a rule scoped to that account. The next month, when "DIRECT DEPOSIT Fidelity Bro458529 (Cash)" is imported into the same account, the system automatically categorizes it as "Income" without user intervention.

**Why this priority**: This is the core value proposition — learn from user corrections so the same type of transaction never needs manual categorization again. Without this, every import cycle requires repetitive manual work.

**Independent Test**: Can be fully tested by manually categorizing a single transaction and verifying that a new import with a similar description in the same account receives the learned category automatically.

**Acceptance Scenarios**:

1. **Given** a transaction with description "DIRECT DEPOSIT Fidelity Bro461026 (Cash)" in account "Fidelity Cash" has no normalized merchant, **When** the user sets its category to "Income," **Then** the system creates a description-based pattern rule scoped to that account.
2. **Given** a description-based pattern rule exists for "DIRECT DEPOSIT Fidelity Bro* (Cash)" → "Income" in account "Fidelity Cash," **When** a new transaction "DIRECT DEPOSIT Fidelity Bro458529 (Cash)" is imported into that account, **Then** it is automatically categorized as "Income."
3. **Given** a transaction has both a normalized merchant AND a description, **When** the user manually changes its category, **Then** a normalized-merchant rule is created (existing behavior) and NO description-based rule is created (to avoid redundancy).

---

### User Story 2 - Pattern Matching During Import and AI Categorization (Priority: P2)

During CSV import or AI-triggered categorization, the system checks description-based pattern rules as a fallback after normalized-merchant rules. This ensures that transactions without a recognizable merchant name but with a consistent description prefix are categorized correctly.

**Why this priority**: The pattern rules only deliver value if they are actually applied during the categorization pipeline. This story ensures the learned rules are used at the right time.

**Independent Test**: Can be tested by creating a description pattern rule manually, then importing a CSV file with a matching transaction and verifying it receives the correct category.

**Acceptance Scenarios**:

1. **Given** no normalized-merchant rule matches a transaction, **When** its description matches a description-based pattern rule for the same account, **Then** the transaction is categorized using that description rule.
2. **Given** both a normalized-merchant rule and a description-based rule could match, **When** the system categorizes the transaction, **Then** the normalized-merchant rule takes precedence.
3. **Given** a description-based rule exists for account A, **When** a transaction with the same description pattern is imported into account B, **Then** the rule does NOT apply (rules are account-scoped).

---

### User Story 3 - Pattern Extraction with Trailing Variation (Priority: P2)

The system intelligently strips trailing variable portions (numeric IDs, reference numbers, check numbers) from transaction descriptions to create generalized patterns. For example, "DIVIDEND Fidelity Bro461026 (Cash)" and "DIVIDEND Fidelity Bro458529 (Cash)" should both match a single rule for "DIVIDEND Fidelity Bro* (Cash)".

**Why this priority**: The quality of pattern extraction directly determines how many future transactions are correctly matched. Poor patterns lead to either too many false positives or too few matches.

**Independent Test**: Can be tested by categorizing a transaction and verifying that the extracted pattern correctly generalizes the variable portions of the description.

**Acceptance Scenarios**:

1. **Given** description "DIRECT DEPOSIT Fidelity Bro461026 (Cash)," **When** a pattern is extracted, **Then** it generalizes the numeric portion to produce a pattern like "DIRECT DEPOSIT Fidelity Bro* (Cash)" that would match similar descriptions.
2. **Given** description "CHECK #1234 DEPOSIT," **When** a pattern is extracted, **Then** variable parts like check numbers are generalized.
3. **Given** description "GROCERY STORE," **When** a pattern is extracted, **Then** the entire description is used as-is (no trailing variable portion to strip).

---

### User Story 4 - User Can View and Manage Description Rules (Priority: P3)

Users can see their description-based pattern rules alongside existing merchant-based rules. They can delete a description rule if it is producing incorrect categorizations.

**Why this priority**: Users need visibility and control over learned rules to correct mistakes and maintain trust in the system.

**Independent Test**: Can be tested by viewing the rules list after creating a description rule and verifying it appears with its account scope, then deleting it and confirming removal.

**Acceptance Scenarios**:

1. **Given** description-based rules exist, **When** the user views the categorization rules, **Then** description rules are displayed alongside merchant rules, clearly indicating they are description-based and which account they apply to.
2. **Given** a description-based rule is producing incorrect categorizations, **When** the user deletes it, **Then** future imports no longer apply that rule.

---

### Edge Cases

- What happens when a transaction description is very short (e.g., "ATM")? The full description is used as the pattern with no generalization.
- What happens when two description rules for the same account would match the same transaction? The most recently created rule takes precedence (consistent with existing merchant-rule behavior).
- What happens when a user changes a transaction's category multiple times? The existing description-based rule for that pattern is updated to the new category rather than creating duplicates.
- What happens when the extracted pattern is identical to one that already exists for the same account? The existing rule's category is updated rather than creating a duplicate.
- What happens when a transaction has an empty description? No description-based rule is created.
- What happens when a user bulk-categorizes multiple transactions? No description-based rules are created — only individual corrections trigger rule learning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST extract a generalized description pattern from a transaction's description when the user manually changes its category and no normalized merchant is available.
- **FR-002**: System MUST store description-based pattern rules with an association to a specific account, the extracted pattern, and the target category.
- **FR-003**: System MUST apply description-based pattern rules during transaction categorization as a fallback after normalized-merchant rules and before AI categorization.
- **FR-004**: System MUST scope description-based pattern rules to the account where the correction was made — rules MUST NOT apply across different accounts.
- **FR-005**: System MUST give normalized-merchant rules higher priority than description-based pattern rules when both could match a transaction.
- **FR-006**: System MUST update an existing description-based rule (same pattern + same account) rather than creating a duplicate when the user re-categorizes a similar transaction.
- **FR-007**: System MUST allow users to view description-based pattern rules alongside merchant-based rules.
- **FR-008**: System MUST allow users to delete description-based pattern rules.
- **FR-009**: System MUST generalize trailing variable portions of descriptions (numeric IDs, reference numbers) when extracting patterns, while preserving the stable prefix and any stable suffix.
- **FR-010**: System MUST NOT create a description-based rule when the transaction has a normalized merchant (the existing merchant-rule behavior handles this case).
- **FR-011**: System MUST NOT create a description-based rule when the transaction description is empty or blank.
- **FR-012**: System MUST record the categorization source as a distinct value when a transaction is categorized via a description-based pattern rule, to distinguish it from merchant-based rule matches.
- **FR-013**: System MUST perform description pattern matching case-insensitively, consistent with existing merchant-rule matching behavior.
- **FR-014**: System MUST NOT create description-based rules from bulk category operations — only individual transaction category corrections trigger rule creation, consistent with existing merchant-rule behavior.

### Key Entities

- **Description Pattern Rule**: A learned categorization rule consisting of a generalized description pattern, the target category, and the account it applies to. Each combination of pattern + account is unique.
- **Description Pattern**: A generalized version of a transaction description where variable trailing portions (numeric IDs, reference numbers) are replaced with wildcards, while stable prefixes and suffixes are preserved.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a user manually categorizes a transaction, the next import containing a similar transaction description in the same account is automatically categorized correctly without user intervention.
- **SC-002**: Description-based rules do not interfere with existing merchant-based rules — merchant rules always take precedence when both could apply.
- **SC-003**: The number of transactions requiring repeated manual categorization for recurring description patterns drops to zero after the first correction.
- **SC-004**: Users can view and delete description-based rules within the same interface used for merchant rules.

## Clarifications

### Session 2026-02-10

- Q: Should description pattern matching be case-sensitive or case-insensitive? → A: Case-insensitive — patterns match regardless of casing, consistent with existing merchant rules.
- Q: Should bulk category operations create description-based rules? → A: No — bulk category changes do NOT create description rules, consistent with existing merchant-rule behavior.

## Assumptions

- The existing categorization source field on transactions can accommodate a new source value for description-based rule matches.
- Account-scoping is sufficient granularity — the same description pattern in different accounts may legitimately map to different categories (e.g., "TRANSFER" in a checking account vs. brokerage account).
- Trailing numeric generalization (stripping sequences of digits and replacing with wildcards) covers the majority of recurring transaction description variations seen in bank and brokerage CSV exports.
- The pattern extraction does not need to be configurable by the user — a single, deterministic algorithm is sufficient for the initial release.
- Existing merchant-based rules continue to work unchanged; description-based rules are purely additive.

## Dependencies

- Existing categorization rules system (categorization_rules table, rule_service.py)
- Existing transaction update endpoint (PUT /api/transactions/{id})
- Existing CSV import pipeline
- Existing AI categorization pipeline (categorization_service.py)
