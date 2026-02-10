# Feature Specification: AI Spending Insights

**Feature Branch**: `009-ai-spending-insights`
**Created**: 2026-02-10
**Status**: Draft
**Input**: User description: "Use the Gemini API to generate natural-language spending insights and summaries for users."

## Clarifications

### Session 2026-02-10

- Q: Where should the AI Spending Insights appear in the application? → A: New section/card on the existing dashboard alongside Net Worth.
- Q: Should the system limit how frequently a user can regenerate insights? → A: Simple cooldown — minimum 30 seconds between requests.
- Q: Should generated insights be saved for later viewing or generated fresh every time? → A: Ephemeral only — generated fresh each time, never saved.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - On-Demand Spending Summary (Priority: P1)

A user opens the FinTrak dashboard and sees an "Insights" card alongside the existing Net Worth card. The card generates a conversational summary of their spending patterns for the selected time period. The summary highlights top spending categories, notable changes compared to the prior period, and a brief overall assessment.

**Why this priority**: This is the core value proposition — transforming raw transaction data into understandable language. Without this, the feature has no reason to exist.

**Independent Test**: Can be fully tested by loading the dashboard with existing transaction data and verifying the Insights card displays a natural-language summary that accurately reflects the user's actual spending.

**Acceptance Scenarios**:

1. **Given** a user has at least 5 categorized transactions in the current month, **When** they view the dashboard, **Then** the Insights card displays a plain-English summary that mentions their top spending categories and total spending for the period.
2. **Given** a user has categorized transactions in both the current and previous month, **When** they view the dashboard, **Then** the Insights card includes a comparison to the previous period (e.g., "You spent 30% more on dining this month compared to last month").
3. **Given** a user has no transactions for the selected period, **When** they view the dashboard, **Then** the Insights card shows a friendly message indicating there is not enough data to generate insights.
4. **Given** the AI service is temporarily unavailable, **When** a user requests insights, **Then** the system displays a clear error message and allows the user to retry.

---

### User Story 2 - Anomaly Detection (Priority: P2)

A user wants to be alerted to unusual or noteworthy transactions. When viewing insights, the system identifies transactions that are significantly larger than typical spending in that category, or transactions from merchants the user has not purchased from before. These anomalies are called out in a dedicated "Unusual Activity" section.

**Why this priority**: Anomaly detection adds safety and awareness value beyond basic summaries. It helps users catch errors, fraud, or simply be more conscious of outlier spending.

**Independent Test**: Can be tested by inserting a transaction that is 3x or more the average for its category and verifying it appears in the unusual activity section.

**Acceptance Scenarios**:

1. **Given** a user has a transaction that is significantly larger (3x or more) than the average for its category, **When** they view insights, **Then** that transaction is highlighted as unusual with a brief explanation (e.g., "You had an unusually large purchase of $450 at Electronics Store — your average in this category is $120").
2. **Given** all transactions fall within normal ranges, **When** they view insights, **Then** the unusual activity section either does not appear or states that no anomalies were found.
3. **Given** a user has a transaction from a merchant they have never purchased from before, **When** they view insights, **Then** the system may note the new merchant as a point of interest.

---

### User Story 3 - Monthly Financial Health Report (Priority: P3)

A user wants a comprehensive monthly report summarizing their overall financial health. At the start of each new month, or on demand, the system generates a detailed report covering total income vs. expenses, savings rate, category breakdowns, trend observations, and actionable suggestions (e.g., "Consider reducing dining out — it increased 40% this month").

**Why this priority**: This builds on the spending summary (P1) by adding depth and actionable recommendations. It requires more data aggregation and a more sophisticated prompt, making it a natural extension once the core summary is working.

**Independent Test**: Can be tested by requesting a monthly report for a month with sufficient transaction data and verifying it includes income/expense breakdown, category totals, and at least one actionable observation.

**Acceptance Scenarios**:

1. **Given** a user has a full month of transaction data (at least 10 transactions across 3+ categories), **When** they request a monthly report, **Then** the report includes total spending, category breakdown, and at least one trend observation.
2. **Given** a user has data for multiple months, **When** they request a monthly report, **Then** the report includes month-over-month comparisons where relevant.
3. **Given** a user has fewer than 5 transactions for the month, **When** they request a monthly report, **Then** the system indicates that there is insufficient data for a comprehensive report and offers a partial summary instead.

