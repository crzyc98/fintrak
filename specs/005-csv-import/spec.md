# Feature Specification: CSV Import

**Feature Branch**: `005-csv-import`
**Created**: 2026-01-12
**Status**: Draft
**Input**: User description: "Per-account CSV column mapping: configure once, then drag & drop to import. Drop zone in account detail panel, visual column mapper for first-time setup, preview before import."

## Clarifications

### Session 2026-01-12

- Q: How should the system handle potential duplicate transactions during import? → A: Show warning for potential duplicates in preview, let user decide.
- Q: How should the column mapper handle amount representation in CSVs? → A: Support both single Amount column (negative=debit) OR separate Debit/Credit columns.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Time CSV Import with Column Mapping (Priority: P1)

A user wants to import transactions from their bank's CSV export into a specific account. Since this is the first time importing for this account, they need to configure how the CSV columns map to transaction fields.

**Why this priority**: This is the core value proposition - enabling users to import external transaction data. Without this, no CSV import functionality exists.

**Independent Test**: Can be fully tested by dropping a CSV file on an account and mapping columns. Delivers immediate value by allowing transaction data entry without manual typing.

**Acceptance Scenarios**:

1. **Given** a user has selected an account with no saved column mapping, **When** they drop a CSV file on the drop zone, **Then** the system displays a visual column mapper showing CSV headers and sample data rows.

2. **Given** the column mapper is displayed, **When** the user selects which columns contain Date, Description, and Amount, **Then** the system validates the selections and enables the "Preview" button.

3. **Given** the user has configured column mappings, **When** they click "Preview", **Then** the system displays parsed transactions with a count of valid rows and any error rows.

4. **Given** the user is viewing the import preview, **When** they confirm the import, **Then** all valid transactions are created with `reviewed=false` status and the column mapping is saved to the account.

---

### User Story 2 - Repeat CSV Import with Saved Mapping (Priority: P2)

A user wants to import a new CSV file for an account that already has a saved column mapping configuration.

**Why this priority**: This provides the "configure once" convenience that makes the feature efficient for regular use. Builds on P1 functionality.

**Independent Test**: Can be tested by importing a second CSV file to an account with existing mapping. Delivers value by skipping the configuration step for repeat imports.

**Acceptance Scenarios**:

1. **Given** a user has selected an account with a saved column mapping, **When** they drop a CSV file on the drop zone, **Then** the system automatically parses the file using the saved mapping and displays the import preview (skipping the mapper).

2. **Given** the import preview is displayed from auto-parsing, **When** the user confirms the import, **Then** transactions are created using the saved mapping configuration.

---

### User Story 3 - Re-configure Column Mapping (Priority: P3)

A user needs to update the column mapping for an account because their bank changed the CSV export format.

**Why this priority**: Edge case handling that improves long-term usability. Less common than regular imports but necessary for maintenance.

**Independent Test**: Can be tested by accessing mapping configuration for an account with existing mapping. Delivers value by allowing recovery from format changes.

**Acceptance Scenarios**:

1. **Given** an account has a saved column mapping, **When** the user accesses the "Re-configure mapping" option, **Then** the column mapper displays pre-filled with the current saved configuration.

2. **Given** the user has modified the column mapping, **When** they save the changes, **Then** the new mapping replaces the old one and future imports use the updated configuration.

---

### User Story 4 - Date Format Configuration (Priority: P3)

A user's bank CSV uses a non-standard date format that needs explicit configuration.

**Why this priority**: Important for international users and banks with varied date formats, but many users will have standard formats auto-detected.

**Independent Test**: Can be tested by importing a CSV with a specific date format (e.g., DD/MM/YYYY vs MM/DD/YYYY). Delivers value by supporting diverse data sources.

**Acceptance Scenarios**:

1. **Given** the column mapper is displayed, **When** the user selects the date column, **Then** the system shows a date format selector with common options (YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY, etc.).

