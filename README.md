# FinTrak

A personal finance tracking application with AI-powered categorization, spending insights, and transaction review workflows.

## Overview

FinTrak helps you manage your finances by:
- Importing and organizing transactions from bank accounts
- AI-powered automatic categorization via Google Gemini
- AI-generated spending insights and reports
- Net worth tracking across accounts
- Efficient bulk review workflows

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
- Google Gemini API (AI categorization & insights)

**Frontend:**
- React 19.2.3
- TypeScript 5.8.2
- Vite 6.2.0
- Tailwind CSS
- Recharts (data visualization)

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

### Environment Variables

Create a `.env` file in `backend/` (auto-loaded via python-dotenv):

```
GEMINI_API_KEY=your-key-here
```

Get a key at https://aistudio.google.com/apikey. Optional settings:

| Variable | Default | Description |
|---|---|---|
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model to use |
| `CATEGORIZATION_BATCH_SIZE` | `50` | Transactions per AI batch |
| `CATEGORIZATION_TIMEOUT_SECONDS` | `120` | API timeout |

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
- Import transactions from CSV (auto-detects date formats including 2-digit years)
- Filter by account, category, date, amount
- Search transactions

### AI Categorization
- Rule-based categorization from merchant patterns
- Gemini-powered categorization for unknown merchants
- Manual category corrections create new rules
- Batch processing with exponential backoff retry

### AI Spending Insights
- Summary and full report modes
- Period selection: current month, last month, or last 3 months
- Top category breakdown with period-over-period comparison
- Anomaly detection (unusual transactions vs category average)
- AI-generated suggestions and analysis

### Net Worth Dashboard
- Live account balances across all accounts
- Asset vs liability breakdown
- Historical trend visualization

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
