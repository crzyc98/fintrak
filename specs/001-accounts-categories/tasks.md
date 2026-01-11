# Tasks: Accounts & Categories Foundation

**Input**: Design documents from `/specs/001-accounts-categories/`
**Prerequisites**: plan.md (required), spec.md (required)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/` for FastAPI, `frontend/` for React
- Backend: `backend/app/` for source, `backend/tests/` for tests
- Frontend: `frontend/src/` for source (existing scaffold in `frontend/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and backend structure

- [x] T001 Create backend project structure: `backend/app/`, `backend/tests/`, `backend/app/models/`, `backend/app/routers/`, `backend/app/services/`
- [x] T002 Create `backend/requirements.txt` with FastAPI, uvicorn, pydantic, duckdb dependencies
- [x] T003 [P] Create `backend/Dockerfile` for Python 3.11+ with uvicorn entrypoint
- [x] T004 [P] Create `docker-compose.yml` with backend and frontend services, volume mount for DuckDB
- [x] T005 [P] Create `.gitignore` with Python, Node.js, and DuckDB patterns
- [x] T006 [P] Create `.dockerignore` with build artifacts and dev dependencies
- [x] T007 Create `backend/app/__init__.py` and `backend/app/main.py` with FastAPI app initialization
- [x] T008 Create `backend/app/database.py` with DuckDB connection management and schema initialization

**Checkpoint**: Backend skeleton ready, database connection established

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T009 Create database schema for `accounts` table in `backend/app/database.py`: id (UUID), name (VARCHAR 100), type (VARCHAR 20), institution (VARCHAR 200), is_asset (BOOLEAN), created_at (TIMESTAMP)
- [x] T010 Create database schema for `categories` table in `backend/app/database.py`: id (UUID), name (VARCHAR 100), emoji (VARCHAR 10), parent_id (UUID nullable), group_name (VARCHAR 20), budget_amount (INTEGER nullable), created_at (TIMESTAMP)
- [x] T011 [P] Create `backend/app/models/__init__.py` with model exports
- [x] T012 [P] Create frontend API client in `frontend/src/services/api.ts` with base URL configuration and fetch helpers

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Create and Manage Financial Accounts (Priority: P1) 🎯 MVP

**Goal**: Users can create, view, edit, and delete financial accounts with type-based grouping

**Independent Test**: Create accounts of different types (Checking, Savings, Credit Card) and verify they appear correctly grouped in the sidebar

### Implementation for User Story 1

- [x] T013 [P] [US1] Create Account Pydantic models in `backend/app/models/account.py`: AccountType enum, AccountCreate, AccountUpdate, AccountResponse schemas
- [x] T014 [US1] Implement AccountService in `backend/app/services/account_service.py`: create, get_all, get_by_id, update, delete methods with DuckDB queries
- [x] T015 [US1] Add is_asset auto-assignment logic in AccountService.create() based on account type (Checking/Savings/Investment/RealEstate/Crypto=true, Credit/Loan=false)
- [x] T016 [US1] Add deletion validation in AccountService.delete() to check for associated records (placeholder for future transactions/snapshots)
- [x] T017 [US1] Create accounts router in `backend/app/routers/accounts.py`: GET /api/accounts, POST /api/accounts, GET /api/accounts/{id}, PUT /api/accounts/{id}, DELETE /api/accounts/{id}
- [x] T018 [US1] Register accounts router in `backend/app/main.py`
- [x] T019 [US1] Update frontend types in `frontend/types.ts`: Add AccountType enum matching spec (Checking, Savings, Credit, Investment, Loan, Real Estate, Crypto), update Account interface with is_asset field
- [x] T020 [US1] Add account API functions in `frontend/src/services/api.ts`: fetchAccounts, createAccount, updateAccount, deleteAccount
- [x] T021 [US1] Create AccountForm component in `frontend/components/forms/AccountForm.tsx` with name, type (dropdown), institution fields and inline validation
- [x] T022 [US1] Update AccountsView in `frontend/components/AccountsView.tsx` to fetch from API instead of mock data, add create/edit/delete UI triggers
- [x] T023 [US1] Add inline validation error display in AccountForm for name length (max 100), required fields

