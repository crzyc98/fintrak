# Tasks: AI Spending Insights

**Input**: Design documents from `/specs/009-ai-spending-insights/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create new files, register the router, and add shared Pydantic models

- [x] T001 [P] Create Pydantic request/response models for insights in backend/app/models/insights.py — include `InsightRequest` (period enum, type enum, optional date_from/date_to with custom-period validator), `CategorySpendingResponse`, `AnomalyResponse`, and `InsightResponse` (with insufficient_data fields). Reference contracts/insights-api.md for exact field names and types. All amounts are INTEGER cents.
- [x] T002 [P] Add TypeScript types and `generateInsights()` API function in frontend/src/services/api.ts — add `InsightRequest`, `CategorySpending`, `Anomaly`, `InsightResponse` interfaces and a `generateInsights(request: InsightRequest): Promise<InsightResponse>` function that POSTs to `/api/insights/generate`. Handle 429 (cooldown) and 503 (service unavailable) responses with appropriate error messages.
- [x] T003 Create insights router skeleton in backend/app/routers/insights.py — create a FastAPI router with prefix `/api/insights`. Add a single `POST /generate` endpoint that accepts `InsightRequest` body and returns `InsightResponse`. For now, return a placeholder response. Register this router in backend/app/main.py by importing and including it (follow the pattern used for the transactions router).

**Checkpoint**: Backend serves POST /api/insights/generate (placeholder), frontend can call it.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data aggregation service that all user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create InsightsService with data aggregation methods in backend/app/services/insights_service.py — implement a class with these methods using `get_db()` context manager for DuckDB access:
  - `get_category_spending(date_from, date_to)` → list of CategorySpendingSummary dicts. Query: join transactions + categories, filter `amount < 0` and `category_id IS NOT NULL`, GROUP BY category, ORDER BY total DESC, LIMIT 5. Use SQL from data-model.md.
  - `get_previous_period_spending(date_from, date_to)` → same structure for the equivalent prior period (e.g., if current is Feb, prior is Jan). Calculate `change_percentage` for each category.
  - `get_transaction_counts(date_from, date_to)` → dict with `categorized_count` and `uncategorized_count`.
  - `resolve_period(period, date_from, date_to)` → convert period enum ("current_month", "last_month", "custom") to concrete (date_from, date_to) tuple.
  - All amounts stay as integer cents. Expenses are negative in DB — use `ABS(amount)` in aggregation.

**Checkpoint**: InsightsService can query aggregated spending data from DuckDB.

---

## Phase 3: User Story 1 — On-Demand Spending Summary (Priority: P1) MVP

**Goal**: User sees a dashboard card that generates a plain-English spending summary with top categories and period-over-period comparisons on demand.

**Independent Test**: Load dashboard with 5+ categorized transactions → click "Generate Insights" → verify summary text with top categories and period comparison appears.

### Implementation for User Story 1

- [x] T005 [US1] Add Gemini prompt builder and summary generation to InsightsService in backend/app/services/insights_service.py — add a `generate_summary(period, date_from, date_to)` method that:
  1. Calls `resolve_period()` to get date range
  2. Calls `get_transaction_counts()` — if categorized < 5, return InsightResponse with `insufficient_data=True` and a friendly message (FR-006)
  3. Calls `get_category_spending()` for current period
  4. Calls `get_previous_period_spending()` for prior period comparison (skip if no prior data)
  5. Builds a Gemini prompt with pre-aggregated data (category totals in dollars, % changes) asking for JSON: `{ "summary": "...", "suggestions": ["..."] }`. Convert cents to dollars in the prompt for readability.
  6. Calls `invoke_gemini()` from gemini_client.py with retry logic (`with_retry`)
  7. Parses JSON response using `extract_json()`, validates that `summary` field exists
  8. If AI fails (AIClientError), raise HTTPException 503 with user-friendly message (FR-007)
  9. If AI returns malformed response, return a fallback summary built from the raw aggregated data (FR-008)
  10. Returns a complete `InsightResponse` with summary, top_categories, empty anomalies, suggestions, generated_at

- [x] T006 [US1] Wire up the insights router endpoint in backend/app/routers/insights.py — replace the placeholder from T003. Call `InsightsService.generate_summary()` for `type="summary"` requests. Wrap in try/except for `AIClientError` → 503, validation errors → 422. Add a module-level `_last_generation_time` variable and check 30-second cooldown (FR-011) — if within cooldown, return 429 with `retry_after_seconds`.

- [x] T007 [US1] Create SpendingInsights dashboard card component in frontend/components/SpendingInsights.tsx — build a React functional component matching the dark dashboard card style (bg-[#0a0f1d], border-white/10, rounded-3xl, same height as NetWorth). Include:
  - Initial state: show a "Generate Insights" button (centered, styled like other dashboard CTAs)
  - Loading state: show a loading spinner/message ("Analyzing your spending...")
  - Error state: show error message with "Retry" button (FR-007)
  - Insufficient data state: show the `insufficient_data_message` from response
  - Success state: display `summary` text in readable paragraphs, followed by top categories as a simple list (emoji + name + formatted dollar amount + change % badge if available), followed by `suggestions` as a bulleted list
  - "Regenerate" button at bottom with 30-second cooldown — use `useState` for countdown timer + `useEffect` with `setInterval` that decrements every second. Disable button and show seconds remaining during cooldown.
  - Call `generateInsights({ period: 'current_month', type: 'summary' })` on button click
  - Use `(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })` for currency formatting

- [x] T008 [US1] Add SpendingInsights card to dashboard grid in frontend/components/Dashboard.tsx — import SpendingInsights component and add it to the dashboard grid layout. Place it after the existing cards (e.g., after TransactionReview or in a new row). It should span the same width as other dashboard cards in the 2-column lg grid.

- [x] T009 [US1] Verify type checking passes by running `cd frontend && npx tsc --noEmit` and `cd backend && python -m py_compile app/routers/insights.py && python -m py_compile app/services/insights_service.py && python -m py_compile app/models/insights.py`

**Checkpoint**: Dashboard shows Insights card → click Generate → see AI-generated spending summary with top categories and suggestions. Insufficient data and error states work. 30-second cooldown enforced.

---

## Phase 4: User Story 2 — Anomaly Detection (Priority: P2)

**Goal**: Insights include an "Unusual Activity" section highlighting transactions that are 3x+ above their category average.

**Independent Test**: Insert a transaction 3x+ above its category average → generate insights → verify it appears in the anomaly section with explanation.

### Implementation for User Story 2

- [x] T010 [US2] Add anomaly detection queries to InsightsService in backend/app/services/insights_service.py — add two methods:
  - `get_category_averages(date_from_3mo, date_to)` → category averages over past 3 months. Use SQL from data-model.md (filter `amount < 0`, `category_id IS NOT NULL`, `HAVING COUNT(*) >= 3`).
  - `get_anomaly_candidates(period_start, period_end, category_averages)` → transactions in the current period that exceed 3x their category average. Use the CTE query from data-model.md. Return list of AnomalyCandidate dicts with transaction_id, date, description, merchant, amount_cents, category_name, category_avg_cents, deviation_factor. LIMIT 10.

- [x] T011 [US2] Extend `generate_summary()` in backend/app/services/insights_service.py to include anomaly data — after computing category spending, also call `get_category_averages()` (3 months back from period_start) and `get_anomaly_candidates()`. If anomalies found, add them to the Gemini prompt asking for `anomaly_explanations` field in the JSON response — a plain-English explanation of each anomaly (e.g., "You had an unusually large purchase of $450 at Best Buy — your average Shopping transaction is $120"). Populate `anomalies` and `anomaly_explanations` fields in the InsightResponse. If no anomalies, set both to empty/null.

- [x] T012 [US2] Add anomaly display section to SpendingInsights component in frontend/components/SpendingInsights.tsx — after the summary and top categories, conditionally render an "Unusual Activity" section if `anomalies.length > 0`. For each anomaly, show: description, formatted amount (`$X.XX`), category name, and deviation factor (e.g., "3.5x your average"). Display the `anomaly_explanations` text above the list. If no anomalies, either hide the section entirely or show "No unusual activity detected." Use orange/amber accent color (matching the existing debt color scheme) for the anomaly section header dot.

**Checkpoint**: Insights now include anomaly detection. Transactions 3x+ above category average appear with AI-generated explanations.

---

## Phase 5: User Story 3 — Monthly Financial Health Report (Priority: P3)

**Goal**: Users can generate a comprehensive monthly report with income/expense breakdown, category details, trends, and actionable suggestions.

**Independent Test**: Request a report for a month with 10+ transactions across 3+ categories → verify it includes total spending, category breakdown, and at least one actionable observation.

### Implementation for User Story 3

- [x] T013 [US3] Add report-specific data aggregation to InsightsService in backend/app/services/insights_service.py — add a `get_income_totals(date_from, date_to)` method that queries total positive transactions (income) for the period. Add a `generate_report(period, date_from, date_to)` method that:
  1. Calls all existing aggregation methods (category spending, previous period, anomalies)
  2. Additionally calls `get_income_totals()` for income data
  3. Builds a richer Gemini prompt that includes income vs expenses, savings rate, all category breakdowns (not just top 5), and asks for: `{ "summary": "...", "category_analysis": "...", "trends": "...", "suggestions": ["..."] }` — requesting actionable recommendations
  4. If fewer than 5 transactions, return insufficient data response with partial summary
  5. Returns InsightResponse with all fields populated

- [x] T014 [US3] Wire report type into the insights router in backend/app/routers/insights.py — in the POST /generate endpoint, check `request.type`: if "summary" call `generate_summary()`, if "report" call `generate_report()`. Both return the same InsightResponse shape.

- [x] T015 [US3] Add report mode toggle to SpendingInsights component in frontend/components/SpendingInsights.tsx — add a toggle or segmented control at the top of the card to switch between "Summary" and "Full Report" modes. When "Full Report" is selected, call `generateInsights({ period: 'current_month', type: 'report' })` instead. The report view should display the same sections as summary but with richer content (the AI will return more detailed text). Style the toggle using the existing dark theme button pattern (similar to the timeframe selector style used elsewhere in the app).

**Checkpoint**: Users can toggle between quick summary and full monthly report. Reports include income/expense data and actionable suggestions.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Edge cases, validation, and cleanup

- [x] T016 [P] Handle edge case: all uncategorized transactions — in InsightsService, if `uncategorized_count > 0` and `categorized_count == 0`, return a specific message suggesting the user categorize transactions first (FR-009). If uncategorized > 20% of total, add a note to suggestions array.
- [x] T017 [P] Handle edge case: single category — in the Gemini prompt builder, detect when only 1 category exists and adjust the prompt to skip cross-category comparisons. Ensure the AI doesn't claim "your top category is X" when there's only one.
- [x] T018 [P] Handle edge case: refunds and credits — ensure positive-amount transactions within expense categories (refunds) are not counted as spending. In aggregation queries, strictly filter `amount < 0` for expenses.
- [x] T019 [P] Handle edge case: no prior period data — when `get_previous_period_spending()` returns empty results (first month of use), omit comparison language from the prompt and set `change_percentage` to null in the response.
- [x] T020 Run full validation — execute `cd backend && pytest` for all backend tests, `cd frontend && npx tsc --noEmit` for type checking. Manually test the quickstart.md scenarios: generate summary, test cooldown, test insufficient data, test error state (with invalid/missing GEMINI_API_KEY).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001, T002 can run in parallel; T003 depends on T001
- **Foundational (Phase 2)**: Depends on T001 (models) — T004 builds on Pydantic models
- **User Story 1 (Phase 3)**: Depends on Phase 2 (T004) — needs aggregation service
- **User Story 2 (Phase 4)**: Depends on Phase 3 (T005-T006) — extends existing service and component
- **User Story 3 (Phase 5)**: Depends on Phase 3 (T005-T006) — extends existing service and component
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **User Story 2 (P2)**: Depends on US1 (extends the same service and component)
- **User Story 3 (P3)**: Depends on US1 (extends the same service and component); can run in parallel with US2

### Within Each User Story

- Backend service logic before router wiring
- Backend complete before frontend integration
- Component creation before dashboard integration

### Parallel Opportunities

- **Phase 1**: T001 and T002 can run in parallel (backend models + frontend types are independent files)
- **Phase 3**: T007 (frontend component) can start as soon as T002 (frontend types) is done, in parallel with T005-T006 (backend)
- **Phase 4+5**: US2 and US3 backend work (T010-T011 and T013-T014) can run in parallel since they extend different methods
- **Phase 6**: All edge case tasks (T016-T019) can run in parallel

---

## Parallel Example: Phase 1

```bash
# These can run in parallel (different files):
Task: T001 "Create Pydantic models in backend/app/models/insights.py"
Task: T002 "Add TypeScript types in frontend/src/services/api.ts"

