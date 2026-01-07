FinTrack — Product Requirements Document (Improved)

A self-hosted personal finance app
Version: 1.0
Date: January 2026
Author: Nick
Status: Draft
Target Release: Q1 2026
Platform: Self-hosted (Docker)

⸻

1) Executive Summary

FinTrack is a self-hosted personal finance application for spending tracking, budgeting, and net worth monitoring—built for people who want the polish of modern consumer apps (e.g., Copilot Money) without handing over sensitive financial data to third parties.

FinTrack centers on a workflow that’s realistic for privacy-first users: import transactions via CSV, categorize with AI, review quickly, and track trends over time (spend + net worth). Everything runs on the user’s own infrastructure.

1.1 Value Propositions
	•	Full data ownership: financial data stays local (self-hosted volumes)
	•	AI-assisted categorization: fast first-pass classification + learns from corrections
	•	Premium UI: modern dashboard + fast review workflows
	•	Low operating cost: no subscription required (optional API usage for AI)
	•	Homelab-friendly: Docker Compose deployment, simple upgrades, portable database

⸻

2) Problem Statement

The market splits into:
	1.	Commercial SaaS (Copilot Money, Monarch, YNAB): great UX, but recurring cost + third-party data storage
	2.	Self-hosted/open source (Actual, Firefly III): strong control, but UX polish and intelligent categorization often lag

Gap: privacy-first users who still want fast workflows and modern design don’t have a satisfying “daily-driver” option.

⸻

3) Target Users & Personas

Primary user
Technically proficient individual running a homelab who wants privacy, speed, and clarity.

Traits
	•	Comfortable with Docker + basic server admin
	•	Multiple accounts and/or complex finances (cards, investments, loans, crypto, property)
	•	Prefers repeatable processes (monthly review, tidy categories, clean data)
	•	Will invest setup time for long-term control

Secondary user (future)
Household/family member (shared budgets + multi-user), not in MVP.

⸻

4) Goals, Non-Goals, Assumptions

Goals (MVP)
	•	Import CSVs reliably across major institutions
	•	Categorize transactions quickly with AI + allow human correction
	•	Make monthly review fast (queue, bulk actions, search)
	•	Provide clear dashboard: spending + net worth

Non-Goals (MVP)
	•	Real-time bank connectivity (Plaid-style)
	•	Multi-user permissions/roles
	•	Fully automated budgeting/forecasting
	•	Mobile-first experience

Assumptions
	•	User can export CSVs from their institutions
	•	User is willing to do occasional manual balance updates for net worth
	•	Single-user instance initially (no account/login complexity unless needed)

⸻

5) Core User Journeys
	1.	First-run setup
	•	Create accounts → create categories → import first CSV → review queue
	2.	Weekly “cleanup”
	•	Import new CSVs → review uncategorized → correct categories → mark reviewed
	3.	Monthly review
	•	Check spend vs. budget (Phase 2) → top categories → anomalies → net worth changes

⸻

6) Requirements

6.1 Account Management (P0 unless noted)
	•	Support account types: checking, savings, credit card, investment, loan, real estate, crypto
	•	Sidebar grouping by type (Depository, Credit Cards, Investments, Loans, Assets)
	•	Display current balance next to account (manual or latest snapshot)
	•	Asset vs liability flag for net worth
	•	Institution name (P1)
	•	Account status indicator (P2)

Acceptance Criteria
	•	User can create/edit/delete accounts
	•	Net worth math reflects asset/liability correctly
	•	Sidebar groups and totals render consistently

⸻

6.2 Transactions (P0)

6.2.1 CSV Import (P0)
	•	Auto-detect columns for date/description/amount (with user override if ambiguous)
	•	Handle date formats (MM/DD/YYYY, YYYY-MM-DD, etc.)
	•	Support single amount column OR separate debit/credit
	•	Dedupe on import (configurable heuristic; start with strict)
	•	Preserve original_description for traceability

Acceptance Criteria
	•	Import works for at least: Chase, Amex, Bank of America + a “generic” CSV
	•	Duplicate imports do not create duplicates
	•	Import produces a clear summary: inserted / skipped / flagged

6.2.2 Categorization (P0)
	•	AI categorization at import time (Claude API)
	•	Merchant normalization (e.g., “AMZN Mktp” → “Amazon”)
	•	Batch requests to minimize token/API cost
	•	Human correction captured and reused as rules (Phase 2 can be richer; MVP can start simple)

Acceptance Criteria
	•	85% correct first-pass on typical consumer transactions (goal metric)
	•	User can reassign category in <2 clicks
	•	Corrections persist and influence future suggestions

6.2.3 Review Workflow (P0)
	•	“Transactions to review” queue
	•	Group by day (Today / Yesterday / dates)
	•	Multi-select + bulk actions: mark reviewed, set category
	•	Fast inline edit: category, notes, flags

Acceptance Criteria
	•	User can process 100 transactions in under 10 minutes (goal metric)
	•	Bulk mark reviewed works and updates state immediately

