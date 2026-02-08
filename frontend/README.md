# FinTrack Frontend

A React-based personal finance tracking application with transaction management, categorization, and review workflows.

## Features

- **Dashboard** - Overview of spending, net worth, and transactions to review
- **Transactions** - View, filter, and manage all transactions
- **Review Workflow** - Bulk review and categorize transactions efficiently
- **Accounts** - Manage bank accounts and credit cards
- **Categories** - Organize transactions with custom categories
- **Recurring Transactions** - Track subscriptions and recurring expenses

## Tech Stack

- **React 19** with TypeScript 5.x
- **Vite 6** for development and building
- **Tailwind CSS** for styling
- **Redux Toolkit** for state management

## Getting Started

### Prerequisites

- Node.js 18+
- Backend API running (see `/backend`)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:5173`

### Environment Variables

Create a `.env.local` file:

```env
VITE_API_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── components/           # React components
│   ├── Dashboard.tsx     # Main dashboard view
│   ├── TransactionsView.tsx
│   ├── ReviewPage.tsx    # Full-page review workflow
│   ├── TransactionReview.tsx  # Dashboard review widget
│   ├── ReviewTransactionList.tsx
│   ├── ReviewActionBar.tsx
│   └── ...
├── src/
│   └── services/
│       └── api.ts        # API client functions
├── App.tsx               # Main app with routing
└── types.ts              # TypeScript type definitions
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

The frontend communicates with the FastAPI backend. Key endpoints:

- `GET /api/transactions` - List transactions
- `GET /api/transactions/review-queue` - Get unreviewed transactions
- `POST /api/transactions/bulk` - Bulk update operations
- `GET /api/accounts` - List accounts
- `GET /api/categories` - List categories
