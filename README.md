# FinTrack

A personal finance tracking application with AI-powered categorization and transaction review workflows.

## Overview

FinTrack helps you manage your finances by:
- Importing and organizing transactions from bank accounts
- AI-powered automatic categorization
- Efficient bulk review workflows
- Budget tracking and spending insights

## Architecture

```
fintrak/
├── backend/          # FastAPI + Python backend
│   ├── app/
│   │   ├── models/   # Pydantic models
│   │   ├── services/ # Business logic
│   │   └── routers/  # API endpoints
│   └── tests/
├── frontend/         # React + TypeScript frontend
│   ├── components/
│   └── src/services/
└── specs/            # Feature specifications
```

## Tech Stack

**Backend:**
- Python 3.11
- FastAPI 0.115.6
- DuckDB 1.1.3 (embedded database)
- Pydantic 2.10.4

**Frontend:**
- React 19.2.3
- TypeScript 5.x
- Vite 6.2.0
- Tailwind CSS

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

App available at `http://localhost:5173`

## Features

### Transaction Management
- Import transactions from CSV
- Filter by account, category, date, amount
- Search transactions

### AI Categorization
- Rule-based categorization from merchant patterns
- AI-powered categorization for unknown merchants
- Manual category corrections create new rules

### Review Workflow
- View unreviewed transactions grouped by date
- Bulk mark as reviewed
- Bulk assign categories
- Bulk add notes
- Dashboard widget with quick preview
- Dedicated full-page review mode

### Accounts & Categories
- Multiple account types (checking, savings, credit, investment)
- Hierarchical category structure
- Budget tracking per category

## API Documentation

When the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

```bash
# Run backend tests
cd backend && pytest

# Check Python code style
cd backend && ruff check .

# Check TypeScript types
cd frontend && npx tsc --noEmit
```

## License

MIT
