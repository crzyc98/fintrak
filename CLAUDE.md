# FinTrak Development Guidelines

## Tech Stack

**Backend:**
- Python 3.12
- FastAPI 0.115.6
- DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
- Pydantic 2.10.4
- google-genai (Gemini API for AI categorization)

**Frontend:**
- React 19.2.3
- TypeScript 5.8.2
- Vite 6.2.0
- Tailwind CSS

## Project Structure

```
fintrak/
├── backend/
│   ├── app/
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   └── routers/      # API endpoints
│   └── tests/
├── frontend/
│   ├── components/
│   └── src/services/
└── specs/                # Feature specifications
```

## Commands

```bash
# Start the app
./fintrak                 # Both frontend & backend
./fintrak start -d        # Detached mode

# Backend
cd backend && pytest      # Run tests
cd backend && ruff check . # Lint Python

# Frontend
cd frontend && npm run dev       # Dev server
cd frontend && npx tsc --noEmit  # Type check
```

## Code Style

- **Python:** Follow PEP 8, use type hints, Pydantic models for data validation
- **TypeScript:** Strict mode, functional React components with hooks
- **Naming:** snake_case (Python), camelCase (TypeScript)

## Database

DuckDB embedded database at project root (`fintrak.duckdb`). Schema managed via `backend/app/database.py`.

## API

- Base URL: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- All endpoints return JSON, use Pydantic models for request/response validation

## Environment Variables

**Required for AI Categorization:**
- `GEMINI_API_KEY` - Google AI Studio API key (get from https://aistudio.google.com/apikey)

**Optional:**
- `GEMINI_MODEL` - Model to use (default: `gemini-1.5-flash`)
- `CATEGORIZATION_BATCH_SIZE` - Transactions per AI batch (default: 50)
- `CATEGORIZATION_TIMEOUT_SECONDS` - API timeout (default: 120)

## AI Categorization

The app uses Google Gemini API for transaction categorization:
- Module: `backend/app/services/gemini_client.py`
- Fallback: `backend/app/services/claude_client.py` (deprecated, retained for rollback)
- Error classes: `AIClientError`, `AITimeoutError`, `AIInvocationError`
- Retry logic: Exponential backoff (2s, 4s, 8s delays)

## Recent Changes
- 008-live-networth: Added Python 3.12 (backend), TypeScript 5.8.2 (frontend) + FastAPI 0.115.6, React 19.2.3, recharts 3.6.0, Vite 6.2.0, Tailwind CSS

- 007-gemini-api-integration: Replaced Claude CLI with Gemini API for AI categorization
- 006-date-range-presets: Added date range preset filters to transactions view

## Active Technologies
- Python 3.12 (backend), TypeScript 5.8.2 (frontend) + FastAPI 0.115.6, React 19.2.3, recharts 3.6.0, Vite 6.2.0, Tailwind CSS (008-live-networth)