---

### Edge Cases

- What happens when a user has transactions but none are categorized? The system should note that uncategorized transactions limit insight quality and suggest the user categorize their transactions first.
- What happens when the AI returns an unhelpful, inaccurate, or malformed response? The system should gracefully handle bad responses and either retry or display a fallback message rather than showing raw AI output.
- What happens when a user has only one category of spending? The summary should still be generated but adapted to reflect the limited data (no cross-category comparisons).
- What happens when transaction amounts are refunds or credits (negative amounts)? The system should account for refunds in its summaries and not double-count or misrepresent spending.
- What happens when the user's selected time range has no prior period for comparison (e.g., the very first month of use)? The system should generate a summary without comparisons and note that trend data will be available after more usage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate a natural-language spending summary from the user's categorized transaction data for a specified time period.
- **FR-002**: System MUST identify and highlight the user's top spending categories in the summary (by total amount spent).
- **FR-003**: System MUST compare current-period spending to the prior equivalent period (e.g., this month vs. last month) when prior data exists.
- **FR-004**: System MUST detect anomalous transactions — those significantly above the user's typical spending in a category — and surface them with explanatory context.
- **FR-005**: System MUST generate a monthly financial health report including total spending, category breakdown, and actionable observations when requested.
- **FR-006**: System MUST handle insufficient data gracefully, displaying a clear message when there are too few transactions to generate meaningful insights.
- **FR-007**: System MUST handle AI service failures gracefully, showing user-friendly error messages and providing a retry option.
- **FR-008**: System MUST NOT display raw AI output directly to users; all AI-generated content must be validated and formatted before display.
- **FR-009**: System MUST only use categorized transactions for insight generation; uncategorized transactions should be excluded with a note to the user if a significant portion is uncategorized.
- **FR-010**: System MUST allow users to request insights on demand (not only on a schedule).
- **FR-011**: System MUST enforce a minimum 30-second cooldown between insight generation requests to prevent excessive AI service usage. The regenerate button should be disabled during the cooldown with a visible countdown or "try again shortly" indicator.

### Key Entities

- **Spending Insight**: A generated natural-language summary tied to a specific time period, containing overall observations, category breakdowns, and trend comparisons. Key attributes: time period, generation timestamp, summary text, insight type (summary, anomaly, report).
- **Anomaly**: A flagged transaction identified as unusual based on spending patterns. Key attributes: associated transaction, category average, deviation factor, explanation text.
- **Financial Report**: A comprehensive monthly summary including income/expense totals, category breakdowns, trend data, and actionable suggestions. Key attributes: month/year, generated content sections, data snapshot used for generation.

## Assumptions

- The user's transactions are already categorized (via the existing AI categorization or manual categorization features). Insights quality depends on categorization completeness.
- The existing Gemini API integration and credentials will be reused for generating insights.
- Transaction amounts are stored as integer cents. Summaries should display human-readable dollar amounts.
- "Anomalous" transactions are defined as those exceeding 3x the user's average spend in the same category over the past 3 months. This threshold is a reasonable default.
- Insights are ephemeral — generated fresh on each request, never persisted or cached. This keeps the feature simple for the initial release; persistence can be added later if needed.
- A 30-second cooldown between insight generation requests prevents excessive AI API usage without being restrictive.
- The feature is single-user (no multi-user scoping needed) consistent with the current FinTrak architecture.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a spending summary in under 15 seconds from the time they request it.
- **SC-002**: Generated summaries accurately reflect the user's actual spending data — top categories mentioned in the summary match the top categories by dollar amount in the underlying data.
- **SC-003**: Anomalous transactions (3x or more above category average) are correctly identified and surfaced at least 90% of the time.
- **SC-004**: When insufficient data exists (fewer than 5 categorized transactions), the system displays a helpful message instead of a misleading summary 100% of the time.
- **SC-005**: AI service failures result in a user-friendly error message (not a blank screen, raw error, or spinner that never resolves) 100% of the time.
- **SC-006**: Monthly reports include at least one actionable observation or suggestion when the user has 10 or more transactions across 3 or more categories.
