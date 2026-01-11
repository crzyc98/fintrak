# Feature Specification: Accounts & Categories Foundation

**Feature Branch**: `001-accounts-categories`
**Created**: 2026-01-07
**Status**: Draft
**Input**: User description: "Build the Accounts & Categories foundation for FinTrack (self-hosted personal finance app)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and Manage Financial Accounts (Priority: P1)

As a user, I want to create and manage my financial accounts so that I can track my assets and liabilities in one place.

**Why this priority**: Financial accounts are the foundation of any personal finance application. Without accounts, users cannot track balances, transactions, or net worth. This is the core data structure upon which all other features depend.

**Independent Test**: Can be fully tested by creating accounts of different types (checking, savings, credit card) and verifying they appear correctly in the sidebar grouped by type.

**Acceptance Scenarios**:

1. **Given** I am on the Accounts page, **When** I click "Create Account" and fill in name="My Checking", type="Checking", institution="Chase", **Then** the account is created and appears in the Checking group in the sidebar
2. **Given** I have an existing account, **When** I click edit and change the name, **Then** the account name is updated everywhere it appears
3. **Given** I have an existing account with no associated data, **When** I click delete and confirm, **Then** the account is removed from the system
4. **Given** I have multiple accounts of different types, **When** I view the sidebar, **Then** accounts are grouped by type (Checking, Savings, Credit, Investment, Loan, Real Estate, Crypto)

---

### User Story 2 - Create and Organize Spending Categories (Priority: P1)

As a user, I want to create a hierarchy of spending categories so that I can organize and categorize my transactions for budgeting purposes.

**Why this priority**: Categories are essential for transaction categorization and budgeting. Without categories, users cannot organize their spending or create meaningful budgets. This is equally foundational alongside accounts.

**Independent Test**: Can be fully tested by creating parent and child categories with different groups and verifying the hierarchy displays correctly in the tree view.

**Acceptance Scenarios**:

1. **Given** I am on the Categories page, **When** I create a category with name="Groceries", emoji="🛒", group="Essential", **Then** the category appears in the Essential group
2. **Given** I have a parent category "Food", **When** I create a child category "Restaurants" with parent_id set to "Food", **Then** "Restaurants" appears nested under "Food" in the tree view
3. **Given** I am editing a category, **When** I set a budget_amount of 500, **Then** the budget amount is saved and displayed with the category
4. **Given** I have a category, **When** I click delete and there are no associated transactions, **Then** the category is removed

---

### User Story 3 - View Account Balances in Sidebar (Priority: P2)

As a user, I want to see current balances next to my accounts in the sidebar so I can quickly understand my financial position at a glance.

**Why this priority**: While accounts can exist without visible balances, showing balances significantly improves usability. This depends on account snapshots existing (which may come from a later feature), so it gracefully degrades to showing no balance.

**Independent Test**: Can be tested by verifying the sidebar displays account names with balance (if snapshot exists) or blank/null indicator (if no snapshot).

**Acceptance Scenarios**:

1. **Given** an account has a balance snapshot, **When** I view the sidebar, **Then** I see the account name with its current balance displayed
2. **Given** an account has no balance snapshots, **When** I view the sidebar, **Then** I see the account name with a null/empty balance indicator (e.g., "--" or blank)
3. **Given** multiple accounts in the same group, **When** I view the sidebar, **Then** accounts within each group are listed with their respective balances

---

### User Story 4 - Data Persistence Across Sessions (Priority: P2)

As a user, I want my accounts and categories to persist across application restarts so that I don't lose my financial data.

**Why this priority**: Data persistence is critical for any finance application. Users must trust that their data is safe. This is marked P2 because it's an infrastructure concern that supports P1 features.

**Independent Test**: Can be tested by creating accounts/categories, restarting the application container, and verifying all data is preserved.

**Acceptance Scenarios**:

1. **Given** I have created accounts and categories, **When** I restart the Docker container, **Then** all my accounts and categories are still present
2. **Given** I have edited an account name, **When** I restart the application, **Then** the edited name persists

---

### Edge Cases

- What happens when a user tries to delete a category that has child categories? (System should prevent deletion or require deleting children first)
- What happens when a user tries to set a category's parent to itself? (System must reject circular references)
- What happens when a user tries to set a category's parent to one of its descendants? (System must detect and reject cycles in the hierarchy)
- What happens when a user enters a name exceeding 100 characters? (System rejects with validation error before save)
- What happens when a user tries to create duplicate account names? (System should allow - users may have multiple accounts at the same institution)
- What happens when a user tries to delete an account with associated transactions or snapshots? (System prevents deletion and displays error message listing why deletion is blocked)
- What happens when a user tries to create a category with an invalid emoji? (System should validate emoji or accept any text in emoji field)