2. **Given** the user has selected a date format, **When** they preview the import, **Then** dates are parsed correctly according to the selected format.

---

### Edge Cases

- What happens when a user drops an empty CSV file? System displays a clear error message indicating the file contains no data.
- What happens when the CSV has encoding issues (non-UTF-8)? System attempts to detect encoding and displays an error with guidance if parsing fails.
- What happens when the selected date column contains unparseable dates? System marks those rows as errors in the preview and allows the user to proceed with valid rows only.
- What happens when the amount column contains non-numeric values? System marks those rows as errors and displays them separately in the preview.
- What happens when a CSV file format is incompatible (e.g., not comma-separated)? System detects common delimiters (comma, semicolon, tab) and handles accordingly.
- What happens when imported transactions appear to be duplicates of existing transactions? System highlights potential duplicates in the preview (matching date, description, and amount) and lets user decide whether to include or exclude them before confirming import.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display a drag-and-drop zone in the account detail panel when an account is selected.
- **FR-002**: System MUST accept CSV files dropped on the drop zone.
- **FR-003**: System MUST provide visual feedback during drag operations (hover state, valid/invalid drop indication).
- **FR-004**: System MUST display a column mapper interface for first-time imports (accounts without saved mapping).
- **FR-005**: System MUST show CSV headers and sample data rows (first 3-5 rows) in the column mapper.
- **FR-006**: System MUST allow users to map CSV columns to Date, Description, and Amount fields. Amount mapping supports two modes: (a) single Amount column where negative values represent debits, or (b) separate Debit and Credit columns.
- **FR-007**: System MUST provide a date format selector with common format options.
- **FR-008**: System MUST auto-detect common column names (e.g., "Date", "Transaction Date", "Amount", "Description") and pre-select likely matches.
- **FR-009**: System MUST save the column mapping configuration to the account for future use.
- **FR-010**: System MUST automatically use saved mapping for repeat imports (skip mapper).
- **FR-011**: System MUST display an import preview showing parsed transactions before creation.
- **FR-012**: System MUST display statistics in the preview: count of valid rows, count of error rows.
- **FR-013**: System MUST create transactions with `reviewed=false` status upon import confirmation.
- **FR-014**: System MUST provide a "Re-configure mapping" option for accounts with existing mappings.
- **FR-015**: System MUST display clear error messages for empty files, encoding issues, or unparseable data.
- **FR-016**: System MUST detect potential duplicate transactions (matching date, description, and amount with existing account transactions) and highlight them in the import preview for user decision.

### Key Entities

- **Account**: An existing entity that will gain a new attribute for storing CSV column mapping configuration. Stores the user's preferred mapping of CSV columns to transaction fields.
- **CSV Column Mapping**: Configuration that defines which CSV columns map to Date, Description, and Amount fields (supporting either single Amount column or separate Debit/Credit columns), plus the date format to use when parsing.
- **Parsed Transaction**: A temporary representation of a transaction parsed from CSV, containing date, description, amount, and any parsing errors before being converted to a persisted transaction.
- **Transaction**: An existing entity representing a financial transaction. CSV imports create new transactions associated with the selected account.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can complete a first-time CSV import (including column mapping) in under 3 minutes.
- **SC-002**: Users can complete a repeat CSV import (with saved mapping) in under 30 seconds.
- **SC-003**: System correctly parses 95% of standard bank CSV formats without manual date format selection.
- **SC-004**: Import preview displays within 2 seconds for CSV files up to 1,000 rows.
- **SC-005**: 90% of users successfully complete their first CSV import on the first attempt.
- **SC-006**: System handles CSV files with up to 10,000 transactions.

## Assumptions

- Users will have CSV files exported from their banks or financial institutions.
- CSV files will contain at minimum: date, description, and amount columns.
- Most bank CSVs use UTF-8 encoding or common Western encodings.
- Users import transactions into one account at a time (no multi-account imports).
- The account detail panel already exists and has space for a drop zone component.
