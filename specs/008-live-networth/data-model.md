# Data Model: Live Net Worth Dashboard

**Feature**: 008-live-networth | **Date**: 2026-02-09

## Overview

This feature introduces **no new entities or schema changes**. It consumes existing data through the established API. This document maps the existing data model relevant to the feature.

---

## Existing Entities (No Changes)

### Account

**Source**: `backend/app/models/account.py` → `AccountResponse`
**Table**: `accounts` (DuckDB)

| Field | Type | Description |
|-------|------|-------------|
| id | VARCHAR(36) | UUID primary key |
| name | VARCHAR(100) | Account display name |
| type | AccountType enum | Checking, Savings, Credit, Investment, Loan, Real Estate, Crypto |
| institution | VARCHAR(200), nullable | Financial institution name |
| is_asset | BOOLEAN | `true` for asset types (Checking, Savings, Investment, Real Estate, Crypto), `false` for liability types (Credit, Loan) |
| current_balance | INTEGER, nullable | Balance in cents, computed from latest snapshot + subsequent transactions. `null` if no balance snapshots exist. |
| csv_column_mapping | JSON, nullable | Column mapping for CSV import |
| created_at | TIMESTAMP | Auto-generated creation time |

**Classification Rules** (from `ASSET_ACCOUNT_TYPES`):
- **Assets**: Checking, Savings, Investment, Real Estate, Crypto → `is_asset = true`
- **Liabilities**: Credit, Loan → `is_asset = false`

### Balance Computation (existing logic in `account_service.py`)

```
current_balance = latest_snapshot_balance + SUM(transactions.amount WHERE date > snapshot_date)
```

If no balance snapshot exists → `current_balance = null`

---

## Derived View: Net Worth Summary (Frontend Only)

This is a computed view, not a stored entity. It exists only in the React component's `useMemo`.

| Field | Type | Computation |
|-------|------|-------------|
| assets | number (cents) | `SUM(current_balance) WHERE is_asset = true`, null coalesced to 0 |
| debts | number (cents) | `SUM(current_balance) WHERE is_asset = false`, null coalesced to 0 |
| netWorth | number (cents) | `assets - debts` |

**Edge Cases**:
- No accounts → `{ assets: 0, debts: 0, netWorth: 0 }`
- All balances null → `{ assets: 0, debts: 0, netWorth: 0 }` (null coalesces to 0)
- Only asset accounts → `debts = 0`
- Only liability accounts → `assets = 0`
- Negative liability balance (overpayment) → reduces total debts (no `Math.abs`)

---

## Data Flow

```
DuckDB (accounts + balance_snapshots + transactions)
  ↓ backend computes current_balance per account
GET /api/accounts → AccountResponse[]
  ↓ frontend fetchAccounts()
AccountData[] (TypeScript)
  ↓ useMemo filter + reduce
{ assets, debts, netWorth } → rendered in NetWorth component
```

---

## TypeScript Types (Existing, No Changes)

### AccountData (frontend/src/services/api.ts)

```typescript
interface AccountData {
  id: string;
  name: string;
  type: string;
  institution: string | null;
  is_asset: boolean;
  current_balance: number | null;  // cents
  csv_column_mapping: CsvColumnMapping | null;
  created_at: string;
}
```

### AccountType (frontend/types.ts)

```typescript
type AccountType = 'Checking' | 'Savings' | 'Credit' | 'Investment' | 'Loan' | 'Real Estate' | 'Crypto';
```
