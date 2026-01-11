# Feature Specification: Transactions Review Workflow

**Feature Branch**: `004-review-workflow`
**Created**: 2026-01-11
**Status**: Draft
**Input**: User description: "Build the Transactions to Review workflow and dashboard widget for FinTrack"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Review Queue (Priority: P1)

As a FinTrack user, I want to see a list of unreviewed transactions grouped by day so that I can quickly identify and process recent transactions that need my attention.

**Why this priority**: This is the foundational capability - users cannot process transactions for review without first being able to see which ones need attention. The grouped-by-day view provides natural organization for how users think about recent activity.

**Independent Test**: Can be fully tested by navigating to the review queue (dashboard widget or dedicated page) and verifying that unreviewed transactions display grouped by day with most recent first, showing "Today", "Yesterday", and older dates.

**Acceptance Scenarios**:

1. **Given** I have 20 unreviewed transactions across 5 days, **When** I view the review queue, **Then** I see transactions grouped under date headers: "Today", "Yesterday", and formatted dates for older transactions
2. **Given** I have no unreviewed transactions, **When** I view the review queue, **Then** I see an empty state message indicating all transactions have been reviewed
3. **Given** I have 100+ unreviewed transactions, **When** I view the review queue, **Then** I see a limited set (configurable, default 50) with an option to load more

---

### User Story 2 - Bulk Mark as Reviewed (Priority: P1)

As a FinTrack user, I want to select multiple transactions and mark them all as reviewed at once so that I can quickly process large batches without clicking each one individually.

**Why this priority**: Bulk actions are the primary mechanism for efficient review - marking transactions one at a time would negate the value of a review workflow.

**Independent Test**: Can be fully tested by selecting 10 transactions using checkboxes, clicking "Mark Reviewed", and verifying all 10 are removed from the queue and their reviewed status is true.

**Acceptance Scenarios**:

1. **Given** I have selected 5 unreviewed transactions, **When** I click "Mark Reviewed", **Then** all 5 transactions are marked as reviewed atomically and removed from the queue
2. **Given** I am processing transactions, **When** a bulk operation fails, **Then** none of the transactions are modified and I see a clear error message explaining the failure
3. **Given** I have selected transactions across multiple date groups, **When** I mark them reviewed, **Then** the date groups update to reflect remaining transactions (empty groups are hidden)

---

### User Story 3 - Quick Category Assignment (Priority: P1)

As a FinTrack user, I want to quickly assign or change the category of selected transactions from the review queue so that I can categorize and review in a single workflow.

**Why this priority**: Category assignment is tightly coupled with review - users typically review a transaction to confirm or correct its category. Combining these actions makes the workflow significantly faster.

**Independent Test**: Can be fully tested by selecting 3 transactions, choosing a category from the dropdown, and verifying all 3 are assigned that category.

**Acceptance Scenarios**:

1. **Given** I have selected 3 transactions, **When** I choose "Groceries" from the category dropdown, **Then** all 3 transactions are assigned to "Groceries" atomically
2. **Given** I have selected transactions with different existing categories, **When** I assign a new category, **Then** all selected transactions receive the new category (overwriting previous)
3. **Given** I am assigning categories, **When** I select transactions and assign a category, **Then** the transactions remain selected so I can also mark them reviewed

---

### User Story 4 - Select All in Date Group (Priority: P2)

As a FinTrack user, I want to select all transactions within a date group at once so that I can quickly review an entire day's transactions together.

**Why this priority**: Provides efficiency for users who review by day, a common pattern. Not essential for basic functionality but significantly improves workflow speed.

**Independent Test**: Can be fully tested by clicking the "select all" checkbox on a date group header and verifying all transactions in that group become selected.

**Acceptance Scenarios**:

1. **Given** I see a date group with 8 transactions, **When** I click the select-all checkbox for that group, **Then** all 8 transactions in the group are selected
2. **Given** I have selected all transactions in a group, **When** I click the select-all checkbox again, **Then** all transactions in the group are deselected
3. **Given** I have selected some but not all transactions in a group, **When** I view the group header checkbox, **Then** it shows an indeterminate state

