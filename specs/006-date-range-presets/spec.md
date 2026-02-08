# Feature Specification: Date Range Presets

**Feature Branch**: `006-date-range-presets`
**Created**: 2026-02-01
**Status**: Draft
**Input**: Add Date range presets in filters (This Month, Last 30 Days, YTD)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quick Filter by Common Time Periods (Priority: P1)

As a user viewing transactions, I want to quickly filter to common time periods without manually entering dates, so I can efficiently review my spending for relevant timeframes.

**Why this priority**: This is the core functionality. Users spend most of their time looking at recent transactions or monthly summaries. Quick access to common date ranges dramatically improves workflow speed.

**Independent Test**: Can be fully tested by clicking a preset button and verifying transactions are filtered to the correct date range.

**Acceptance Scenarios**:

1. **Given** I am on the Transactions page with the filter panel open, **When** I click "This Month", **Then** transactions are filtered to show only transactions from the first day of the current month through today.

2. **Given** I am on the Transactions page, **When** I click "Last 30 Days", **Then** transactions are filtered to show transactions from 30 days ago through today.

3. **Given** I am on the Transactions page, **When** I click "YTD" (Year to Date), **Then** transactions are filtered to show transactions from January 1st of the current year through today.

---

### User Story 2 - Visual Feedback for Active Preset (Priority: P2)

As a user, I want to see which preset is currently active, so I understand what time period I'm viewing.

**Why this priority**: Provides essential context for the data being displayed, preventing confusion.

**Independent Test**: Can be tested by selecting a preset and verifying visual indicator appears.

**Acceptance Scenarios**:

1. **Given** I select "This Month" preset, **When** the filter is applied, **Then** the "This Month" button shows an active/selected state (highlighted).

2. **Given** I have "This Month" preset active, **When** I manually change the date_from or date_to fields, **Then** the preset indicator is cleared (no preset appears selected).

---

### User Story 3 - Clear Preset and Return to All Transactions (Priority: P2)

As a user, I want to easily clear the date filter and see all transactions again.

**Why this priority**: Users need an escape hatch to remove filters.

**Independent Test**: Can be tested by selecting a preset, then clicking clear and verifying all transactions appear.

**Acceptance Scenarios**:

1. **Given** I have a date preset active, **When** I click "Clear Filters" or a dedicated clear button, **Then** the date range filter is removed and all transactions are shown.

---

### Edge Cases

- What happens when "This Month" is selected on the 1st of the month? → Should show only transactions from today (Jan 1 through Jan 1).
- What happens when "YTD" is selected on January 1st? → Should show only transactions from today.
- What happens when there are no transactions in the selected date range? → Empty state message should display.
- How do presets interact with other active filters (account, category)? → Presets should combine with other filters (AND logic).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide clickable preset buttons for common date ranges in the transaction filter panel.
- **FR-002**: System MUST include the following presets: "This Month", "Last Month", "Last 30 Days", and "YTD".
- **FR-003**: Selecting a preset MUST automatically populate the date_from and date_to filter fields with the calculated dates.
- **FR-004**: System MUST visually indicate which preset (if any) is currently active.
- **FR-005**: Manually editing date fields MUST clear the active preset indicator.
- **FR-006**: Presets MUST combine with other active filters (account, category, reviewed status) using AND logic.
- **FR-007**: The "Clear Filters" button MUST also clear any active date preset.
- **FR-008**: Preset buttons MUST be displayed as a horizontal row above the From/To date input fields in the filter panel.

### Key Entities

- **DatePreset**: A named preset with a calculation function that returns { date_from, date_to } based on current date.

## Clarifications

### Session 2026-02-01

- Q: Should we include any additional presets beyond the three specified? → A: Add "Last Month" preset (previous calendar month)
- Q: Where should the date preset buttons be placed in the filter panel UI? → A: Above the From/To date inputs (horizontal row of buttons)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can filter to a common date range with a single click (vs. 2 date field interactions previously).
- **SC-002**: Preset selection applies filter and updates transaction list within 500ms.
- **SC-003**: Active preset state is visually distinguishable from inactive presets.
