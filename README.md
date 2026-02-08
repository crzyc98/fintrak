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
- Python 3.12
- FastAPI 0.115.6
- DuckDB 1.1.3 (embedded database)
- Pydantic 2.10.4

**Frontend:**
- React 19.2.3
- TypeScript 5.x
- Vite 6.2.0
- Tailwind CSS

## Quick Start

The easiest way to start FinTrack is with the CLI:

```bash
./fintrak              # Start both frontend & backend
```

Access the app at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

### CLI Commands

```bash
./fintrak              # Start both services (foreground)
./fintrak start -d     # Start in background (detached)
./fintrak stop         # Stop all services
./fintrak status       # Check what's running
./fintrak backend      # Start only backend
./fintrak frontend     # Start only frontend
./fintrak logs         # Tail logs (when running detached)
```

### Dev Container (Recommended)

Open in VS Code with the Dev Containers extension, or use GitHub Codespaces. The container includes:
- Python 3.12 + uv
- Node.js LTS
- Claude Code CLI
- OpenAI Codex CLI
- Speckit

Everything installs automatically on container creation.

### Manual Setup

If you prefer to run services individually:

**Backend:**
```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

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