## Requirements *(mandatory)*

### Functional Requirements

**Account Management**

- **FR-001**: System MUST allow users to create accounts with the following attributes: name (required, max 100 chars), type (required), institution (optional, max 200 chars), is_asset (required boolean)
- **FR-002**: System MUST support the following account types: Checking, Savings, Credit, Investment, Loan, Real Estate, Crypto
- **FR-003**: System MUST automatically set is_asset to true for Checking, Savings, Investment, Real Estate, and Crypto account types; false for Credit and Loan types
- **FR-004**: System MUST allow users to view a list of all accounts
- **FR-005**: System MUST allow users to edit existing account attributes
- **FR-006**: System MUST allow users to delete accounts only when no associated records (transactions, balance snapshots) exist; system MUST prevent deletion and display an error if associated records are present
- **FR-007**: System MUST display accounts grouped by account type in the sidebar, sorted alphabetically by name within each group
- **FR-008**: System MUST display the current balance for each account in the sidebar (derived from the most recent balance snapshot if one exists, otherwise display as null/empty)
- **FR-009**: System MUST automatically record the creation timestamp for each account

**Category Management**

- **FR-010**: System MUST allow users to create categories with the following attributes: name (required, max 100 chars), emoji (optional), parent_id (optional), group_name (required), budget_amount (optional, stored as cents/integer)
- **FR-011**: System MUST support the following category groups: Essential, Lifestyle, Income, Transfer, Other
- **FR-012**: System MUST allow categories to have a parent category (for hierarchical organization)
- **FR-013**: System MUST validate that no circular parent relationships exist when setting a category's parent
- **FR-014**: System MUST allow users to view all categories in a hierarchical tree structure
- **FR-015**: System MUST allow users to edit existing category attributes
- **FR-016**: System MUST allow users to delete categories (when no child categories exist)
- **FR-017**: System MUST prevent deletion of categories that have child categories

**Data Persistence**

- **FR-018**: System MUST persist all account and category data to durable storage
- **FR-019**: System MUST preserve data across application container restarts

**User Interface Behavior**

- **FR-020**: System MUST display validation errors inline next to each invalid field (not as toast or modal)

### Key Entities

- **Account**: Represents a financial account owned by the user. Contains name, type classification, optional institution name, asset/liability indicator, and creation timestamp. The current balance is derived from the most recent balance snapshot (separate entity).

- **Category**: Represents a classification for financial transactions. Contains name, visual emoji identifier, optional parent category reference (for hierarchy), group classification, and optional budget amount (stored as cents/integer, displayed according to user locale). Categories form a tree structure through parent-child relationships.

- **Balance Snapshot** (referenced, not implemented in this feature): A point-in-time record of an account's balance. Used to derive current balance displayed in the sidebar. If no snapshots exist for an account, balance displays as null.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can create a new account within 30 seconds (from clicking "Create" to seeing it in the sidebar)
- **SC-002**: Users can create a new category with a parent relationship within 30 seconds
- **SC-003**: 100% of account and category data persists correctly across container restarts
- **SC-004**: Circular category relationship detection catches 100% of invalid parent assignments (self-reference and descendant references)
- **SC-005**: All CRUD operations for accounts and categories are accessible via both the user interface and the programmatic interface
- **SC-006**: The sidebar accurately displays current balances for accounts that have snapshots and shows appropriate empty state for accounts without snapshots

## Clarifications

### Session 2026-01-07

- Q: What happens when deleting an account that has associated transactions or balance snapshots? → A: Prevent deletion if any associated records exist; user must remove them first
- Q: What are the maximum character limits for text fields? → A: 100 characters for names (account, category), 200 for institution
- Q: How should currency/monetary amounts be handled? → A: Single currency assumed; store as cents (integer); display based on user locale
- Q: How should validation errors be displayed to users? → A: Inline error messages displayed next to each invalid field
- Q: How should accounts be sorted within each type group in the sidebar? → A: Alphabetically by account name

## Assumptions

- Single-user system: No authentication or authorization is required for MVP
- Single currency assumed for MVP; all monetary amounts stored as cents (integers) to avoid floating-point precision issues
- Balance snapshots will be created by a future feature (e.g., manual entry or import); this feature only reads existing snapshots
- The system runs in a Docker environment with volume-mounted persistent storage
- Emoji field accepts any valid Unicode emoji character; validation is best-effort
- Account names do not need to be unique (user may have "Savings" at multiple institutions)
- Category names do not need to be globally unique but should be unique within the same parent
- Maximum hierarchy depth for categories is not explicitly limited but recommended to stay under 5 levels for usability