6.2.4 Transaction List (P0)
	•	Filter: account, category, date range, amount
	•	Search: description / merchant
	•	Sorting: date desc default

⸻

6.3 Categories & Budgeting

Category Structure (P0)
	•	Hierarchical categories (parent/child)
	•	Category fields: name, emoji, parent_id, group, optional budget_amount
	•	Special types: Income, Transfer (treated differently in analytics)

Budgeting (Phase 2)
	•	Monthly budgets per category
	•	Rollover
	•	Pace indicators

⸻

6.4 Dashboard (P0 MVP subset)

Widgets:
	1.	Monthly Spending
	•	Total spent MTD
	•	Compare to last month
	•	Cumulative line chart + pace line (pace line can be Phase 2 if needed)
	2.	Net Worth
	•	Assets, Debts, Net Worth
	•	Time range selector (1M, 3M, YTD, 1Y, ALL)
	•	Trend lines
	3.	Top Categories
	•	Top spend categories for month + progress bars
	4.	Transactions to Review
	•	Queue + bulk action

⸻

6.5 Net Worth Tracking (P0)
	•	Manual balance snapshots per account
	•	Historical trend visualization
	•	Include non-connected accounts (property, vehicles, crypto) via account types + manual snapshots

Acceptance Criteria
	•	User can enter a balance for any account and see it reflected in net worth history
	•	Net worth = sum(assets) - sum(liabilities) for a given date range

⸻

6.6 Recurring Transactions (Phase 2)
	•	Detect recurring bills/subscriptions via pattern matching
	•	Calendar of upcoming charges
	•	Alerts for abnormal changes

⸻

7) Non-Functional Requirements

7.1 Privacy & Security
	•	Default: local-only deployment (no cloud dependency required)
	•	Secrets (API keys) stored via env vars / Docker secrets
	•	Clear data model separation between “raw import” and “enriched/categorized”

7.2 Performance
	•	Dashboard load: <2s on typical homelab hardware
	•	Import + categorize 100 txns: <30s (goal)

7.3 Reliability & Data Safety
	•	Single-file DB (DuckDB) stored on persistent volume
	•	Backup guidance documented (copy DB file + config)

7.4 Observability (lightweight)
	•	Structured logs for imports + AI calls
	•	Simple “Import history” log table (Phase 1-lite is fine)

⸻

8) MVP Scope (Phase 1)

Included:
	•	Accounts CRUD
	•	Categories CRUD (basic hierarchy)
	•	CSV import + dedupe
	•	AI categorization
	•	Transactions list + filters
	•	Review queue + bulk actions
	•	Manual balances + net worth chart
	•	Dashboard core widgets

Excluded (Phase 2+):
	•	Budget rollover + pace
	•	Recurring detection + calendar
	•	Rule engine beyond basic learning
	•	Multi-user

⸻

9) Technical Architecture
	•	Frontend: React + TypeScript + Tailwind
	•	Charts: Recharts
	•	Backend: FastAPI (Python)
	•	Database: DuckDB (single-file)
	•	AI: Claude API (Anthropic)
	•	Deploy: Docker Compose (web + optional worker)

(Your stack choice aligns well with spec-driven development since you can keep interfaces tight: schema → endpoints → UI components.)

⸻

10) Success Metrics
	•	Import + categorize 100 txns < 30s
	•	Categorization accuracy > 85% first pass
	•	Dashboard load < 2s
	•	Setup from clone to running < 5 minutes
	•	Monthly review workflow < 10 minutes

⸻

Your first five /speckit.specify prompts (copy/paste)

Spec Kit’s workflow generally expects you to start with /specify → /plan → /tasks.  ￼

1) Accounts + Categories foundation (data model + CRUD)

/speckit.specify Build the “Accounts & Categories” foundation for FinTrack (self-hosted personal finance app).

Scope:
- Backend: FastAPI + DuckDB
- Frontend: React + TypeScript + Tailwind
- Single-user, local-first (no auth required for MVP)
- Docker Compose runnable

Requirements:
1) Accounts
- CRUD accounts with fields: id, name, type (checking/savings/credit/investment/loan/real_estate/crypto), institution (optional), is_asset boolean, created_at
- Sidebar grouping by account type and show current balance (derived from latest snapshot if exists, else null)

2) Categories
- CRUD categories with hierarchy: id, name, emoji, parent_id nullable, group_name (Essential/Lifestyle/Income/Transfer/Other), budget_amount nullable
- Validate no circular parent relationships

3) API
- /api/accounts (GET, POST)
- /api/accounts/{id} (GET, PUT, DELETE)
- /api/categories (GET, POST)
- /api/categories/{id} (PUT, DELETE)

4) UI
- Simple Accounts page: list + create/edit
- Simple Categories page: list (tree view is fine) + create/edit
- Sidebar shows grouped accounts and balances

Acceptance criteria:
- CRUD works end-to-end via UI and API
- Data persists across container restarts
- Basic unit tests for validation (e.g., category cycles)

