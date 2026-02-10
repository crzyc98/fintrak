# Feature Specification: Live Net Worth Dashboard

**Feature Branch**: `008-live-networth`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Wire up the NetWorth dashboard component to use real account data from the backend API instead of hardcoded values."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Real Net Worth on Dashboard (Priority: P1)

A user opens the FinTrak dashboard and sees their actual net worth summary — total assets, total debts, and net worth — calculated from their real account balances. The values update automatically whenever accounts or balances change.

**Why this priority**: This is the core value of the feature. Without real data, the dashboard is misleading and unusable for financial tracking.

**Independent Test**: Can be fully tested by adding accounts with known balances and verifying the dashboard displays the correct totals.

**Acceptance Scenarios**:

1. **Given** a user has accounts with balances (e.g., Checking: $10,000, Savings: $25,000, Credit Card: -$3,000), **When** they view the dashboard, **Then** the Net Worth card shows Assets: $35,000, Debts: $3,000, and the values match the sum of their real account balances.
2. **Given** a user updates an account balance, **When** they return to the dashboard, **Then** the Net Worth card reflects the updated totals.
3. **Given** a user has no accounts, **When** they view the dashboard, **Then** the Net Worth card shows $0 for both assets and debts.

---

### User Story 2 - Replace Mock Chart with Meaningful Visualization (Priority: P2)

The historical net worth chart currently uses fake mock data. Since there is no historical balance tracking yet, the chart should be replaced or adapted to display something meaningful based on available data, or hidden until historical data is available.

**Why this priority**: A chart with fake data is worse than no chart — it misleads users. However, the summary totals (P1) are more critical than the chart.

**Independent Test**: Can be tested by verifying the chart area does not display fabricated data points.

**Acceptance Scenarios**:

1. **Given** no historical balance data is available, **When** the user views the Net Worth card, **Then** the chart area is hidden or shows a placeholder message encouraging the user to track balances over time.
2. **Given** the mock data import is removed, **When** the dashboard loads, **Then** no references to mock net worth data remain in the component.

---

### Edge Cases

- What happens when a user has only asset accounts and no debt accounts? The debts section should display $0.
- What happens when a user has only debt accounts and no asset accounts? The assets section should display $0.
- What happens when all account balances are null (newly created, no balance snapshots)? Totals should display $0.
- What happens when the API request to fetch accounts fails? The component should show an error state or fallback gracefully.
- What happens with negative liability balances (e.g., credit card overpayment)? These should reduce the total debt, consistent with AccountsView behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Net Worth dashboard card MUST display total assets calculated from all real asset accounts (Checking, Savings, Investment, Real Estate, Crypto).
- **FR-002**: The Net Worth dashboard card MUST display total debts calculated from all real liability accounts (Credit, Loan).
- **FR-003**: The displayed values MUST update when the user navigates to the dashboard after account or balance changes.
- **FR-004**: The component MUST handle the loading state while account data is being fetched.
- **FR-005**: The component MUST handle the error state if the accounts API request fails.
- **FR-006**: The component MUST display $0 for assets and debts when no accounts exist.
- **FR-007**: The mock data import (`NET_WORTH_DATA` from `mockData`) MUST be removed from the component.
- **FR-008**: The percentage change badges (32%, 16%) MUST be removed since there is no historical data to compute them from.
- **FR-009**: The historical chart MUST be hidden or replaced with a placeholder until real historical data tracking is implemented.
- **FR-010**: The timeframe selector buttons (1W, 1M, 3M, etc.) MUST be removed or hidden since they serve no purpose without historical data.

### Key Entities

- **Account**: Represents a financial account with a type (asset or liability), current balance, and institution. The `is_asset` boolean determines whether the balance contributes to assets or debts.
- **Net Worth Summary**: A derived view showing total assets, total debts, and net worth (assets minus debts), computed from all accounts.

## Assumptions

- The existing `/api/accounts` endpoint returns all accounts with their `current_balance` and `is_asset` fields, which is sufficient for computing net worth totals.
- The `fetchAccounts` function already exists in the frontend API service and can be reused directly.
- The totals computation logic in `AccountsView` (filtering by `is_asset`, summing `current_balance`) is the correct pattern to follow.
- Historical net worth tracking (for the chart) is a separate future feature and out of scope for this specification.
- The currency format should be consistent with the rest of the application (USD with dollar sign).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Net Worth card displays asset and debt totals that exactly match the sum of real account balances, verifiable by comparing with the Accounts view totals.
- **SC-002**: The Net Worth card loads and displays data within 2 seconds of opening the dashboard.
- **SC-003**: 100% of mock/hardcoded financial values are removed from the Net Worth component.
- **SC-004**: Users with zero accounts see $0 values instead of hardcoded placeholder amounts.
