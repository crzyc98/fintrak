# Feature Specification: Natural Language Transaction Search

**Feature Branch**: `011-nl-transaction-search`
**Created**: 2026-02-09
**Status**: Draft
**Input**: User description: "Allow users to search transactions using natural language queries powered by the Gemini API."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Natural Language Search (Priority: P1)

A user wants to find specific transactions without remembering exact merchant names or manually setting date ranges. They type a natural language query like "coffee purchases last month" or "Amazon orders over $50" into the search bar and press Enter to submit. The system interprets their query and returns matching transactions.

**Why this priority**: This is the core value proposition — replacing manual filter configuration with intuitive free-text search. It delivers immediate productivity gains for every user interaction with the transaction list.

**Independent Test**: Can be fully tested by typing a natural language query and verifying that relevant transactions are returned based on the intent of the query.

**Acceptance Scenarios**:

1. **Given** a user has transactions in their account, **When** they type "show me all coffee purchases last month" and press Enter, **Then** the system returns transactions matching coffee-related merchants within last month's date range.
2. **Given** a user has transactions in their account, **When** they type "groceries over $100 in January" and press Enter, **Then** the system returns transactions categorized as groceries with amounts exceeding $100 during January.
3. **Given** a user types a query that matches no transactions, **When** the search completes, **Then** the system displays a clear "no results found" message with a suggestion to try a different query.
4. **Given** a user types a vague or uninterpretable query, **When** the system cannot determine intent, **Then** the system displays a helpful message explaining what types of queries are supported, with examples.

---

### User Story 2 - Fuzzy Merchant Name Matching (Priority: P2)

A user searches for transactions by merchant name but doesn't know the exact name stored in the system (e.g., the bank records show "AMZN*MKTP US" but the user searches for "Amazon"). The system intelligently matches abbreviated, truncated, or coded merchant names to common merchant identities.

**Why this priority**: Raw bank transaction descriptions are often cryptic codes that users don't recognize. Fuzzy matching bridges the gap between what users know (merchant brand names) and what the system stores (raw bank descriptions).

**Independent Test**: Can be fully tested by searching for a well-known merchant brand name and verifying that transactions with abbreviated or coded descriptions for that merchant are returned.

**Acceptance Scenarios**:

1. **Given** a user has transactions with description "AMZN*MKTP US 12345", **When** they search "Amazon purchases", **Then** those transactions appear in the results.
2. **Given** a user has transactions with description "SQ *BLUE BOTTLE COF", **When** they search "Blue Bottle Coffee", **Then** those transactions appear in the results.
3. **Given** a user searches for a merchant with no matching transactions, **When** the search completes, **Then** the system returns no results rather than false positives from unrelated merchants.

---

### User Story 3 - Search with Combined Filters (Priority: P3)

A user wants to combine natural language search with existing manual filters. For example, they type "dining out" while also having the "Chase Sapphire" account selected in the account filter. The natural language query and manual filters work together to narrow results.

**Why this priority**: Power users will want to combine the convenience of natural language with precise manual controls. This integrates seamlessly with the existing filter system rather than replacing it.

**Independent Test**: Can be fully tested by applying a manual filter (e.g., account selector), then typing a natural language query, and verifying results respect both the manual filter and the search intent.

**Acceptance Scenarios**:

1. **Given** a user has the "Chase Sapphire" account selected, **When** they type "restaurants this year", **Then** only restaurant transactions from the Chase Sapphire account are returned.
2. **Given** a user has a date range manually set, **When** they type "subscriptions", **Then** results are limited to the manually set date range, not overridden by the natural language query.
3. **Given** a user has both manual filters and a natural language query active, **When** they clear the search bar, **Then** only the manual filters remain applied.

---

### Edge Cases

