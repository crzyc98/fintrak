
import { Account, Category, Transaction, RecurringItem, TopMover } from './types';

export const MOCK_RECURRING: RecurringItem[] = [
  { 
    id: 'rec-icloud', 
    name: 'Apple iCloud', 
    amount: 0.99, 
    dueDate: 'May 1', 
    type: 'Subscription', 
    frequency: 'Monthly', 
    category: 'SUBSCRIPTIONS', 
    categoryColor: 'bg-pink-500/10 text-pink-400', 
    status: 'Overdue',
    icon: '☁️'
  },
  { 
    id: 'rec-gcloud', 
    name: 'Google Cloud Storage', 
    amount: 29.99, 
    dueDate: 'May 1', 
    type: 'Annually', 
    frequency: 'Annually', 
    category: 'SUBSCRIPTIONS', 
    categoryColor: 'bg-pink-500/10 text-pink-400', 
    status: 'Overdue',
    icon: '👨‍💻'
  },
  { 
    id: 'rec-koinly', 
    name: 'Koinly', 
    amount: 195.30, 
    dueDate: 'May 1', 
    type: 'Annually', 
    frequency: 'Annually', 
    category: 'CRYPTO SERVICES', 
    categoryColor: 'bg-yellow-500/10 text-yellow-500', 
    status: 'Overdue',
    icon: '🪙'
  },
  { 
    id: 'rec-mortgage', 
    name: 'Mortgage', 
    amount: 3323.51, 
    dueDate: 'May 1', 
    type: 'Subscription', 
    frequency: 'Monthly', 
    category: 'MORTGAGE', 
    categoryColor: 'bg-orange-500/10 text-orange-500', 
    status: 'Overdue',
    icon: '🏠'
  },
  { 
    id: 'rec-verizon-w', 
    name: 'Verizon Wireless', 
    amount: 115.50, 
    dueDate: 'May 1', 
    type: 'Subscription', 
    frequency: 'Monthly', 
    category: 'WIRELESS PHONE', 
    categoryColor: 'bg-purple-500/10 text-purple-400', 
    status: 'Overdue',
    icon: '☎️'
  },
  { 
    id: 'rec-grid-1', 
    name: 'Bill Payment National Grid-narragans', 
    amount: 394.90, 
    dueDate: 'May 1', 
    type: 'Bill Payment', 
    frequency: 'Monthly', 
    category: 'UTILITIES', 
    categoryColor: 'bg-orange-500/10 text-orange-400', 
    status: 'Overdue',
    icon: '🔌'
  },
  { 
    id: 'rec-verizon-c', 
    name: 'Verizon Cable', 
    amount: 101.79, 
    dueDate: 'May 1', 
    type: 'Subscription', 
    frequency: 'Monthly', 
    category: 'VERIZON CABLE', 
    categoryColor: 'bg-green-500/10 text-green-500', 
    status: 'Overdue',
    icon: '☎️'
  },
  { 
    id: 'rec-youtube', 
    name: 'YouTube TV', 
    amount: 78.10, 
    dueDate: 'May 28', 
    type: 'Subscription', 
    frequency: 'Monthly', 
    category: 'SUBSCRIPTIONS', 
    categoryColor: 'bg-pink-500/10 text-pink-400', 
    status: 'Overdue',
    icon: '📺',
    rules: {
      name: 'Youtube Tv',
      minAmount: 48.00,
      maxAmount: 100.00,
      frequency: 'month',
      dayOfMonth: 'any day of the month'
    },
    history: [
      { date: 'Jun 2022', value: 75 },
      { date: 'Aug 2022', value: 75 },
      { date: 'Oct 2022', value: 75 },
      { date: 'Dec 2022', value: 75 },
      { date: 'Jan 2023', value: 45 },
      { date: 'Mar 2023', value: 78.10 },
      { date: 'May 2023', value: 78.10 }
    ],
    metrics: [
      { year: '2026', spent: 0, avgTransaction: 0 },
      { year: '2025', spent: 0, avgTransaction: 0 },
      { year: '2024', spent: 0, avgTransaction: 0 },
      { year: '2023', spent: 217.18, avgTransaction: 72.39 },
      { year: '2022', spent: 834.48, avgTransaction: 69.54 }
    ],
    lastAccount: { name: 'Ultimate Rewards®', lastFour: '9631' }
  },
];

