
// API Account Types matching backend
export type AccountType = 'Checking' | 'Savings' | 'Credit' | 'Investment' | 'Loan' | 'Real Estate' | 'Crypto';

// Legacy types for mock data compatibility
export type LegacyAccountType = 'Credit card' | 'Depository' | 'Investment';

export const ACCOUNT_TYPES: AccountType[] = ['Checking', 'Savings', 'Credit', 'Investment', 'Loan', 'Real Estate', 'Crypto'];

export const ASSET_ACCOUNT_TYPES: AccountType[] = ['Checking', 'Savings', 'Investment', 'Real Estate', 'Crypto'];

// Category Groups
export type CategoryGroup = 'Essential' | 'Lifestyle' | 'Income' | 'Transfer' | 'Other';

export const CATEGORY_GROUPS: CategoryGroup[] = ['Essential', 'Lifestyle', 'Income', 'Transfer', 'Other'];

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

// API Account interface matching backend
export interface Account {
  id: string;
  name: string;
  type: AccountType;
  institution: string | null;
  is_asset: boolean;
  current_balance: number | null;
  created_at: string;
}

// Legacy Account interface for mock data compatibility
export interface LegacyAccount {
  id: string;
  name: string;
  type: LegacyAccountType;
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

// API Category interface matching backend
export interface Category {
  id: string;
  name: string;
  emoji: string | null;
  parent_id: string | null;
  group_name: CategoryGroup;
  budget_amount: number | null;
  created_at: string;
}

export interface CategoryTreeNode extends Category {
  children: CategoryTreeNode[];
}

// Legacy Category interface for mock data compatibility
export interface LegacyCategory {
  id: string;
  name: string;
  parentId?: string;
  budget: number;
  spent: number;
  colorClass: string;
  icon: string;
  subCategories?: LegacyCategory[];
  history?: { date: string; value: number }[];
  metrics?: CategoryMetric[];
}

// Legacy Transaction interface for mock data compatibility
export interface LegacyTransaction {
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

// API Transaction interface matching backend
export interface Transaction {
  id: string;
  account_id: string;
  date: string;  // ISO date string YYYY-MM-DD
  description: string;
  original_description: string;
  amount: number;  // Integer cents
  category_id: string | null;
  reviewed: boolean;
  reviewed_at: string | null;  // ISO datetime string
  notes: string | null;
  created_at: string;  // ISO datetime string

  // Categorization fields
  normalized_merchant?: string | null;
  confidence_score?: number | null;
  categorization_source?: 'rule' | 'ai' | 'manual' | 'none' | null;

  // Joined fields
  account_name?: string;
  category_name?: string;
  category_emoji?: string;
}

// For update requests (partial)
export interface TransactionUpdate {
  description?: string;
  category_id?: string | null;
  reviewed?: boolean;
  notes?: string | null;
}

// Paginated response
export interface TransactionListResponse {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Filter parameters
export interface TransactionFilters {
  account_id?: string;
  category_id?: string;
  date_from?: string;
  date_to?: string;
  amount_min?: number;
  amount_max?: number;
  reviewed?: boolean;
  search?: string;
  limit?: number;
  offset?: number;
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

// ============================================================================
// Categorization Types
// ============================================================================

export interface CategorizationTriggerRequest {
  transaction_ids?: string[];
  force_ai?: boolean;
}

export interface CategorizationBatchResponse {
  id: string;
  import_id?: string | null;
  transaction_count: number;
  success_count: number;
  failure_count: number;
  rule_match_count: number;
  ai_match_count: number;
  skipped_count: number;
  duration_ms?: number | null;
  error_message?: string | null;
  started_at: string;
  completed_at?: string | null;
}

export interface CategorizationRuleCreate {
  merchant_pattern: string;
  category_id: string;
}

export interface CategorizationRuleResponse {
  id: string;
  merchant_pattern: string;
  category_id: string;
  category_name?: string | null;
  created_at: string;
}

export interface CategorizationRuleListResponse {
  rules: CategorizationRuleResponse[];
  total: number;
  has_more: boolean;
}
