# Feature Specification: Transactions Core

**Feature Branch**: `002-transactions-core`
**Created**: 2026-01-11
**Status**: Draft
**Input**: User description: "Implement Transactions core (data model + transaction list) for FinTrack"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View All Transactions (Priority: P1)

As a FinTrack user, I want to view all my transactions in a list so that I can see my complete financial activity at a glance.

**Why this priority**: This is the foundational capability - without viewing transactions, no other functionality (filtering, editing, categorizing) is useful.

**Independent Test**: Can be fully tested by navigating to the transactions page and verifying that transactions display in a table sorted by date (most recent first), showing date, description, amount, account, category, and review status.

**Acceptance Scenarios**:

1. **Given** I have transactions in my account, **When** I navigate to the transactions page, **Then** I see all transactions displayed in a table sorted by date descending
2. **Given** I have no transactions, **When** I navigate to the transactions page, **Then** I see an empty state message indicating no transactions exist
3. **Given** I have more transactions than fit on one page, **When** I view the transactions page, **Then** I can navigate through pages or scroll to load more transactions

---

### User Story 2 - Filter Transactions (Priority: P1)

As a FinTrack user, I want to filter my transactions by various criteria so that I can quickly find specific transactions or analyze spending patterns.

**Why this priority**: Filtering is essential for usability once transaction volume grows - users need to narrow down what they're looking at.

**Independent Test**: Can be fully tested by applying various filter combinations and verifying only matching transactions appear.

**Acceptance Scenarios**:

1. **Given** I have transactions across multiple accounts, **When** I filter by a specific account, **Then** I see only transactions from that account
2. **Given** I have transactions in various categories, **When** I filter by a specific category, **Then** I see only transactions with that category
3. **Given** I have transactions with various amounts, **When** I filter by amount range, **Then** I see only transactions within that range
4. **Given** I have transactions across various dates, **When** I filter by date range, **Then** I see only transactions within that date range
5. **Given** I have reviewed and unreviewed transactions, **When** I filter by review status, **Then** I see only transactions matching that status
6. **Given** I am viewing filtered results, **When** I clear filters, **Then** I see all transactions again

---

### User Story 3 - Search Transactions by Description (Priority: P2)

As a FinTrack user, I want to search transactions by description so that I can quickly find specific merchants or transaction types.

**Why this priority**: Search is a common and fast way to find transactions, complementing the filter functionality.

**Independent Test**: Can be fully tested by entering search terms and verifying matching transactions appear.

**Acceptance Scenarios**:

1. **Given** I have transactions with various descriptions, **When** I search for a keyword, **Then** I see transactions where the description contains that keyword
2. **Given** I search for a term with no matches, **When** the search completes, **Then** I see an empty result with a helpful message
3. **Given** I have active filters, **When** I also search by description, **Then** both the filter and search criteria are applied together

---

### User Story 4 - Edit Transaction Category (Priority: P1)

As a FinTrack user, I want to edit the category of a transaction inline so that I can quickly organize my spending without navigating away from the list.

**Why this priority**: Categorization is core to financial tracking and budgeting - users need to assign/correct categories frequently.

**Independent Test**: Can be fully tested by clicking on a transaction's category, selecting a new category, and verifying the change persists.

**Acceptance Scenarios**:

1. **Given** I see a transaction in the list, **When** I click on the category field, **Then** I see a dropdown of available categories
2. **Given** I am editing a category, **When** I select a new category, **Then** the transaction updates immediately and the change persists
3. **Given** I am editing a category, **When** I click away without selecting, **Then** the edit is cancelled and original value remains

---

### User Story 5 - Edit Transaction Notes (Priority: P2)

As a FinTrack user, I want to add or edit notes on a transaction inline so that I can record additional context about specific transactions.

**Why this priority**: Notes provide context but are not essential for core functionality.

**Independent Test**: Can be fully tested by clicking on a transaction's notes field, entering text, and verifying the change persists.

**Acceptance Scenarios**:

1. **Given** I see a transaction in the list, **When** I click on the notes field, **Then** I can enter or edit text
2. **Given** I am editing notes, **When** I finish editing (blur or enter), **Then** the notes are saved and persist
3. **Given** a transaction has notes, **When** I view the transaction list, **Then** I see an indicator that notes exist

---

### User Story 6 - Toggle Transaction Review Status (Priority: P2)

As a FinTrack user, I want to mark transactions as reviewed so that I can track which transactions I have verified and categorized correctly.

**Why this priority**: Review status helps users track their progress through transaction review but is not essential for basic functionality.

**Independent Test**: Can be fully tested by clicking the review toggle and verifying the status changes and persists.

**Acceptance Scenarios**:

