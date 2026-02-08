# Quickstart: Date Range Presets

## Prerequisites

- Node.js 18+
- Project running locally (`./fintrak` or `cd frontend && npm run dev`)

## Implementation Overview

This feature modifies **one file**: `frontend/components/TransactionsView.tsx`

### Changes Summary

1. Add `activePreset` state variable
2. Add preset button row in filter panel (above date inputs)
3. Add date calculation helper functions
4. Wire up preset click handlers
5. Clear preset when dates manually edited

## Quick Implementation Guide

### Step 1: Add Preset Definitions

```typescript
// At top of TransactionsView.tsx, after imports

type DateRange = { date_from: string; date_to: string };

interface DatePreset {
  id: string;
  label: string;
  getRange: () => DateRange;
}

const formatDate = (date: Date): string => {
  return date.toISOString().split('T')[0];
};

const DATE_PRESETS: DatePreset[] = [
  {
    id: 'this_month',
    label: 'This Month',
    getRange: () => {
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
      return { date_from: formatDate(firstDay), date_to: formatDate(now) };
    },
  },
  {
    id: 'last_month',
    label: 'Last Month',
    getRange: () => {
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      const lastDay = new Date(now.getFullYear(), now.getMonth(), 0);
      return { date_from: formatDate(firstDay), date_to: formatDate(lastDay) };
    },
  },
  {
    id: 'last_30_days',
    label: 'Last 30 Days',
    getRange: () => {
      const now = new Date();
      const thirtyDaysAgo = new Date(now);
      thirtyDaysAgo.setDate(now.getDate() - 30);
      return { date_from: formatDate(thirtyDaysAgo), date_to: formatDate(now) };
    },
  },
  {
    id: 'ytd',
    label: 'YTD',
    getRange: () => {
      const now = new Date();
      const firstDay = new Date(now.getFullYear(), 0, 1);
      return { date_from: formatDate(firstDay), date_to: formatDate(now) };
    },
  },
];
```

### Step 2: Add State

```typescript
// Add to existing state declarations
const [activePreset, setActivePreset] = useState<string | null>(null);
```

### Step 3: Add Preset Handler

```typescript
const handlePresetClick = (preset: DatePreset) => {
  const { date_from, date_to } = preset.getRange();
  setFilters((prev) => ({ ...prev, date_from, date_to }));
  setActivePreset(preset.id);
  setCurrentPage(1);
};
```

### Step 4: Clear Preset on Manual Date Change

```typescript
// Modify handleFilterChange to clear preset when dates change
const handleFilterChange = (key: keyof TransactionFiltersData, value: string | boolean | undefined) => {
  // Clear active preset if user manually changes dates
  if (key === 'date_from' || key === 'date_to') {
    setActivePreset(null);
  }
  // ... rest of existing logic
};
```

### Step 5: Add Preset Buttons to UI

Add this above the "From" date input in the filter panel:

```tsx
{/* Date Presets */}
<div className="col-span-full">
  <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
    Quick Select
  </label>
  <div className="flex flex-wrap gap-2">
    {DATE_PRESETS.map((preset) => (
      <button
        key={preset.id}
        onClick={() => handlePresetClick(preset)}
        className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-colors ${
          activePreset === preset.id
            ? 'bg-blue-500 text-white'
            : 'bg-[#0a0f1d] border border-white/10 text-gray-400 hover:text-white hover:border-white/20'
        }`}
      >
        {preset.label}
      </button>
    ))}
  </div>
</div>
```

## Testing

1. Open the app: `./fintrak`
2. Go to Transactions page
3. Open filter panel (funnel icon)
4. Click each preset and verify:
   - Transactions filter to correct date range
   - Button shows active (blue) state
   - From/To date inputs update with computed dates
5. Manually edit a date field and verify preset indicator clears
6. Click "Clear Filters" and verify preset clears

## Files Modified

| File | Changes |
|------|---------|
| `frontend/components/TransactionsView.tsx` | Add presets, state, handlers, UI |
