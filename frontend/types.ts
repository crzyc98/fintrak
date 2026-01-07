
export type AccountType = 'Credit card' | 'Depository' | 'Investment';

export interface Holding {
  ticker: string;
  name: string;
  changePercent: number;
  value: number;
}

export interface Allocation {
  label: string;
  percent: number;
  color: string;
}

export interface TopMover {
  symbol: string;
  name: string;
  price: number;
  changePercent: number;
  sparkline: { val: number }[];
}

export interface Account {
  id: string;
  name: string;
  type: AccountType;
  balance: number;
  statusColor: string;
  lastSynced: string;
  trendPercent: number;
  sparkline: { val: number }[];
  iconUrl?: string;
  logoColor?: string;
  holdings?: Holding[];
  allocations?: Allocation[];
  oneWeekChange?: number;
}

export interface CategoryMetric {
  year: string;
  spent: number;
  avgMonthly: number;
}

export interface Category {
  id: string;
  name: string;
  parentId?: string;
  budget: number;
  spent: number;
  colorClass: string;
  icon: string;
  subCategories?: Category[];
  history?: { date: string; value: number }[];
  metrics?: CategoryMetric[];
}

export interface Transaction {
  id: string;
  merchant: string;
  amount: number;
  category: string;
  categoryIcon?: string;
  categoryColor: string;
  date: string; 
  displayDate: string; 
  month: string; 
  accountName: string;
  accountLastFour: string;
  reviewed: boolean;
  recurring?: boolean;
  notes?: string;
  tags?: string[];
}

export interface RecurringRule {
  name: string;
  minAmount: number;
  maxAmount: number;
  frequency: string;
  dayOfMonth: string;
}

export interface RecurringMetric {
  year: string;
  spent: number;
  avgTransaction: number;
}

export interface RecurringItem {
  id: string;
  name: string;
  amount: number;
  dueDate: string;
  type: 'Subscription' | 'Bill' | 'Bill Payment' | 'Annually';
  frequency: 'Monthly' | 'Annually';
  category: string;
  categoryColor: string;
  status: 'Overdue' | 'Paid';
  icon?: string;
  rules?: RecurringRule;
  history?: { date: string; value: number }[];
  metrics?: RecurringMetric[];
  lastAccount?: { name: string; lastFour: string };
}