1. **Given** I see an unreviewed transaction, **When** I click the review toggle, **Then** the transaction is marked as reviewed with a timestamp
2. **Given** I see a reviewed transaction, **When** I click the review toggle, **Then** the transaction is marked as unreviewed and the reviewed timestamp is cleared
3. **Given** I have toggled review status, **When** I refresh the page, **Then** the review status persists

---

### User Story 7 - Delete Transaction (Priority: P3)

As a FinTrack user, I want to delete a transaction so that I can remove erroneous or duplicate entries.

**Why this priority**: Delete is useful but less commonly needed; most corrections are category/note edits.

**Independent Test**: Can be fully tested by selecting a transaction, confirming deletion, and verifying it no longer appears.

**Acceptance Scenarios**:

1. **Given** I see a transaction in the list, **When** I click delete, **Then** I see a confirmation prompt
2. **Given** I see the confirmation prompt, **When** I confirm deletion, **Then** the transaction is removed and no longer appears in the list
3. **Given** I see the confirmation prompt, **When** I cancel, **Then** the transaction remains unchanged

---

### Edge Cases

- What happens when a user tries to filter with invalid date range (start date after end date)? System should show validation error and not apply the filter.
- What happens when a user tries to edit a transaction that was deleted by another session? System should show an error message and refresh the list.
- How does the system handle very large transaction lists (10,000+ transactions)? Pagination ensures only a subset loads at once; server-side filtering keeps responses fast.
- What happens when network connection is lost during an edit? Changes are not saved and user sees an error indicating the save failed.
- What happens when the user filters and gets no results? System shows a helpful empty state message indicating no transactions match the criteria.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store transactions with the following fields: id, account_id, date, description, original_description, amount, category_id (nullable), reviewed (boolean, default false), reviewed_at (nullable), notes (nullable), created_at
- **FR-002**: System MUST maintain referential integrity between transactions and accounts (account_id references existing accounts)
- **FR-003**: System MUST maintain referential integrity between transactions and categories (category_id references existing categories when not null)
- **FR-004**: System MUST provide a transaction list endpoint that returns transactions sorted by date descending by default
- **FR-005**: System MUST support filtering transactions by: account_id, category_id, date_from, date_to, amount_min, amount_max, and reviewed status
- **FR-006**: System MUST support searching transactions by description (partial match, case-insensitive)
- **FR-007**: System MUST support pagination of transaction results to handle large datasets efficiently
- **FR-008**: System MUST provide an endpoint to update transaction fields: category_id, reviewed status, and notes
- **FR-009**: System MUST automatically set reviewed_at timestamp when reviewed is set to true, and clear it when set to false
- **FR-010**: System MUST provide an endpoint to delete individual transactions
- **FR-011**: System MUST perform all filtering on the server side to ensure fast response times regardless of total transaction count
- **FR-012**: Users MUST be able to edit category and notes inline without navigating away from the transaction list
- **FR-013**: Users MUST see changes reflected immediately in the UI after successful edits
- **FR-014**: Users MUST be shown a confirmation prompt before deleting a transaction
- **FR-015**: System MUST display amounts with appropriate formatting (currency symbol, decimal places)
- **FR-016**: System MUST display dates in a user-readable format

### Key Entities

- **Transaction**: Represents a single financial transaction associated with an account. Contains date, description, amount, optional category assignment, review status, and notes. Links to exactly one Account and optionally one Category.
- **Account** (existing): The financial account associated with the transaction (e.g., checking account, credit card).
- **Category** (existing): The spending/income category assigned to a transaction for budgeting and analysis purposes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view their complete transaction list within 2 seconds of page load, regardless of total transaction count (pagination ensures this)
- **SC-002**: Filtered transaction results return within 1 second when applying any combination of filters
- **SC-003**: Inline edits (category, notes, review status) persist and reflect in the UI within 500ms of user action
- **SC-004**: System supports accounts with 10,000+ transactions without degradation in list view performance
- **SC-005**: Users can successfully filter, search, and find specific transactions within 3 clicks/actions
- **SC-006**: All CRUD operations on transactions complete successfully with appropriate feedback to the user
- **SC-007**: Transaction list pagination allows users to navigate through all their transactions without loading entire dataset at once

## Assumptions

- The existing Accounts and Categories functionality from the prior spec is complete and available for use
- Users access the system through a web browser on desktop or laptop (responsive design for mobile is not in scope for this spec)
- Transaction amounts can be positive (income/credits) or negative (expenses/debits)
- The original_description field preserves the raw description from import, while description can be edited by users
- A single user context is assumed (no multi-user/permissions considerations for this spec)
- Currency formatting follows a standard format (assumes single currency; multi-currency is out of scope)

## Out of Scope

- CSV import functionality (covered in next spec)
- AI categorization and merchant normalization
- Bulk edit operations
- Transaction splitting
- Recurring transaction detection
- Export functionality
- Mobile-responsive design
- Multi-currency support
