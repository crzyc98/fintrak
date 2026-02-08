# Data Model: Date Range Presets

## Overview

This feature is **frontend-only** and requires no database or API changes. The existing transaction filtering system already supports `date_from` and `date_to` parameters.

## Entities

### DatePreset (Frontend TypeScript)

A configuration object defining a named date range preset.

```typescript
interface DatePreset {
  id: string;           // Unique identifier: 'this_month', 'last_month', 'last_30_days', 'ytd'
  label: string;        // Display text: 'This Month', 'Last Month', 'Last 30 Days', 'YTD'
  getRange: () => {     // Function to compute dates based on current date
    date_from: string;  // ISO date string (YYYY-MM-DD)
    date_to: string;    // ISO date string (YYYY-MM-DD)
  };
}
```

### Preset Definitions

| ID | Label | date_from Calculation | date_to Calculation |
|----|-------|----------------------|---------------------|
| `this_month` | This Month | First day of current month | Today |
| `last_month` | Last Month | First day of previous month | Last day of previous month |
| `last_30_days` | Last 30 Days | Today minus 30 days | Today |
| `ytd` | YTD | January 1 of current year | Today |

## State Management

### New Component State

```typescript
// In TransactionsView.tsx
const [activePreset, setActivePreset] = useState<string | null>(null);
```

### State Transitions

1. **Preset Selected**:
   - Compute dates using preset's `getRange()` function
   - Set `filters.date_from` and `filters.date_to`
   - Set `activePreset` to preset ID

2. **Date Manually Changed**:
   - Clear `activePreset` (set to `null`)
   - Keep date values as user entered

3. **Filters Cleared**:
   - Clear `activePreset` (set to `null`)
   - Clear date values (existing behavior)

## No Database Changes

The existing `transactions` table and API already support date filtering via query parameters:
- `GET /api/transactions?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD`

No schema modifications required.
