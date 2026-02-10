# Research: AI Spending Insights

**Feature Branch**: `009-ai-spending-insights`
**Date**: 2026-02-10

## R1: Gemini Prompt Strategy for Spending Insights

**Decision**: Use plain-text prompts with structured JSON context (not raw transaction rows). Pre-aggregate spending data in Python before sending to Gemini — category totals, period comparisons, anomaly candidates — and ask the AI to synthesize natural-language summaries from the aggregated data.

**Rationale**: Sending raw transactions to the AI is wasteful (token cost, latency) and risks exposing sensitive data. Pre-aggregation reduces prompt size dramatically (tens of category totals vs. hundreds of transactions), keeps response times under the 15-second target, and lets the backend validate the AI's claims against known data.

**Alternatives considered**:
- Send raw transactions to AI: Higher cost, slower, potential data exposure, harder to validate output
- Use Gemini's function-calling to query DB: Over-engineered for v1, adds complexity, not needed when data is already available in Python

## R2: AI Response Format and Validation

**Decision**: Request JSON-structured responses from Gemini (using the existing `response_mime_type="application/json"` mode) with a defined schema: `{ summary: string, categories: [{name, amount, change_pct}], anomalies: [{description, amount, category, reason}], suggestions: [string] }`. Validate required fields exist and that referenced categories/amounts match the input data before displaying.

**Rationale**: JSON mode is already configured in the existing `invoke_gemini` function. Structured output enables programmatic validation (e.g., verify top categories match input data) and allows the frontend to render sections independently (summary card, anomaly list, suggestions). The existing `extract_json` helper handles edge cases.

**Alternatives considered**:
- Freeform text response: Harder to validate, can't render structured UI sections, inconsistent formatting
- Markdown response: Better than freeform but still hard to programmatically validate data accuracy

## R3: Data Aggregation Approach

**Decision**: Create a new `InsightsService` in the backend that queries DuckDB directly for aggregated spending data. Queries needed:
1. Category spending totals for current and previous period
2. Per-category averages over past 3 months (for anomaly detection)
3. Individual transactions exceeding 3x category average (anomaly candidates)
4. Total categorized vs. uncategorized transaction counts

**Rationale**: DuckDB is excellent at analytical queries (aggregations, window functions). Doing aggregation in SQL is more efficient than fetching all transactions and processing in Python. The existing `get_db()` context manager provides database access.

**Alternatives considered**:
- Reuse existing transaction_service queries: They're optimized for pagination/filtering, not aggregation; would require multiple round-trips
- Add aggregation to spending_service: Could work but that service is focused on the monthly spending chart; better to keep insights logic separate

## R4: Frontend Component Architecture

**Decision**: Create a single `SpendingInsights.tsx` dashboard card component that:
- Renders in the Dashboard grid alongside NetWorth
- Has a "Generate Insights" button (not auto-generated on page load to avoid unnecessary API calls)
- Shows loading state during AI generation
- Displays structured sections: summary, anomalies (if any), suggestions
- Implements 30-second cooldown on the regenerate button

**Rationale**: Making insight generation user-triggered (not automatic) avoids unnecessary Gemini API calls on every dashboard visit. The dashboard grid already supports multiple cards. A single component with internal sections keeps the feature self-contained.

**Alternatives considered**:
- Auto-generate on dashboard load: Wasteful API calls, slow page load, poor UX when API is slow
- Separate components per insight type: Over-engineered for v1, adds complexity

## R5: New Backend Endpoint Design

**Decision**: Create a new router `backend/app/routers/insights.py` with a single endpoint `POST /api/insights/generate` that accepts `{ period: "current_month" | "last_month" | "custom", date_from?: string, date_to?: string, type: "summary" | "report" }`. Returns structured insight JSON.

**Rationale**: POST rather than GET because the operation has side effects (API call to Gemini, nontrivial computation). A dedicated router keeps insights logic cleanly separated from transactions. The `type` parameter supports both quick summaries (P1) and full reports (P3) through the same endpoint.

**Alternatives considered**:
- Add endpoints to transactions router: Clutters an already large router
- Separate endpoints per insight type: Unnecessary for v1, can refactor later
- GET endpoint: Misleading since this triggers external API calls and is not idempotent

## R6: Anomaly Detection Strategy

**Decision**: Compute anomalies in Python before sending to Gemini. Query each category's average transaction amount over the past 3 months. Flag individual transactions in the current period that exceed 3x the category average. Pass these pre-identified anomalies to Gemini for natural-language explanation generation.

**Rationale**: Computing anomalies in code ensures accuracy (SC-003 requires 90% accuracy). Letting the AI identify anomalies from raw data is unreliable and unverifiable. The AI's role is to explain the anomalies in plain English, not to detect them.

**Alternatives considered**:
- Let Gemini detect anomalies: Unreliable, can't guarantee accuracy, non-deterministic
- Statistical methods (z-scores, IQR): Over-engineered for v1; simple 3x average threshold is sufficient and understandable
