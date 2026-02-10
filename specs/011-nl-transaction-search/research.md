# Research: Natural Language Transaction Search

**Feature**: 011-nl-transaction-search
**Date**: 2026-02-09

## R1: Gemini Prompt Design for Query Interpretation

**Decision**: Use a structured prompt that provides the AI with the user's query, the current date, the user's category list, and account list. Request JSON output with specific filter fields.

**Rationale**: The AI needs context about the user's data to map queries like "groceries" to actual category IDs and to resolve relative dates like "last month." Providing the category/account lists directly in the prompt avoids a separate embedding or lookup step and leverages Gemini's in-context understanding. The existing `invoke_and_parse` flow already handles JSON mode, retry, and extraction.

**Alternatives considered**:
- **Embedding-based semantic search**: Would require vectorizing all transactions and maintaining an embedding index. Overkill for personal finance scale (hundreds of transactions). Adds significant complexity with a vector store.
- **Two-step: AI extracts intent → separate fuzzy matcher**: More complex, slower (two round-trips), and the AI can already handle fuzzy merchant matching by receiving the raw query and returning description keywords.
- **Fine-tuned model**: Unnecessary — Gemini 1.5 Flash handles structured extraction well with zero-shot prompting and JSON mode.

**Prompt Structure**:
```
You are a financial transaction search assistant. Parse the user's natural language
query into structured search filters.

Today's date: {current_date}

Available categories:
{categories_json}

Available accounts:
{accounts_json}

User query: "{sanitized_query}"

Return a JSON object with these fields (omit fields not mentioned in the query):
- date_from: ISO date string (YYYY-MM-DD)
- date_to: ISO date string (YYYY-MM-DD)
- amount_min: integer in cents (e.g., $50 = 5000)
- amount_max: integer in cents
- category_ids: array of category ID strings from the list above
- merchant_keywords: array of merchant name strings to match (include common abbreviations)
- description_keywords: array of general search terms
- summary: human-readable description of what the query means (e.g., "Coffee purchases in January 2026")

Only include fields that the query explicitly or implicitly references.
For merchant names, include both the brand name and common bank description variants.
For amounts, convert dollar values to cents (multiply by 100).
```

## R2: AI Response Schema Validation

**Decision**: Use Pydantic model `InterpretedFilters` to validate AI response. All fields optional. Invalid/missing fields are silently ignored rather than failing the search.

**Rationale**: AI responses are inherently non-deterministic. Strict validation that rejects the whole response on one bad field would degrade user experience. Instead, validate each field independently — use valid fields, discard invalid ones, and still return results. This follows the existing pattern in `categorization_service.py` where invalid category IDs are skipped rather than failing the batch.

**Alternatives considered**:
- **Strict validation (reject on any error)**: Too brittle for AI outputs. Users would see errors for minor AI parsing mistakes.
- **No validation (trust AI output)**: Security risk — AI could return malformed data that causes SQL errors or unexpected behavior.

## R3: Filter Merging Strategy

**Decision**: Dimension-based precedence — manual filters win on any dimension where both manual and NL filters provide a value. NL filters apply only to unconstrained dimensions.

**Rationale**: Per spec clarification (Q2: "Manual filters win"). Implementation: check each dimension (date_from/date_to, amount_min/amount_max, category_id, account_id, reviewed) — if the manual filter has a value, skip the NL-extracted value for that dimension.

**Merge dimensions**:
| Dimension | Manual filter field | NL filter field | Merge rule |
|-----------|-------------------|-----------------|------------|
| Date range | date_from, date_to | date_from, date_to | Manual wins if either date_from or date_to is set manually |
| Amount range | amount_min, amount_max | amount_min, amount_max | Manual wins if either amount bound is set manually |
| Category | category_id | category_ids[] | Manual wins if category_id is set |
| Account | account_id | (not extracted by AI) | Always manual |
| Review status | reviewed | (not extracted by AI) | Always manual |
| Search terms | (none) | merchant_keywords[], description_keywords[] | Always from NL (this is the core NL value-add) |

## R4: Fallback Strategy

**Decision**: On any AI error (timeout, rate limit, API down), fall back to basic text search using the raw query text as a LIKE filter on `t.description`. Display a notice to the user.

**Rationale**: The existing `search` field already supports case-insensitive LIKE on description. Using the raw NL query as a basic text search is a reasonable degradation — "coffee purchases last month" as a LIKE search won't match dates, but "coffee" substring matching will still find coffee merchants. This ensures the search bar never appears broken.

**Fallback flow**:
1. NL search endpoint catches `AIClientError` (or subclasses)
2. Sets `fallback: true` in response metadata
3. Executes existing `transaction_service.get_list()` with `search=raw_query`
4. Frontend shows notice: "AI search unavailable — showing basic text results"

**Alternatives considered**:
- **Return error and show empty state**: Bad UX — user typed a query and gets nothing.
- **Retry silently with longer timeout**: Already handled by `with_retry` — if 3 retries fail, the service is genuinely down.

## R5: Merchant Fuzzy Matching Approach

**Decision**: Delegate fuzzy matching to the AI prompt. Gemini returns `merchant_keywords` which are applied as multiple OR'd LIKE conditions on both `t.description` and `t.normalized_merchant`.

**Rationale**: The AI already knows that "Amazon" maps to "AMZN", "WMT" maps to "Walmart", etc. By asking Gemini to include common abbreviations in `merchant_keywords`, we get fuzzy matching without maintaining a separate merchant alias database. The SQL query uses `OR` across all keywords: `(LOWER(t.description) LIKE '%amzn%' OR LOWER(t.description) LIKE '%amazon%' OR LOWER(t.normalized_merchant) LIKE '%amzn%' OR ...)`.

**Alternatives considered**:
- **Static merchant alias table**: Requires manual curation, doesn't scale to long tail of merchants.
- **Trigram/Levenshtein matching in DuckDB**: Complex, slower, and DuckDB's fuzzy matching support is limited compared to PostgreSQL.
- **Separate merchant normalization service**: Out of scope per spec boundaries.

## R6: Search Timeout Configuration

**Decision**: Use a shorter timeout for NL search (15 seconds) than the categorization timeout (120 seconds). NL search is interactive and users expect fast responses.

**Rationale**: SC-001 requires end-to-end under 5 seconds. Gemini Flash typically responds in 1-3 seconds. A 15-second timeout allows for retry (3 attempts × ~3s each + backoff) while still failing fast enough to trigger fallback within a reasonable window. The existing `CATEGORIZATION_TIMEOUT_SECONDS=120` is designed for batch processing, not interactive search.

**Configuration**: Add `NL_SEARCH_TIMEOUT_SECONDS` env var (default: 15).
