const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Account API
export interface AccountCreateData {
  name: string;
  type: string;
  institution?: string;
}

export interface AccountUpdateData {
  name?: string;
  type?: string;
  institution?: string;
}

// CSV Import Types
export type AmountMode = 'single' | 'split';

export interface CsvColumnMapping {
  date_column: string;
  description_column: string;
  amount_mode: AmountMode;
  amount_column?: string | null;
  debit_column?: string | null;
  credit_column?: string | null;
  date_format: string;
}

export interface AccountData {
  id: string;
  name: string;
  type: string;
  institution: string | null;
  is_asset: boolean;
  current_balance: number | null;
  csv_column_mapping: CsvColumnMapping | null;
  created_at: string;
}

export async function fetchAccounts(): Promise<AccountData[]> {
  return fetchApi<AccountData[]>('/api/accounts');
}

export async function fetchAccount(id: string): Promise<AccountData> {
  return fetchApi<AccountData>(`/api/accounts/${id}`);
}

export async function createAccount(data: AccountCreateData): Promise<AccountData> {
  return fetchApi<AccountData>('/api/accounts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateAccount(id: string, data: AccountUpdateData): Promise<AccountData> {
  return fetchApi<AccountData>(`/api/accounts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteAccount(id: string): Promise<void> {
  await fetchApi<void>(`/api/accounts/${id}`, {
    method: 'DELETE',
  });
}

// Category API
export interface CategoryCreateData {
  name: string;
  emoji?: string;
  parent_id?: string;
  group_name: string;
  budget_amount?: number;
}

export interface CategoryUpdateData {
  name?: string;
  emoji?: string;
  parent_id?: string | null;
  group_name?: string;
  budget_amount?: number | null;
}

export interface CategoryData {
  id: string;
  name: string;
  emoji: string | null;
  parent_id: string | null;
  group_name: string;
  budget_amount: number | null;
  created_at: string;
}

export interface CategoryTreeNode extends CategoryData {
  children: CategoryTreeNode[];
}

export async function fetchCategories(): Promise<CategoryData[]> {
  return fetchApi<CategoryData[]>('/api/categories');
}

export async function fetchCategoryTree(): Promise<CategoryTreeNode[]> {
  return fetchApi<CategoryTreeNode[]>('/api/categories/tree');
}

export async function fetchCategory(id: string): Promise<CategoryData> {
  return fetchApi<CategoryData>(`/api/categories/${id}`);
}

export async function createCategory(data: CategoryCreateData): Promise<CategoryData> {
  return fetchApi<CategoryData>('/api/categories', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateCategory(id: string, data: CategoryUpdateData): Promise<CategoryData> {
  return fetchApi<CategoryData>(`/api/categories/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteCategory(id: string): Promise<void> {
  await fetchApi<void>(`/api/categories/${id}`, {
    method: 'DELETE',
  });
}

// Transaction API
export interface TransactionData {
  id: string;
  account_id: string;
  date: string;
  description: string;
  original_description: string;
  amount: number;
  category_id: string | null;
  reviewed: boolean;
  reviewed_at: string | null;
  notes: string | null;
  created_at: string;
  // Categorization fields
  normalized_merchant?: string | null;
  confidence_score?: number | null;
  categorization_source?: 'rule' | 'ai' | 'manual' | 'none' | null;
  // Joined fields
  account_name?: string;
  category_name?: string;
  category_emoji?: string;
}

export interface TransactionUpdateData {
  description?: string;
  category_id?: string | null;
  reviewed?: boolean;
  notes?: string | null;
}

export interface TransactionFiltersData {
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

export interface TransactionListResponseData {
  items: TransactionData[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export async function fetchTransactions(
  filters?: TransactionFiltersData
): Promise<TransactionListResponseData> {
  const params = new URLSearchParams();

  if (filters) {
    if (filters.account_id) params.append('account_id', filters.account_id);
    if (filters.category_id) params.append('category_id', filters.category_id);
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    if (filters.amount_min !== undefined) params.append('amount_min', filters.amount_min.toString());
    if (filters.amount_max !== undefined) params.append('amount_max', filters.amount_max.toString());
    if (filters.reviewed !== undefined) params.append('reviewed', filters.reviewed.toString());
    if (filters.search) params.append('search', filters.search);
    if (filters.limit !== undefined) params.append('limit', filters.limit.toString());
    if (filters.offset !== undefined) params.append('offset', filters.offset.toString());
  }

  const queryString = params.toString();
  const url = queryString ? `/api/transactions?${queryString}` : '/api/transactions';

  return fetchApi<TransactionListResponseData>(url);
}

export async function fetchTransaction(id: string): Promise<TransactionData> {
  return fetchApi<TransactionData>(`/api/transactions/${id}`);
}

export async function updateTransaction(
  id: string,
  data: TransactionUpdateData
): Promise<TransactionData> {
  return fetchApi<TransactionData>(`/api/transactions/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteTransaction(id: string): Promise<void> {
  await fetchApi<void>(`/api/transactions/${id}`, {
    method: 'DELETE',
  });
}

// Categorization API
export interface CategorizationTriggerRequestData {
  transaction_ids?: string[];
  force_ai?: boolean;
}

export interface CategorizationBatchResponseData {
  id: string;
  import_id: string | null;
  transaction_count: number;
  success_count: number;
  failure_count: number;
  rule_match_count: number;
  ai_match_count: number;
  skipped_count: number;
  duration_ms: number | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

export interface CategorizationBatchListResponseData {
  batches: CategorizationBatchResponseData[];
  total: number;
  has_more: boolean;
}

export async function triggerCategorization(
  request?: CategorizationTriggerRequestData
): Promise<CategorizationBatchResponseData> {
  return fetchApi<CategorizationBatchResponseData>('/api/categorization/trigger', {
    method: 'POST',
    body: request ? JSON.stringify(request) : undefined,
  });
}

export async function listBatches(
  limit: number = 100,
  offset: number = 0
): Promise<CategorizationBatchListResponseData> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<CategorizationBatchListResponseData>(
    `/api/categorization/batches?${params.toString()}`
  );
}

export async function getBatch(
  batchId: string
): Promise<CategorizationBatchResponseData> {
  return fetchApi<CategorizationBatchResponseData>(
    `/api/categorization/batches/${batchId}`
  );
}

// Categorization Rules API
export interface CategorizationRuleCreateData {
  merchant_pattern: string;
  category_id: string;
}

export interface CategorizationRuleResponseData {
  id: string;
  merchant_pattern: string;
  category_id: string;
  category_name: string | null;
  created_at: string;
}

export interface CategorizationRuleListResponseData {
  rules: CategorizationRuleResponseData[];
  total: number;
  has_more: boolean;
}

export async function listRules(
  categoryId?: string,
  limit: number = 100,
  offset: number = 0
): Promise<CategorizationRuleListResponseData> {
  const params = new URLSearchParams();
  if (categoryId) params.append('category_id', categoryId);
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<CategorizationRuleListResponseData>(
    `/api/categorization/rules?${params.toString()}`
  );
}

export async function createRule(
  data: CategorizationRuleCreateData
): Promise<CategorizationRuleResponseData> {
  return fetchApi<CategorizationRuleResponseData>('/api/categorization/rules', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function deleteRule(ruleId: string): Promise<void> {
  await fetchApi<void>(`/api/categorization/rules/${ruleId}`, {
    method: 'DELETE',
  });
}

// Normalization API
export interface NormalizationRequestData {
  description: string;
}

export interface NormalizationResponseData {
  original: string;
  normalized: string;
  tokens_removed: string[];
}

export async function previewNormalization(
  request: NormalizationRequestData
): Promise<NormalizationResponseData> {
  return fetchApi<NormalizationResponseData>('/api/categorization/normalize', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Review Queue API
export interface DateGroupedTransactions {
  date_label: string;
  date: string;
  transactions: TransactionData[];
}

export interface ReviewQueueResponse {
  groups: DateGroupedTransactions[];
  total_count: number;
  displayed_count: number;
  has_more: boolean;
}

export interface ReviewQueueCountResponse {
  count: number;
}

export type BulkOperationType = 'mark_reviewed' | 'set_category' | 'add_note';

export interface BulkOperationRequest {
  transaction_ids: string[];
  operation: BulkOperationType;
  category_id?: string;
  note?: string;
}

export interface BulkOperationResponse {
  success: boolean;
  affected_count: number;
  operation: BulkOperationType;
  transaction_ids: string[];
}

// Review Queue API Functions

export async function fetchReviewQueue(
  limit: number = 50,
  offset: number = 0
): Promise<ReviewQueueResponse> {
  const params = new URLSearchParams();
  params.append('limit', limit.toString());
  params.append('offset', offset.toString());

  return fetchApi<ReviewQueueResponse>(
    `/api/transactions/review-queue?${params.toString()}`
  );
}

export async function fetchReviewQueueCount(): Promise<ReviewQueueCountResponse> {
  return fetchApi<ReviewQueueCountResponse>('/api/transactions/review-queue/count');
}

export async function bulkUpdateTransactions(
  request: BulkOperationRequest
): Promise<BulkOperationResponse> {
  return fetchApi<BulkOperationResponse>('/api/transactions/bulk', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// CSV Import API
export interface CsvPreviewResponse {
  headers: string[];
  sample_rows: string[][];
  row_count: number;
  suggested_mapping: CsvColumnMapping | null;
}

export type ParsedTransactionStatus = 'valid' | 'warning' | 'error';

export interface ParsedTransaction {
  row_number: number;
  date: string;
  description: string;
  amount: number;
  status: ParsedTransactionStatus;
  status_reason: string | null;
}

export interface CsvParseResponse {
  transactions: ParsedTransaction[];
  valid_count: number;
  warning_count: number;
  error_count: number;
}

export interface BulkTransactionCreateResponse {
  created_count: number;
  account_id: string;
}

export async function previewCsv(fileContent: string): Promise<CsvPreviewResponse> {
  return fetchApi<CsvPreviewResponse>('/api/import/preview', {
    method: 'POST',
    body: JSON.stringify({ file_content: fileContent }),
  });
}

export async function parseCsv(
  accountId: string,
  fileContent: string,
  mapping: CsvColumnMapping
): Promise<CsvParseResponse> {
  return fetchApi<CsvParseResponse>('/api/import/parse', {
    method: 'POST',
    body: JSON.stringify({
      account_id: accountId,
      file_content: fileContent,
      mapping,
    }),
  });
}

export async function createTransactionsFromCsv(
  accountId: string,
  transactions: ParsedTransaction[],
  mapping: CsvColumnMapping,
  saveMapping: boolean = true
): Promise<BulkTransactionCreateResponse> {
  return fetchApi<BulkTransactionCreateResponse>('/api/import/transactions', {
    method: 'POST',
    body: JSON.stringify({
      account_id: accountId,
      transactions,
      mapping,
      save_mapping: saveMapping,
    }),
  });
}

export async function updateAccountMapping(
  accountId: string,
  mapping: CsvColumnMapping
): Promise<AccountData> {
  return fetchApi<AccountData>(`/api/accounts/${accountId}`, {
    method: 'PUT',
    body: JSON.stringify({ csv_column_mapping: mapping }),
  });
}