**Checkpoint**: Users can fully manage accounts via UI and API

---

## Phase 4: User Story 2 - Create and Organize Spending Categories (Priority: P1)

**Goal**: Users can create a hierarchy of spending categories with emoji, group, and budget support

**Independent Test**: Create parent and child categories with different groups and verify the hierarchy displays correctly in the tree view

### Implementation for User Story 2

- [x] T024 [P] [US2] Create Category Pydantic models in `backend/app/models/category.py`: CategoryGroup enum, CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTree schemas
- [x] T025 [US2] Implement CategoryService in `backend/app/services/category_service.py`: create, get_all, get_tree, get_by_id, update, delete methods
- [x] T026 [US2] Add circular parent detection in CategoryService: validate parent_id is not self or any descendant
- [x] T027 [US2] Add child category check in CategoryService.delete() to prevent deletion when children exist
- [x] T028 [US2] Create categories router in `backend/app/routers/categories.py`: GET /api/categories, GET /api/categories/tree, POST /api/categories, GET /api/categories/{id}, PUT /api/categories/{id}, DELETE /api/categories/{id}
- [x] T029 [US2] Register categories router in `backend/app/main.py`
- [x] T030 [US2] Update frontend types in `frontend/types.ts`: Add CategoryGroup enum (Essential, Lifestyle, Income, Transfer, Other), update Category interface with group_name, budget stored as cents
- [x] T031 [US2] Add category API functions in `frontend/src/services/api.ts`: fetchCategories, fetchCategoryTree, createCategory, updateCategory, deleteCategory
- [x] T032 [US2] Create CategoryForm component in `frontend/components/forms/CategoryForm.tsx` with name, emoji, parent (dropdown), group (dropdown), budget fields and inline validation
- [x] T033 [US2] Update CategoriesView in `frontend/components/CategoriesView.tsx` to fetch from API instead of mock data, add create/edit/delete UI triggers
- [x] T034 [US2] Add inline validation error display in CategoryForm for name length, circular parent prevention message

**Checkpoint**: Users can fully manage hierarchical categories via UI and API

---

## Phase 5: User Story 3 - View Account Balances in Sidebar (Priority: P2)

**Goal**: Show current balances next to accounts in the sidebar (from snapshots if available, otherwise null)

**Independent Test**: Verify the sidebar displays account names with balance (if snapshot exists) or "--" indicator (if no snapshot)

### Implementation for User Story 3

- [x] T035 [US3] Create balance_snapshots table schema in `backend/app/database.py`: id (UUID), account_id (UUID), balance (INTEGER cents), snapshot_date (DATE), created_at (TIMESTAMP)
- [x] T036 [US3] Add get_latest_balance method to AccountService in `backend/app/services/account_service.py` to query most recent snapshot per account
- [x] T037 [US3] Extend GET /api/accounts endpoint in `backend/app/routers/accounts.py` to include current_balance field (nullable) from latest snapshot
- [x] T038 [US3] Update AccountResponse schema in `backend/app/models/account.py` to include current_balance (Optional[int])
- [x] T039 [US3] Update Sidebar component in `frontend/components/Sidebar.tsx` to fetch accounts from API and display balance or "--" for null
- [x] T040 [US3] Sort accounts alphabetically by name within each type group in Sidebar

**Checkpoint**: Sidebar shows live account balances from backend

---

## Phase 6: User Story 4 - Data Persistence Across Sessions (Priority: P2)

**Goal**: All account and category data persists across application/container restarts

**Independent Test**: Create accounts/categories, restart the Docker container, verify all data is preserved

### Implementation for User Story 4