2) Transaction model + list/search/filter UI

/speckit.specify Implement “Transactions core” (data model + transaction list) for FinTrack.

Scope:
- FastAPI + DuckDB backend
- React/TS frontend
- No CSV import yet (that will be next)
- Use existing Accounts + Categories from prior spec

Requirements:
1) Transactions table with fields:
- id, account_id, date, description, original_description, amount
- category_id nullable, reviewed boolean default false, reviewed_at nullable
- notes nullable, created_at

2) API
- GET /api/transactions with filters: account_id, category_id, date_from, date_to, amount_min, amount_max, reviewed
- Sorting: default date desc
- PUT /api/transactions/{id} to update: category_id, reviewed, notes
- DELETE /api/transactions/{id}

3) UI
- Transaction list page/table:
  - Filters: account, category, date range, reviewed status
  - Search by description
  - Inline edit category + notes
  - Toggle reviewed

Acceptance criteria:
- Can view and filter transactions quickly (server-side filtering)
- Inline edits persist and reflect immediately
- Reasonable pagination (cursor or page-based) implemented

3) CSV import + dedupe + mapping

/speckit.specify Add CSV import for transactions in FinTrack with column detection, mapping, and deduplication.

Scope:
- Backend-focused with a minimal UI import flow
- No AI categorization yet (next spec)
- Must support multiple bank CSV formats

Requirements:
1) Import endpoint
- POST /api/import/{account_id}
- Accept CSV file upload
- Auto-detect candidate columns for: date, description, amount
- Support:
  - single amount column (positive/negative)
  - OR separate debit/credit columns (derive signed amount)
  - multiple date formats
- If detection is ambiguous, return a structured response asking for mapping (do not guess silently)

2) Dedupe
- Implement duplicate detection using a stable fingerprint:
  - account_id + date + normalized_description + amount
- On import, skip duplicates and return counts: inserted/skipped

3) Import summary + error handling
- Return a JSON summary: inserted, skipped_duplicates, parse_errors (first N rows), and mapping used
- Do not partially insert without reporting row-level failures

4) Minimal UI
- Account detail page: “Import CSV” button
- Show import result summary and any mapping prompts

Acceptance criteria:
- Chase + Amex + Bank of America + generic CSV can be imported with either auto-detect or mapping
- Re-importing the same file produces 0 new transactions
- Unit tests for dedupe and date parsing

4) AI categorization (Claude) + merchant normalization + batch mode

/speckit.specify Add AI-powered transaction categorization to FinTrack using the Claude API (Anthropic), optimized for batching and cost.

Scope:
- Integrate into the CSV import pipeline
- Provide human override and persist learning signals for future improvements

Requirements:
1) Categorization flow
- On successful import, categorize uncategorized transactions for that import batch
- Use Claude API with batched prompts (configurable batch size)
- Input includes: normalized merchant, raw description, amount sign (expense vs income), and available category list

2) Merchant normalization
- Implement a deterministic normalization step before AI:
  - trim, collapse whitespace, remove obvious bank noise tokens when safe
  - extract likely merchant name
- Store both original_description and normalized merchant/display description

3) Output
- AI returns category_id (or category name to map), and a confidence score (0-1)
- If confidence below threshold, leave uncategorized

4) Learning (MVP-light)
- When user manually changes a category, record a simple rule candidate:
  - normalized merchant -> category_id
- On future imports, apply deterministic rules before calling AI

5) Safety + reliability
- Never send full account numbers or sensitive identifiers in prompts
- Timeouts/retries with clear logging
- Config via env vars: CLAUDE_API_KEY, model name, batch size, confidence threshold

Acceptance criteria:
- Imported transactions get categorized automatically when confidence is high
- Manual corrections persist and influence future imports
- AI calls are batched and logged (counts + duration)
- Tests: rule application precedence over AI

5) Review queue + bulk actions + dashboard widget

/speckit.specify Build the “Transactions to Review” workflow and dashboard widget for FinTrack.

Scope:
- Backend + frontend
- Uses existing transaction model and categorization outputs

Requirements:
1) Review queue definition
- Transactions where reviewed=false
- Default view shows most recent N, grouped by day (Today, Yesterday, older dates)

2) API
- GET /api/transactions/review-queue?limit=&group_by_day=true
- Bulk update endpoint:
  - POST /api/transactions/bulk
  - Operations: mark_reviewed, set_category, add_note
  - Accept list of transaction IDs

3) UI
- Dashboard widget: “Transactions to Review”
  - grouped list + checkboxes
  - bulk “Mark reviewed”
  - quick category assignment (dropdown)
- Dedicated Review page (optional but preferred) for faster processing

Acceptance criteria:
- User can process large batches quickly (checkbox + bulk actions)
- Bulk operations are atomic (all succeed or clear error)
- UI remains responsive for 200+ transactions

If you want, next I can generate a matching feature naming scheme for your specs/001-... folders plus a “golden path” order for /plan so you don’t end up rewriting interfaces midstream.