# Then sequentially:
Task: T003 "Create router skeleton in backend/app/routers/insights.py" (needs T001)
```

## Parallel Example: User Story 1

```bash
# After T004 (foundational) completes, backend and frontend can overlap:

# Backend (sequential):
Task: T005 "Add Gemini prompt builder to InsightsService"
Task: T006 "Wire up router endpoint"

# Frontend (can start in parallel with backend once T002 types exist):
Task: T007 "Create SpendingInsights component"
Task: T008 "Add component to Dashboard grid" (needs T007)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004)
3. Complete Phase 3: User Story 1 (T005-T009)
4. **STOP and VALIDATE**: Generate a spending summary via the dashboard
5. Deploy/demo if ready — this alone delivers the core value

### Incremental Delivery

1. Setup + Foundational → API endpoint reachable
2. Add User Story 1 → Spending summaries work → **MVP!**
3. Add User Story 2 → Anomaly detection integrated → Enhanced insights
4. Add User Story 3 → Full monthly reports available → Complete feature
5. Polish → Edge cases handled, validation passing → Production ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No new database tables — all data from existing transactions/categories/accounts
- Gemini prompt should use pre-aggregated data (dollars, not raw transactions) per research.md R1
- Anomaly detection happens in Python code, not AI — AI only explains anomalies per research.md R6
- All currency: integer cents in backend, divide by 100 for display and prompts
- Cooldown is enforced both server-side (429) and client-side (disabled button + countdown)