- What happens when the AI service is unavailable or times out? The system falls back to the existing text-based search and informs the user that natural language search is temporarily unavailable.
- What happens when the user types a query in a non-English language? The system attempts to process it but displays a message if it cannot interpret the query, suggesting English queries.
- What happens when the user types a query referencing categories that don't exist in their data (e.g., "show travel expenses" but no "travel" category exists)? The system searches across descriptions and merchant names as a fallback, not just categories.
- What happens when the query contains conflicting criteria (e.g., "income expenses last month")? The system makes a best-effort interpretation and displays what criteria it applied so the user can refine.
- What happens when the user rapidly types multiple queries in succession? The system cancels any in-flight search when a new query is submitted, displaying only the most recent results.
- What happens when sensitive data appears in the query (e.g., the user types an account number)? The system sanitizes user input before sending it to the AI service, consistent with existing sanitization practices.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST upgrade the existing search bar to accept natural language queries, with a visual AI indicator showing when NL interpretation is active. When the AI service is unavailable, the same search bar seamlessly falls back to basic text matching.
- **FR-002**: System MUST interpret natural language queries and translate them into structured transaction filters including: date ranges, amount ranges, merchant names, category names, and description keywords.
- **FR-003**: System MUST support temporal references in queries (e.g., "last month", "this year", "in January", "past 30 days") and resolve them relative to the current date.
- **FR-004**: System MUST support amount references in queries (e.g., "over $50", "less than $20", "between $10 and $100") and convert them to appropriate filters.
- **FR-005**: System MUST support merchant name references using fuzzy matching, resolving common brand names to their bank-description equivalents (e.g., "Amazon" matches "AMZN*MKTP US").
- **FR-006**: System MUST support category-based queries (e.g., "groceries", "dining out", "subscriptions") by matching against the user's existing categories.
- **FR-007**: System MUST combine natural language search results with any manually applied filters (account, date range, amount range, review status). When a manual filter is already set on a specific dimension (e.g., date range, amount range), the NL-extracted value for that same dimension is ignored and the manual filter takes precedence. NL-extracted filters only apply to dimensions not already constrained by manual filters.
- **FR-008**: System MUST display the interpreted search criteria to the user (e.g., "Showing: coffee merchants, last 30 days") so users can verify the system understood their intent.
- **FR-009**: System MUST trigger NL search only on explicit submit (Enter key or search button click). If a previous search is still in progress when a new query is submitted, the system MUST cancel the in-flight request and display only the latest results.
- **FR-010**: System MUST fall back to basic text search when the AI service is unavailable, and inform the user that enhanced search is temporarily unavailable.
- **FR-011**: System MUST sanitize user query input before sending to the AI service, removing any sensitive data patterns (account numbers, SSNs, etc.).
- **FR-012**: System MUST display helpful example queries when the search bar is empty or focused, to guide users on supported query types.
- **FR-013**: System MUST paginate natural language search results consistently with existing transaction list pagination.

### Key Entities

- **Search Query**: A natural language text input from the user describing their search intent. Contains the raw query text and a timestamp.
- **Interpreted Filters**: The structured representation of a parsed natural language query, containing extracted date ranges, amount ranges, merchant identifiers, category references, and description keywords. This is what the system applies against the transaction data.
- **Search Result**: A collection of transactions matching both the interpreted filters and any manually applied filters, along with metadata about the interpretation (what criteria were applied, total match count).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can find specific transactions using natural language in under 5 seconds, including AI interpretation time.
- **SC-002**: Natural language search correctly interprets at least 90% of queries involving common patterns (date ranges, amounts, merchant names, categories).
- **SC-003**: Fuzzy merchant name matching correctly resolves at least 80% of common merchant abbreviations (e.g., "AMZN" to "Amazon", "WMT" to "Walmart") to their brand names.
- **SC-004**: Users who use natural language search reduce the number of manual filter adjustments by at least 50% compared to using filters alone.
- **SC-005**: When the AI service is unavailable, the system falls back to basic search within 2 seconds with no loss of existing search functionality.
- **SC-006**: 85% of users can successfully complete a natural language search on their first attempt without needing to rephrase their query.

## Clarifications

### Session 2026-02-09

- Q: How should NL search integrate with the existing search bar UI? → A: Upgrade the existing search bar to support NL queries with an AI indicator, falling back to basic text match when AI is unavailable.
- Q: When NL-extracted filters conflict with manually-set filters on the same dimension, which takes precedence? → A: Manual filters win. If a manual filter is already set on a dimension (e.g., dates, amount range), NL-extracted values for that same dimension are ignored.
- Q: How should NL search be triggered — auto-search on typing or explicit submit? → A: Explicit submit. User must press Enter or click a search button to trigger NL interpretation, avoiding unnecessary AI calls on partial queries.

## Assumptions

- Users primarily search in English. Non-English queries will be handled on a best-effort basis.
- The existing AI service integration and credentials are sufficient for this feature; no additional AI service subscriptions are required.
- Transaction volume per user is manageable for real-time search (the system is a personal finance tracker, not an enterprise-scale ledger).
- The AI service will return structured filter interpretations rather than raw database queries, maintaining a security boundary between AI output and data access.
- Merchant name normalization for fuzzy matching will leverage the existing normalized merchant data and the AI's knowledge of common merchant abbreviations.
- Search history and saved queries are out of scope for this feature.
- Voice input is out of scope; this feature covers text-based natural language input only.

## Scope Boundaries

**In Scope**:
- Natural language query input and AI-powered interpretation
- Fuzzy merchant name matching within search queries
- Integration with existing manual filters
- Display of interpreted search criteria
- Graceful fallback when AI is unavailable
- Input sanitization before AI processing

**Out of Scope**:
- Background merchant normalization/enrichment (separate feature)
- Search history or saved/favorite queries
- Voice-based search input
- Multi-language support beyond English
- Transaction recommendations or proactive suggestions based on search patterns
- Bulk operations on search results (existing bulk operations continue to work as-is)
