# FinTrak Development Guidelines

## Tech Stack

**Backend:**
- Python 3.12
- FastAPI 0.115.6
- DuckDB 1.1.3 (file-based: `fintrak.duckdb`)
- Pydantic 2.10.4

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