---

### User Story 5 - Add Notes in Bulk (Priority: P2)

As a FinTrack user, I want to add a note to multiple selected transactions at once so that I can annotate related transactions efficiently.

**Why this priority**: Notes are a secondary action compared to categorization and marking reviewed, but bulk notes are valuable for grouping related transactions (e.g., "Business trip expenses").

**Independent Test**: Can be fully tested by selecting 5 transactions, adding a note "Conference expenses", and verifying all 5 have that note appended.

**Acceptance Scenarios**:

1. **Given** I have selected 3 transactions, **When** I add the note "Team lunch", **Then** all 3 transactions have "Team lunch" appended to their notes
2. **Given** a transaction already has notes, **When** I add a bulk note, **Then** the new note is appended with a separator (newline) rather than replacing existing notes
3. **Given** I add a bulk note, **When** the operation completes, **Then** I see confirmation of how many transactions were updated

---

### User Story 6 - Dashboard Review Widget (Priority: P2)

As a FinTrack user, I want to see a compact "Transactions to Review" widget on my dashboard so that I can monitor and quickly access my review queue from the main view.

**Why this priority**: The dashboard widget provides at-a-glance visibility and quick access, but users can still use the dedicated review page for full functionality.

**Independent Test**: Can be fully tested by viewing the dashboard and verifying the widget shows a count of unreviewed transactions with the most recent few items displayed.

**Acceptance Scenarios**:

1. **Given** I have 25 unreviewed transactions, **When** I view the dashboard, **Then** I see a widget showing "25 to review" with the 5 most recent transactions listed
2. **Given** I have 0 unreviewed transactions, **When** I view the dashboard, **Then** I see the widget with a "All caught up!" message
3. **Given** I click on the widget, **When** the navigation completes, **Then** I am taken to the full review page with the complete review queue

---

### User Story 7 - Dedicated Review Page (Priority: P3)

As a FinTrack user, I want a dedicated review page with full-screen focus so that I can efficiently process large batches of transactions without distractions.

**Why this priority**: Power users benefit from a focused interface, but the core functionality works via the dashboard widget. This is an enhancement for efficiency.

**Independent Test**: Can be fully tested by navigating to the dedicated review page and verifying all review actions are available in a streamlined interface.

**Acceptance Scenarios**:

1. **Given** I navigate to the review page, **When** the page loads, **Then** I see the full review queue with all bulk action controls prominently displayed
2. **Given** I am on the review page with 200 transactions, **When** I scroll or interact, **Then** the interface remains responsive (no lag or freezing)
3. **Given** I complete reviewing all transactions, **When** the queue is empty, **Then** I see a success state with an option to return to the dashboard

---

### Edge Cases

- What happens when a transaction is deleted while selected in the review queue? The selection state is cleared for that transaction and the queue refreshes.
- What happens when another session marks a transaction as reviewed while I'm viewing it? Upon my next action, the queue refreshes and that transaction is no longer visible.
- How does the system handle slow networks during bulk operations? The UI shows a loading state, disables controls to prevent double-submission, and displays timeout errors after 30 seconds.
- What happens when bulk operation partially succeeds (some transactions fail)? The entire operation is atomic - all succeed or all fail with rollback.
- What happens when user selects 500+ transactions for bulk operation? The system processes them atomically but may show a progress indicator for operations exceeding 2 seconds.

## Requirements *(mandatory)*

### Functional Requirements

**Review Queue**
- **FR-001**: System MUST provide an endpoint to retrieve unreviewed transactions (reviewed=false) ordered by date descending
- **FR-002**: System MUST support grouping transactions by day with labels "Today", "Yesterday", and individual formatted dates for older transactions (e.g., "Jan 8", "Jan 7")
- **FR-003**: System MUST support configurable result limits (default 50) with pagination for loading additional transactions
- **FR-004**: System MUST return transaction count for the review queue without fetching all records