export const MOCK_CATEGORIES: Category[] = [
  { 
    id: 'cat-household', 
    name: 'Household', 
    icon: '🏠', 
    budget: 3898, 
    spent: 0, 
    colorClass: 'text-orange-400',
    subCategories: [
      { id: 'sub-mortgage', name: 'Mortgage', icon: '💰', budget: 3345, spent: 0, colorClass: 'text-orange-400' },
      { id: 'sub-utilities', name: 'Utilities', icon: '🔌', budget: 401, spent: 0, colorClass: 'text-orange-400' },
      { id: 'sub-home', name: 'Home', icon: '🏠', budget: 152, spent: 0, colorClass: 'text-orange-400',
        history: [
          { date: 'Jul 2024', value: 120 },
          { date: 'Oct 2024', value: 140 },
          { date: 'Jan 2025', value: 151.89 },
          { date: 'Apr 2025', value: 0 },
          { date: 'Jul 2025', value: 0 },
          { date: 'Jan 2026', value: 0 }
        ],
        metrics: [
          { year: '2026', spent: 0, avgMonthly: 0 },
          { year: '2025', spent: 0, avgMonthly: 0 },
          { year: '2024', spent: 454.21, avgMonthly: 37.85 },
          { year: '2022', spent: 1665.43, avgMonthly: 138.79 }
        ]
      }
    ]
  },
];

export const MOCK_ACCOUNTS: Account[] = [
  { 
    id: '1', 
    name: 'Ultimate Rewards® 9631', 
    type: 'Credit card', 
    balance: 4979.49, 
    statusColor: 'bg-blue-400',
    lastSynced: '3 years ago',
    trendPercent: 19.91,
    logoColor: 'bg-blue-600',
    sparkline: [{val:10}, {val:15}, {val:12}, {val:20}, {val:18}, {val:25}]
  },
  { 
    id: '4', 
    name: 'Joint WROS - TOD', 
    type: 'Investment', 
    balance: 654276.32, 
    statusColor: 'bg-green-500',
    lastSynced: '3 years ago',
    trendPercent: 1.78,
    oneWeekChange: 0.00,
    logoColor: 'bg-green-700',
    sparkline: [{val:200}, {val:180}, {val:220}, {val:210}, {val:250}],
    allocations: [
      { label: 'Mutual fund', percent: 75, color: 'bg-blue-500' },
      { label: 'Equity', percent: 25, color: 'bg-blue-400' }
    ],
    holdings: [
      { ticker: 'FDFIX', name: 'Fidelity Flex 500 Index Fund', changePercent: 0.00, value: 17.79 },
      { ticker: 'FLAPX', name: 'Fidelity Flex Mid Cap Inde...', changePercent: 0.00, value: 14.83 },
    ]
  },
];

export const TOP_MOVERS: TopMover[] = [
  {
    symbol: 'ETH',
    name: 'Ethereum',
    price: 31.61,
    changePercent: 1.94,
    sparkline: [{val:1.8}, {val:2.0}, {val:1.9}, {val:2.1}, {val:2.0}, {val:2.2}, {val:2.1}]
  }
];

export const LIVE_BALANCE_HISTORY = [
  { date: 'Mon', value: 2050000, estimate: false },
  { date: 'Tue', value: 2060000, estimate: false },
  { date: 'Wed', value: 2080000, estimate: false },
  { date: 'Thu', value: 2075000, estimate: false },
  { date: 'Fri', value: 2100000, estimate: false },
  { date: 'Sat', value: 2110000, estimate: false },
  { date: 'Sun', value: 2119906, estimate: true },
];

export const MOCK_TRANSACTIONS: Transaction[] = [
  { 
    id: 't1', 
    merchant: 'Bar Cino - Newport', 
    amount: -92.68, 
    category: 'RESTAURANTS', 
    categoryIcon: '🍔',
    categoryColor: 'bg-orange-500/20 text-orange-400', 
    date: '2023-04-29',
    displayDate: 'Saturday, April 29',
    month: 'April 2023',
    accountName: 'Ultimate Rewards® 9631',
    accountLastFour: '9631',
    reviewed: false, 
    recurring: false 
  },
];

export const SPENDING_CHART_DATA = [
  { day: 0, amount: 0, pace: 0 },
  { day: 31, amount: 900, pace: 1000 }, 
];

export const NET_WORTH_DATA = [
  { date: 'Jan', assets: 2100000, debts: 180000 },
  { date: 'Feb', assets: 2150000, debts: 178000 },
  { date: 'Mar', assets: 2180000, debts: 175000 },
  { date: 'Apr', assets: 2208011, debts: 173186 },
];
