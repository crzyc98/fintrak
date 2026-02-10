# Tasks: Natural Language Transaction Search

**Input**: Design documents from `/specs/011-nl-transaction-search/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/nl-search-api.md

**Tests**: Not explicitly requested — test tasks omitted. Run `cd backend && pytest` and `cd frontend && npx tsc --noEmit` after implementation to verify.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Configuration for NL search timeout

- [x] T001 Add NL_SEARCH_TIMEOUT_SECONDS config (default: 15) to backend/app/config.py — add `NL_SEARCH_TIMEOUT_SECONDS = int(os.getenv("NL_SEARCH_TIMEOUT_SECONDS", "15"))` alongside existing categorization config

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Pydantic models shared by all user stories

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T002 Add InterpretedFilters, NLSearchRequest, and NLSearchResponse Pydantic models to backend/app/models/transaction.py — follow data-model.md field definitions; InterpretedFilters has all optional fields (date_from, date_to, amount_min, amount_max, category_ids, merchant_keywords, description_keywords, summary); NLSearchRequest has required query (1-500 chars) plus optional manual filter fields matching TransactionFilters; NLSearchResponse extends TransactionListResponse with interpretation (Optional[InterpretedFilters]), fallback (bool), fallback_reason (Optional[str])

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 — Natural Language Search (Priority: P1) MVP

**Goal**: Users can type a natural language query, press Enter, and see matching transactions with an interpretation banner. Falls back to basic text search when AI is unavailable.

**Independent Test**: Type "coffee purchases last month" in the search bar, press Enter, verify coffee-related transactions from last month are returned with an interpretation banner showing "Coffee purchases, last 30 days."

### Implementation for User Story 1

- [x] T003 [US1] Create backend/app/services/nl_search_service.py with build_nl_search_prompt() function — accepts sanitized query, categories list, accounts list, and current date; constructs prompt per research.md R1 structure requesting JSON output with date_from, date_to, amount_min, amount_max, category_ids, merchant_keywords, description_keywords, summary fields; **IMPORTANT**: instruct Gemini to wrap the response in a JSON array `[{...}]` (single-element array) because the existing `invoke_and_parse()` / `extract_json()` pipeline only accepts arrays — a bare object `{...}` would be discarded and silently trigger fallback; also add sanitize_nl_query() that reuses SENSITIVE_PATTERNS from categorization_service.py to strip account numbers, SSNs, etc. from user input before sending to AI
- [x] T004 [US1] Add interpret_query() to backend/app/services/nl_search_service.py — fetches user's categories (from category service) and accounts (from account service) for prompt context; calls build_nl_search_prompt(); invokes Gemini via invoke_and_parse() from gemini_client.py with NL_SEARCH_TIMEOUT_SECONDS timeout; **extract the first element** from the returned list[dict] (since the prompt requests a single-element array); parses that dict into InterpretedFilters model with lenient validation (silently discard invalid category_ids, clamp keyword lists); if the list is empty, treat as uninterpretable (return None); on AIClientError catch, return None to signal fallback
- [x] T005 [US1] Add execute_nl_search() orchestrator to backend/app/services/nl_search_service.py — accepts NLSearchRequest; calls interpret_query(); if interpretation succeeds, check if InterpretedFilters is meaningful (at least one non-null field besides summary) — if all filter fields are null, treat as uninterpretable: return NLSearchResponse with fallback=True and fallback_reason="Could not interpret your query. Try something like: 'coffee purchases last month' or 'groceries over $50'."; if interpretation has valid filters, build TransactionFilters from InterpretedFilters (convert description_keywords to LIKE search string, convert category_ids to category_id if single match); call transaction_service.get_list(filters); return NLSearchResponse with interpretation metadata; if interpretation fails (returns None from AIClientError), execute fallback: use raw query as basic text search via TransactionFilters(search=query), return NLSearchResponse with fallback=True and fallback_reason="AI search unavailable — showing basic text results"
- [x] T006 [US1] Add POST /api/transactions/nl-search endpoint to backend/app/routers/transactions.py — accepts NLSearchRequest body; calls nl_search_service.execute_nl_search(); returns NLSearchResponse; follow existing router patterns (type hints, response_model)
- [x] T007 [P] [US1] Add TypeScript interfaces and nlSearch() function to frontend/src/services/api.ts — add InterpretedFiltersData interface (all optional fields), NLSearchRequestData interface (required query + optional manual filters + pagination), NLSearchResponseData interface (extends TransactionListResponseData with interpretation, fallback, fallback_reason); add nlSearch(request: NLSearchRequestData): Promise<NLSearchResponseData> that POSTs to /api/transactions/nl-search
- [x] T008 [US1] Upgrade search bar to Enter-to-submit with AI indicator in frontend/components/TransactionsView.tsx — replace the existing 300ms debounce search with Enter-key/button submit handler that calls nlSearch(); add isNLSearching state for loading indicator; add AI sparkle icon (small SVG) next to search input that animates during search; keep searchTerm state for controlled input but only trigger API call on Enter; on successful NL response, update transactions/total/has_more from response; on error or when GEMINI is unavailable, fall back to existing fetchTransactions with search param
- [x] T009 [US1] Add interpretation banner, fallback notice, and empty-results guidance to frontend/components/TransactionsView.tsx — below the search bar, show a dismissible chip/banner displaying interpretation.summary when NL search returns results (e.g., "Showing: Coffee purchases in January 2026"); when response.fallback is true, show a yellow notice banner with fallback_reason text (handles both AI-unavailable and uninterpretable-query messages from T005); when NL search returns 0 items with a valid interpretation, show "No transactions matched your search. Try a broader query like 'all purchases last month'." with 2-3 clickable suggestions; add nlSearchResponse state to track the latest NL search response; banner disappears when search is cleared
- [x] T010 [US1] Add example queries display to frontend/components/TransactionsView.tsx — when search bar is empty and focused, show a dropdown or inline hint with 4-5 example queries (e.g., "coffee purchases last month", "Amazon orders over $50", "groceries in January", "subscriptions this year"); clicking an example fills the search bar and triggers the search; style consistently with existing Tailwind dark theme
- [x] T011 [US1] Add AbortController-based request cancellation in frontend/components/TransactionsView.tsx — store an AbortController ref; on each new NL search submit, abort the previous in-flight request; pass signal to nlSearch() fetch call in api.ts (add optional AbortSignal parameter to nlSearch); handle AbortError gracefully (don't show error to user); this fully satisfies FR-009 (explicit submit + cancel in-flight) within the MVP

**Checkpoint**: At this point, User Story 1 should be fully functional — users can type NL queries, get AI-interpreted results, see interpretation banners, cancel in-flight searches, and gracefully fall back to text search

---

## Phase 4: User Story 2 — Fuzzy Merchant Name Matching (Priority: P2)

**Goal**: When users search for merchant brand names (e.g., "Amazon"), the system matches transactions with abbreviated or coded bank descriptions (e.g., "AMZN*MKTP US").

**Independent Test**: Search "Amazon purchases" and verify transactions with description "AMZN*MKTP US 12345" appear in results.

### Implementation for User Story 2

- [x] T012 [US2] Enhance build_nl_search_prompt() in backend/app/services/nl_search_service.py — add explicit instruction to Gemini: "For merchant names, include both the brand name AND common bank description abbreviations/codes (e.g., for Amazon include: amazon, amzn, amzn*mktp; for Walmart include: walmart, wmt; for Starbucks include: starbucks, sbux). Include at least 2-3 variants per merchant."
- [x] T013 [US2] Enhance execute_nl_search() filter building in backend/app/services/nl_search_service.py — when InterpretedFilters has merchant_keywords, build OR'd LIKE conditions that search BOTH t.description and t.normalized_merchant columns: `(LOWER(t.description) LIKE LOWER(?) OR LOWER(t.normalized_merchant) LIKE LOWER(?))` for each keyword, combined with OR between keywords; extend TransactionService.get_all() or build custom query in nl_search_service to support these multi-column OR conditions that the existing TransactionFilters.search field cannot express

**Checkpoint**: Fuzzy merchant matching works — "Amazon" finds "AMZN*MKTP US" transactions

---

## Phase 5: User Story 3 — Search with Combined Filters (Priority: P3)

**Goal**: Natural language queries work alongside manually applied filters (account, date range, amount, category, review status). Manual filters take precedence when they overlap with NL-extracted values.

**Independent Test**: Set account filter to "Chase Sapphire", type "restaurants this year", verify only restaurant transactions from the Chase Sapphire account are returned.

### Implementation for User Story 3

- [x] T014 [US3] Implement merge_filters() in backend/app/services/nl_search_service.py — accepts NLSearchRequest manual filters and InterpretedFilters; applies dimension-based precedence per research.md R3: if manual date_from OR date_to is set, ignore NL date values; if manual amount_min OR amount_max is set, ignore NL amount values; if manual category_id is set, ignore NL category_ids; account_id and reviewed are always manual; merchant_keywords and description_keywords always come from NL; returns merged TransactionFilters; update execute_nl_search() to call merge_filters() instead of building filters directly from InterpretedFilters
- [x] T015 [US3] Update NL search call in frontend/components/TransactionsView.tsx — pass current manual filter state (account_id, category_id, date_from, date_to, amount_min, amount_max, reviewed) from the existing filters state object into the NLSearchRequest body when calling nlSearch(); ensure pagination (limit, offset) is included
- [x] T016 [US3] Update interpretation banner in frontend/components/TransactionsView.tsx — when manual filters are active alongside NL search, show both in the banner (e.g., "Account: Chase Sapphire + AI: restaurants this year"); when user clears search bar, revert to regular fetchTransactions() with only manual filters; ensure clearing NL search does not clear manual filters

**Checkpoint**: All user stories functional — NL search works standalone and combined with manual filters

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T017 Run backend lint and frontend type check — execute `cd backend && ruff check .` and `cd frontend && npx tsc --noEmit`; fix any issues found
- [x] T018 Run quickstart.md validation — follow manual testing steps in specs/011-nl-transaction-search/quickstart.md; verify NL search, interpretation banner, fallback mode, and example queries all work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T002) — core MVP (T003-T011)
- **US2 (Phase 4)**: Depends on US1 completion (T003-T011) — enhances existing service
- **US3 (Phase 5)**: Depends on US1 completion (T003-T011) — adds merge logic to existing service
- **Polish (Phase 6)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories; includes request cancellation (T011) for full FR-009 compliance
- **User Story 2 (P2)**: Depends on US1 — enhances the prompt and query builder created in US1
- **User Story 3 (P3)**: Depends on US1 — adds merge logic to the service created in US1; can run in parallel with US2

### Within Each User Story

- Backend service before endpoint
- Endpoint before frontend API function
- Frontend API function before UI components
- Core UI before enhancement UI (e.g., search bar before interpretation banner)

### Parallel Opportunities

- T001 and T002 can be parallelized (different files)
- T007 [P] [US1] (frontend API types) can run in parallel with T006 [US1] (backend endpoint)
- T012 [US2] and T014 [US3] target the same file (nl_search_service.py) — run sequentially to avoid conflicts
- T015 [US3] (frontend) can run in parallel with T013 [US2] (backend)

---

## Parallel Example: User Story 1

```bash
# After T005 (service) and T006 (endpoint) are complete, launch frontend tasks:
Task T007: "Add TypeScript types and nlSearch() to api.ts"        # Can start immediately
Task T008: "Upgrade search bar in TransactionsView.tsx"           # Needs T007 first

# Within US1 frontend, T009, T010, T011 can run after T008:
Task T009: "Add interpretation banner to TransactionsView.tsx"    # After T008
Task T010: "Add example queries display to TransactionsView.tsx"  # After T008, parallel with T009
Task T011: "Add AbortController cancellation"                     # After T008, parallel with T009/T010
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001)
2. Complete Phase 2: Foundational (T002)
3. Complete Phase 3: User Story 1 (T003-T011)
4. **STOP and VALIDATE**: Test NL search end-to-end with example queries
5. Deploy/demo if ready — users can already search with natural language

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Merchant fuzzy matching now works → Deploy/Demo
4. Add User Story 3 → Combined filters work → Deploy/Demo
5. Polish → Request cancellation, lint, validation → Final release

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Tests not explicitly requested — validate with `pytest` and `tsc --noEmit` after implementation
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- The backend NL search service (nl_search_service.py) is the central file — US2 and US3 enhance it