**Bulk Operations**
- **FR-005**: System MUST provide a bulk update endpoint accepting a list of transaction IDs and an operation type
- **FR-006**: System MUST support bulk operations: mark_reviewed, set_category, add_note
- **FR-007**: System MUST execute bulk operations atomically (all-or-nothing transaction)
- **FR-008**: System MUST validate all transaction IDs exist before executing bulk operations
- **FR-009**: System MUST validate category_id exists when performing set_category operation
- **FR-010**: System MUST return the count of affected transactions on successful bulk operations
- **FR-010a**: System MUST enforce a maximum of 500 transactions per bulk operation request and reject requests exceeding this limit with a clear error

**UI Components**
- **FR-011**: Users MUST be able to select individual transactions via checkboxes
- **FR-012**: Users MUST be able to select/deselect all transactions within a date group via a group header checkbox
- **FR-013**: Users MUST see an indeterminate state on group checkboxes when only some transactions are selected
- **FR-014**: Users MUST be able to invoke bulk actions (mark reviewed, set category, add note) from a persistent action bar
- **FR-015**: Users MUST see the count of currently selected transactions
- **FR-016**: System MUST disable action controls and show loading state during bulk operations

**Dashboard Widget**
- **FR-017**: Dashboard MUST display a "Transactions to Review" widget showing the count of unreviewed transactions
- **FR-018**: Widget MUST display up to 5 most recent unreviewed transactions as a preview
- **FR-019**: Widget MUST provide navigation to the full review page
- **FR-020**: Widget MUST show an empty state when no transactions need review

**Data Integrity**
- **FR-021**: System MUST set reviewed_at timestamp when marking transactions as reviewed via bulk operations
- **FR-022**: System MUST append notes with a newline separator when using add_note on transactions with existing notes
- **FR-023**: System MUST update categorization_source to 'manual' when category is changed via set_category bulk operation

### Key Entities

- **Transaction** (existing): Financial record with reviewed flag, reviewed_at timestamp, category_id, and notes. The review queue filters on reviewed=false.
- **BulkOperationRequest**: Contains list of transaction IDs, operation type (mark_reviewed, set_category, add_note), and operation-specific payload (category_id for set_category, note text for add_note).
- **BulkOperationResponse**: Contains operation result status, count of affected transactions, and error details if applicable.
- **ReviewQueueResponse**: Contains grouped transactions (by date), total count, and pagination metadata.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can process (review and categorize) 50 transactions in under 2 minutes using bulk actions
- **SC-002**: Review queue loads and displays within 1 second for up to 200 transactions
- **SC-003**: Bulk operations complete within 3 seconds for up to 100 transactions
- **SC-004**: 90% of users can successfully use bulk actions without requiring help or documentation
- **SC-005**: Interface remains responsive (no perceptible lag) when displaying 200+ transactions in the review queue
- **SC-006**: Zero partial failures - bulk operations either complete fully or fail with clear error messaging

## Clarifications

### Session 2026-01-11

- Q: What is the maximum number of transactions allowed per bulk operation? → A: 500 transactions maximum
- Q: How should dates older than "Yesterday" be grouped? → A: Individual days (e.g., "Jan 8", "Jan 7", "Jan 6"...)

## Assumptions

- The transaction model from 002-transactions-core is complete with reviewed, reviewed_at, category_id, and notes fields
- The AI categorization from 003-ai-categorization creates transactions with reviewed=false by default
- Users primarily review transactions to verify/correct AI categorization results
- A single user context is assumed (no multi-user permissions for this spec)
- The dashboard exists as a primary navigation destination where the widget can be placed
- Most review sessions involve processing transactions from the last few days (hence day-grouping as default)

## Out of Scope

- Keyboard shortcuts for power users
- Custom sorting options for the review queue (always most recent first)
- Filter combinations within the review queue (e.g., filter by category while reviewing)
- Undo functionality for bulk operations
- Scheduling or auto-review based on rules
- Mobile-responsive design optimizations
