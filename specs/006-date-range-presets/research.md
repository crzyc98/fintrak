# Research: Date Range Presets

## Overview

This feature adds date range preset buttons to the transaction filter panel. Research focused on date calculation patterns and UI integration with the existing filter system.

## Findings

### 1. Existing Filter Infrastructure

**Decision**: Leverage existing `date_from` and `date_to` filter fields.

**Rationale**: The `TransactionFiltersData` interface in `frontend/src/services/api.ts` already supports:
```typescript
export interface TransactionFiltersData {
  date_from?: string;  // YYYY-MM-DD format
  date_to?: string;    // YYYY-MM-DD format
  // ... other filters
}
```

The backend already handles these filters. No API changes needed.

**Alternatives considered**:
- Creating a new "preset" filter type → Rejected: unnecessary complexity, date range is already supported
- Backend-computed presets → Rejected: date calculation is simple and belongs client-side

### 2. Date Calculation Approach

**Decision**: Use JavaScript Date API with utility functions for each preset.

**Rationale**:
- No external dependencies needed
- Standard date calculations are simple and well-understood
- Format as ISO date strings (YYYY-MM-DD) to match existing filter format

**Preset calculations**:

| Preset | date_from | date_to |
|--------|-----------|---------|
| This Month | First day of current month | Today |
| Last Month | First day of previous month | Last day of previous month |
| Last 30 Days | Today - 30 days | Today |
| YTD | January 1 of current year | Today |

**Alternatives considered**:
- date-fns library → Rejected: overkill for 4 simple calculations
- moment.js → Rejected: deprecated, heavy dependency

### 3. Active Preset State Management

**Decision**: Track active preset in component state, detect when dates manually changed.

**Rationale**:
- User needs visual feedback of which preset is active
- Manual date edits should clear the preset indicator
- Compare filter dates against computed preset dates to detect manual changes

**Implementation approach**:
```typescript
const [activePreset, setActivePreset] = useState<string | null>(null);

// When preset clicked: set both activePreset and filter dates
// When date manually changed: clear activePreset
```

**Alternatives considered**:
- Derive active preset from current dates → Rejected: ambiguous when dates happen to match multiple presets
- Store preset ID in filters object → Rejected: unnecessary API coupling

### 4. UI Placement

**Decision**: Horizontal row of pill-style buttons above the From/To date inputs.

**Rationale**:
- Follows existing design system (rounded buttons, blue highlight for active state)
- Placed above date inputs creates logical flow: quick-select first, then refine if needed
- Matches clarification decision from spec

**Visual pattern**:
```
[This Month] [Last Month] [Last 30 Days] [YTD]
From: [____]  To: [____]
```

## No Outstanding Unknowns

All technical decisions resolved. Ready to proceed to Phase 1 design.