- [x] T041 [US4] Configure DuckDB file path in `backend/app/database.py` to use volume-mounted path (e.g., `/data/fintrak.duckdb`)
- [x] T042 [US4] Update `docker-compose.yml` to mount persistent volume for `/data` directory
- [x] T043 [US4] Add database initialization check on app startup in `backend/app/main.py` to create tables if not exists
- [x] T044 [US4] Add health check endpoint GET /api/health in `backend/app/main.py` to verify database connectivity

**Checkpoint**: Data survives container restarts

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T045 [P] Add CORS middleware configuration in `backend/app/main.py` for frontend origin
- [x] T046 [P] Add request logging middleware in `backend/app/main.py`
- [x] T047 Remove mock data usage from `frontend/components/AccountsView.tsx` and `frontend/components/CategoriesView.tsx`
- [x] T048 Update `frontend/App.tsx` to handle API loading states and errors gracefully
- [x] T049 [P] Create `backend/tests/__init__.py` and `backend/tests/conftest.py` with test database fixtures
- [x] T050 [P] Create `backend/tests/test_accounts.py` with CRUD operation tests
- [x] T051 [P] Create `backend/tests/test_categories.py` with CRUD and circular parent detection tests

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Accounts) and US2 (Categories) can proceed in parallel
  - US3 (Sidebar balances) depends on US1 completion
  - US4 (Persistence) can proceed in parallel with US1/US2
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Independent of US1
- **User Story 3 (P2)**: Depends on US1 (needs accounts to exist and display)
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Independent infrastructure work

### Within Each User Story

- Models before services
- Services before routers/endpoints
- Backend before frontend for same feature
- Core implementation before validation/edge cases

### Parallel Opportunities

- T003, T004, T005, T006 can run in parallel (different files)
- T011, T012 can run in parallel (different projects)
- T013 can start while T014-T018 wait for models
- US1 and US2 can be worked on in parallel after Phase 2
- T049, T050, T051 can run in parallel (test files)

---

## Parallel Example: Phase 1 Setup

```bash
# These tasks can run in parallel (different files):
T003: Create backend/Dockerfile
T004: Create docker-compose.yml
T005: Create .gitignore
T006: Create .dockerignore
```

## Parallel Example: User Stories 1 & 2

```bash
# After Phase 2 completes, these user stories can proceed in parallel:
# Team Member A: User Story 1 (Accounts)
T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023

# Team Member B: User Story 2 (Categories)
T024 → T025 → T026 → T027 → T028 → T029 → T030 → T031 → T032 → T033 → T034
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Accounts)
4. **STOP and VALIDATE**: Test account CRUD independently
5. Deploy/demo if ready - users can manage accounts

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy (MVP: Account management)
3. Add User Story 2 → Test independently → Deploy (Add: Category management)
4. Add User Story 3 → Test independently → Deploy (Add: Sidebar balances)
5. Add User Story 4 → Test independently → Deploy (Add: Persistence guarantee)
6. Each story adds value without breaking previous stories

### Single Developer Strategy

1. Complete Setup (T001-T008)
2. Complete Foundational (T009-T012)
3. Complete US1 Accounts (T013-T023) - test and verify
4. Complete US2 Categories (T024-T034) - test and verify
5. Complete US3 Sidebar (T035-T040) - test and verify
6. Complete US4 Persistence (T041-T044) - test and verify
7. Complete Polish (T045-T051)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Existing frontend scaffold in `frontend/` - update rather than recreate
- DuckDB chosen for single-file persistence - no separate database server needed
- All monetary values stored as integers (cents) to avoid floating-point issues

## Summary

| Metric | Value |
|--------|-------|
| Total Tasks | 51 |
| Phase 1 (Setup) | 8 tasks |
| Phase 2 (Foundational) | 4 tasks |
| Phase 3 (US1 Accounts) | 11 tasks |
| Phase 4 (US2 Categories) | 11 tasks |
| Phase 5 (US3 Sidebar) | 6 tasks |
| Phase 6 (US4 Persistence) | 4 tasks |
| Phase 7 (Polish) | 7 tasks |
| Parallel Opportunities | 15 tasks marked [P] |
| MVP Scope | Phases 1-3 (23 tasks) |
