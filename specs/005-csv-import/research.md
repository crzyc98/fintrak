# Research: CSV Import

**Feature**: 005-csv-import | **Date**: 2026-01-12

## Research Summary

No major technical unknowns. The existing tech stack (Python/FastAPI backend, React/TypeScript frontend, DuckDB storage) fully supports the CSV import feature. This document captures design decisions and best practices.

---

## 1. CSV File Handling Approach

**Decision**: Client-side file reading with base64 encoding for API transport

**Rationale**:
- Browser FileReader API provides efficient client-side CSV reading
- Base64 encoding allows JSON-based API transport without multipart forms
- Python's built-in `csv` module handles parsing; `base64` module handles decoding
- Keeps API contract simple and consistent with existing endpoints

**Alternatives Considered**:
- **Multipart form upload**: More complex API contract, requires python-multipart (already in deps)
- **Streaming upload**: Overkill for files under 1MB; adds complexity
- **Client-side parsing only**: Would prevent server-side duplicate detection

---

## 2. Column Mapping Storage

**Decision**: Store mapping as JSON in `csv_column_mapping` column on accounts table

**Rationale**:
- DuckDB supports JSON type natively
- Single column keeps schema simple
- JSON structure allows flexible mapping (single Amount vs Debit/Credit modes)
- Easy to extend if future fields needed

**Schema**:
```json
{
  "date_column": "Transaction Date",
  "description_column": "Description",
  "amount_mode": "single",  // or "split"
  "amount_column": "Amount",  // used when mode=single
  "debit_column": null,  // used when mode=split
  "credit_column": null,  // used when mode=split
  "date_format": "YYYY-MM-DD"
}
```

**Alternatives Considered**:
- **Separate mapping table**: Unnecessary complexity for 1:1 account relationship
- **User-level default mapping**: Spec requires per-account mapping

---

## 3. Duplicate Detection Strategy

**Decision**: Match on (date, description, amount) tuple against existing account transactions

**Rationale**:
- Simple, deterministic matching
- Covers most real duplicate scenarios (re-importing same file)
- User sees duplicates in preview and decides (per clarification)

**Implementation**:
- Query existing transactions for the account
- Build set of (date, description, amount) tuples
- Flag parsed rows that match existing tuples

**Alternatives Considered**:
- **Fuzzy matching**: Adds complexity, false positives risk
- **Hash-based deduplication**: Same result as tuple matching, less transparent

---

## 4. Date Format Parsing

**Decision**: Support common formats with user-selectable dropdown

**Supported Formats**:
- `YYYY-MM-DD` (ISO 8601)
- `MM/DD/YYYY` (US)
- `DD/MM/YYYY` (EU)
- `MM-DD-YYYY`
- `DD-MM-YYYY`
- `M/D/YYYY` (no leading zeros)
- `D/M/YYYY` (no leading zeros)

**Rationale**:
- Python `datetime.strptime` handles all formats
- Auto-detection via heuristics for common patterns
- User override available if auto-detection fails

**Alternatives Considered**:
- **dateutil.parser**: More flexible but can misinterpret ambiguous dates (01/02/2024)
- **Strict single format**: Too limiting for international users

---

## 5. Amount Parsing

**Decision**: Support single Amount column OR separate Debit/Credit columns

**Single Amount Mode**:
- Parse as float, multiply by 100 for cents storage
- Negative values = debits, positive = credits

**Split Mode**:
- Debit column values stored as negative
- Credit column values stored as positive
- Empty cells treated as zero

**Rationale**:
- Covers ~95% of bank CSV formats
- Matches clarification decision from spec

**Alternatives Considered**:
- **Transaction type column**: Less common in practice, adds complexity

---

## 6. Error Handling Strategy

**Decision**: Categorize rows as valid, warning (duplicates), or error (parse failures)

**Row Categories**:
- **Valid**: All fields parsed successfully, not a duplicate
- **Warning**: Parsed successfully but flagged as potential duplicate
- **Error**: Parse failure (invalid date, non-numeric amount)

**Preview Display**:
- Show counts: X valid, Y warnings, Z errors
- Expandable sections for warnings and errors
- User can proceed with valid + selected warnings

**Alternatives Considered**:
- **Fail entire import on any error**: Too strict for real-world CSVs
- **Silent skip of errors**: User might not notice data loss

---

## 7. Frontend Component Architecture

**Decision**: Three modal components coordinated by AccountsView

**Components**:
1. `CsvDropZone`: Inline drop zone in account panel, triggers file selection
2. `CsvColumnMapper`: Modal for first-time mapping configuration
3. `CsvImportPreview`: Modal showing parsed transactions, confirm/cancel

**State Flow**:
```
AccountsView (parent state)
  → CsvDropZone (file selection)
  → [if no mapping] CsvColumnMapper (configure mapping)
  → CsvImportPreview (review & confirm)
  → API call → refresh transactions
```

**Rationale**:
- Keeps each component focused on single responsibility
- AccountsView orchestrates flow, manages loading/error states
- Modal pattern matches existing app UX

**Alternatives Considered**:
- **Single multi-step wizard component**: Harder to test, more complex state
- **Separate import page**: Breaks "import to selected account" flow

---

## 8. API Design

**Decision**: Three endpoints matching the UI flow

**Endpoints**:
1. `POST /api/import/preview` - Returns headers + sample rows for mapping UI
2. `POST /api/import/parse` - Parses CSV with mapping, returns transactions + duplicates
3. `POST /api/import/transactions` - Creates transactions from confirmed import

**Rationale**:
- Separates concerns: preview (no parsing), parse (validate), create (commit)
- Allows user to cancel at any step without side effects
- Matches spec's import flow

**Alternatives Considered**:
- **Single endpoint with modes**: Less clear API contract
- **WebSocket for streaming**: Overkill for file sizes under 1MB

---

## 9. Performance Considerations

**Decision**: Process files up to 10,000 rows; batch insert transactions

**Approach**:
- Limit preview to first 5 rows (quick UI)
- Full parse on demand
- Batch INSERT for transaction creation (single query)
- Target: <2s for 1,000 rows per SC-004

**Rationale**:
- DuckDB handles batch inserts efficiently
- Python CSV parsing is fast for this scale
- Client-side FileReader is async, won't block UI

**Alternatives Considered**:
- **Background job for large files**: Not needed at this scale
- **Pagination**: Adds complexity, not needed for preview UX

---

## Dependencies

**No new dependencies required**. Existing stack covers all needs:
- Python: `csv`, `base64`, `datetime` (stdlib)
- FastAPI: Request handling, Pydantic validation
- React: FileReader API, existing modal patterns
- DuckDB: JSON column type, batch inserts
