import React, { useState, useEffect, useCallback } from 'react';
import { Account, Category } from '../types';
import {
  fetchTransactions,
  updateTransaction,
  deleteTransaction,
  fetchAccounts,
  fetchCategories,
  triggerCategorization,
  TransactionData,
  TransactionFiltersData,
} from '../src/services/api';

const TransactionsView: React.FC = () => {
  // Transaction state
  const [transactions, setTransactions] = useState<TransactionData[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [limit] = useState(50);

  // Filter state
  const [filters, setFilters] = useState<TransactionFiltersData>({});
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchDebounce, setSearchDebounce] = useState<NodeJS.Timeout | null>(null);

  // Reference data
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);

  // Edit state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<'category' | 'notes' | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Delete confirmation
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  // Selection state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isCategorizing, setIsCategorizing] = useState(false);

  // Load reference data
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const [accountsData, categoriesData] = await Promise.all([
          fetchAccounts(),
          fetchCategories(),
        ]);
        setAccounts(accountsData);
        setCategories(categoriesData);
      } catch (err) {
        console.error('Failed to load reference data:', err);
      }
    };
    loadReferenceData();
  }, []);

  // Load transactions
  const loadTransactions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const offset = (currentPage - 1) * limit;
      const response = await fetchTransactions({
        ...filters,
        limit,
        offset,
      });
      setTransactions(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transactions');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage, limit, filters]);

  useEffect(() => {
    loadTransactions();
  }, [loadTransactions]);

  // Search debounce
  useEffect(() => {
    if (searchDebounce) {
      clearTimeout(searchDebounce);
    }
    const timeout = setTimeout(() => {
      setFilters((prev) => ({ ...prev, search: searchTerm || undefined }));
      setCurrentPage(1);
    }, 300);
    setSearchDebounce(timeout);
    return () => clearTimeout(timeout);
  }, [searchTerm]);

  // Formatting helpers
  const formatAmount = (cents: number): string => {
    const dollars = cents / 100;
    const formatted = Math.abs(dollars).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
    return cents < 0 ? `-$${formatted}` : `$${formatted}`;
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  // Pagination
  const totalPages = Math.ceil(total / limit);
  const canGoPrev = currentPage > 1;
  const canGoNext = currentPage < totalPages;

  // Filter handlers
  const handleFilterChange = (key: keyof TransactionFiltersData, value: string | boolean | undefined) => {
    setFilters((prev) => {
      const newFilters = { ...prev };
      if (value === '' || value === undefined) {
        delete newFilters[key];
      } else {
        (newFilters as Record<string, unknown>)[key] = value;
      }
      return newFilters;
    });
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({});
    setSearchTerm('');
    setCurrentPage(1);
  };

  const hasActiveFilters =
    Object.keys(filters).filter((k) => k !== 'limit' && k !== 'offset').length > 0 || searchTerm;

  // Edit handlers
  const handleCategoryEdit = (transaction: TransactionData) => {
    setEditingId(transaction.id);
    setEditingField('category');
    setEditValue(transaction.category_id || '');
  };

  const handleNotesEdit = (transaction: TransactionData) => {
    setEditingId(transaction.id);
    setEditingField('notes');
    setEditValue(transaction.notes || '');
  };

  const handleCategoryChange = async (transactionId: string, categoryId: string | null) => {
    try {
      await updateTransaction(transactionId, { category_id: categoryId });
      setTransactions((prev) =>
        prev.map((t) =>
          t.id === transactionId
            ? {
                ...t,
                category_id: categoryId,
                category_name: categories.find((c) => c.id === categoryId)?.name || null,
                category_emoji: categories.find((c) => c.id === categoryId)?.emoji || null,
              }
            : t
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update category');
    }
    setEditingId(null);
    setEditingField(null);
  };

  const handleNotesSave = async (transactionId: string) => {
    try {
      await updateTransaction(transactionId, { notes: editValue || null });
      setTransactions((prev) =>
        prev.map((t) => (t.id === transactionId ? { ...t, notes: editValue || null } : t))
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update notes');
    }
    setEditingId(null);
    setEditingField(null);
  };

  const handleReviewToggle = async (transaction: TransactionData) => {
    try {
      const newReviewed = !transaction.reviewed;
      await updateTransaction(transaction.id, { reviewed: newReviewed });
      setTransactions((prev) =>
        prev.map((t) =>
          t.id === transaction.id
            ? { ...t, reviewed: newReviewed, reviewed_at: newReviewed ? new Date().toISOString() : null }
            : t
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update review status');
    }
  };

  const handleDelete = async (transactionId: string) => {
    try {
      await deleteTransaction(transactionId);
      setTransactions((prev) => prev.filter((t) => t.id !== transactionId));
      setTotal((prev) => prev - 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete transaction');
    }
    setDeleteConfirm(null);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingField(null);
    setEditValue('');
  };

  // Selection handlers
  const toggleSelection = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selectedIds.size === transactions.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(transactions.map((t) => t.id)));
    }
  };

  const clearSelection = () => {
    setSelectedIds(new Set());
  };

  // AI Categorization handler
  const handleAICategorize = async () => {
    if (selectedIds.size === 0) return;

    try {
      setIsCategorizing(true);
      setError(null);

      const result = await triggerCategorization({
        transaction_ids: Array.from(selectedIds),
        force_ai: true,
      });

      // Reload transactions to show updated categories
      await loadTransactions();
      clearSelection();

      // Show success message (could be a toast, but using error state for simplicity)
      const categorized = result.success_count;
      if (categorized > 0) {
        // Temporarily show success in a non-blocking way
        console.log(`Categorized ${categorized} transaction(s)`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to categorize transactions');
    } finally {
      setIsCategorizing(false);
    }
  };

  // Clear selection when transactions change (pagination, filters)
  useEffect(() => {
    clearSelection();
  }, [currentPage, filters]);

  if (isLoading && transactions.length === 0) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050910]">
        <div className="text-gray-500">Loading transactions...</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full -mt-4 -mx-10 bg-[#050910]">
      {/* Header */}
      <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
        <h1 className="text-sm font-bold text-gray-300">Transactions</h1>
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search transactions..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-64 bg-[#0a0f1d] border border-white/5 rounded-xl py-2 pl-10 pr-4 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-blue-500/50 placeholder-gray-600 text-gray-300"
            />
            <svg
              className="w-4 h-4 absolute left-3.5 top-2.5 text-gray-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2 rounded-lg transition-colors ${
              showFilters || hasActiveFilters
                ? 'bg-blue-500/20 text-blue-400'
                : 'text-gray-500 hover:text-white hover:bg-white/5'
            }`}
            title="Filters"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="px-8 py-4 border-b border-white/5 bg-[#0a0f1d]/50">
          <div className="flex flex-wrap gap-4 items-end">
            {/* Account Filter */}
            <div>
              <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                Account
              </label>
              <select
                value={filters.account_id || ''}
                onChange={(e) => handleFilterChange('account_id', e.target.value || undefined)}
                className="bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              >
                <option value="">All Accounts</option>
                {accounts.map((account) => (
                  <option key={account.id} value={account.id}>
                    {account.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                Category
              </label>
              <select
                value={filters.category_id || ''}
                onChange={(e) => handleFilterChange('category_id', e.target.value || undefined)}
                className="bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              >
                <option value="">All Categories</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.emoji} {category.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                From
              </label>
              <input
                type="date"
                value={filters.date_from || ''}
                onChange={(e) => handleFilterChange('date_from', e.target.value || undefined)}
                className="bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                To
              </label>
              <input
                type="date"
                value={filters.date_to || ''}
                onChange={(e) => handleFilterChange('date_to', e.target.value || undefined)}
                className="bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              />
            </div>

            {/* Reviewed Filter */}
            <div>
              <label className="block text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1.5">
                Status
              </label>
              <select
                value={filters.reviewed === undefined ? '' : filters.reviewed.toString()}
                onChange={(e) => {
                  const val = e.target.value;
                  handleFilterChange('reviewed', val === '' ? undefined : val === 'true');
                }}
                className="bg-[#0a0f1d] border border-white/10 rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              >
                <option value="">All</option>
                <option value="true">Reviewed</option>
                <option value="false">Unreviewed</option>
              </select>
            </div>

            {/* Clear Filters */}
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="mx-8 mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm flex items-center justify-between">
          <span>{error}</span>
          <div className="flex items-center space-x-2">
            <button
              onClick={loadTransactions}
              className="px-3 py-1 text-sm font-medium text-red-300 hover:text-white border border-red-500/30 rounded-lg transition-colors"
            >
              Retry
            </button>
            <button onClick={() => setError(null)} className="text-red-300 hover:text-white">
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Selection Toolbar */}
      {selectedIds.size > 0 && (
        <div className="px-8 py-3 border-b border-white/5 bg-blue-500/10 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-blue-400">
              {selectedIds.size} transaction{selectedIds.size !== 1 ? 's' : ''} selected
            </span>
            <button
              onClick={clearSelection}
              className="text-sm text-gray-400 hover:text-white transition-colors"
            >
              Clear selection
            </button>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={handleAICategorize}
              disabled={isCategorizing}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-semibold text-white bg-purple-600 hover:bg-purple-500 disabled:bg-purple-600/50 disabled:cursor-not-allowed rounded-xl transition-colors"
            >
              {isCategorizing ? (
                <>
                  <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Categorizing...</span>
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                  <span>AI Categorize</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Transaction Table */}
      <div className="flex-1 overflow-auto px-8 py-4">
        {transactions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <svg
              className="w-16 h-16 text-gray-700 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="1.5"
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
              />
            </svg>
            <p className="text-gray-500 font-medium mb-2">
              {hasActiveFilters ? 'No transactions match your filters' : 'No transactions yet'}
            </p>
            <p className="text-gray-600 text-sm">
              {hasActiveFilters
                ? 'Try adjusting your filters or search term'
                : 'Import transactions from a CSV file to get started'}
            </p>
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
                <th className="text-left py-3 px-4 w-8">
                  <button
                    onClick={toggleSelectAll}
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      selectedIds.size === transactions.length && transactions.length > 0
                        ? 'bg-blue-500 border-blue-500 text-white'
                        : selectedIds.size > 0
                        ? 'bg-blue-500/50 border-blue-500 text-white'
                        : 'border-gray-600 hover:border-gray-400'
                    }`}
                    title={selectedIds.size === transactions.length ? 'Deselect all' : 'Select all'}
                  >
                    {selectedIds.size > 0 && (
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        {selectedIds.size === transactions.length ? (
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        ) : (
                          <path fillRule="evenodd" d="M3 10h14v1H3v-1z" clipRule="evenodd" />
                        )}
                      </svg>
                    )}
                  </button>
                </th>
                <th className="text-left py-3 px-4">Date</th>
                <th className="text-left py-3 px-4">Description</th>
                <th className="text-left py-3 px-4">
                  <div className="flex items-center space-x-1">
                    <span>Category</span>
                    <select
                      value={filters.category_id || ''}
                      onChange={(e) => handleFilterChange('category_id', e.target.value || undefined)}
                      className={`ml-1 bg-transparent border-none text-[10px] font-bold uppercase tracking-widest cursor-pointer focus:outline-none focus:ring-0 ${
                        filters.category_id ? 'text-blue-400' : 'text-gray-500'
                      }`}
                      title="Filter by category"
                    >
                      <option value="">All</option>
                      <option value="__uncategorized__">Uncategorized</option>
                      {categories.map((cat) => (
                        <option key={cat.id} value={cat.id}>
                          {cat.emoji} {cat.name}
                        </option>
                      ))}
                    </select>
                    {filters.category_id && (
                      <button
                        onClick={() => handleFilterChange('category_id', undefined)}
                        className="text-blue-400 hover:text-blue-300"
                        title="Clear filter"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </th>
                <th className="text-left py-3 px-4">
                  <div className="flex items-center space-x-1">
                    <span>Account</span>
                    <select
                      value={filters.account_id || ''}
                      onChange={(e) => handleFilterChange('account_id', e.target.value || undefined)}
                      className={`ml-1 bg-transparent border-none text-[10px] font-bold uppercase tracking-widest cursor-pointer focus:outline-none focus:ring-0 ${
                        filters.account_id ? 'text-blue-400' : 'text-gray-500'
                      }`}
                      title="Filter by account"
                    >
                      <option value="">All</option>
                      {accounts.map((account) => (
                        <option key={account.id} value={account.id}>
                          {account.name}
                        </option>
                      ))}
                    </select>
                    {filters.account_id && (
                      <button
                        onClick={() => handleFilterChange('account_id', undefined)}
                        className="text-blue-400 hover:text-blue-300"
                        title="Clear filter"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    )}
                  </div>
                </th>
                <th className="text-right py-3 px-4">Amount</th>
                <th className="text-center py-3 px-4 w-8">
                  <span className="sr-only">Notes</span>
                </th>
                <th className="text-center py-3 px-4 w-8">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {transactions.map((transaction) => (
                <tr
                  key={transaction.id}
                  className={`group hover:bg-white/5 transition-colors ${
                    transaction.reviewed ? 'opacity-60' : ''
                  } ${selectedIds.has(transaction.id) ? 'bg-blue-500/10' : ''}`}
                >
                  {/* Selection Checkbox + Review Status */}
                  <td className="py-3 px-4">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => toggleSelection(transaction.id)}
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                          selectedIds.has(transaction.id)
                            ? 'bg-blue-500 border-blue-500 text-white'
                            : 'border-gray-600 hover:border-gray-400'
                        }`}
                        title="Select for bulk actions"
                      >
                        {selectedIds.has(transaction.id) && (
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        )}
                      </button>
                      {/* Review toggle */}
                      <button
                        onClick={() => handleReviewToggle(transaction)}
                        className={`transition-colors ${
                          transaction.reviewed
                            ? 'text-green-500 hover:text-green-400'
                            : 'text-gray-600 hover:text-gray-400'
                        }`}
                        title={transaction.reviewed ? 'Mark as unreviewed' : 'Mark as reviewed'}
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          {transaction.reviewed ? (
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          ) : (
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm0-2a6 6 0 100-12 6 6 0 000 12z" clipRule="evenodd" />
                          )}
                        </svg>
                      </button>
                    </div>
                  </td>

                  {/* Date */}
                  <td className="py-3 px-4 text-sm text-gray-400 whitespace-nowrap">
                    {formatDate(transaction.date)}
                  </td>

                  {/* Description */}
                  <td className="py-3 px-4">
                    <div className="text-sm font-medium text-white truncate max-w-xs">
                      {transaction.normalized_merchant || transaction.description}
                    </div>
                    {(transaction.normalized_merchant || transaction.description) !== transaction.original_description && (
                      <div className="text-xs text-gray-600 truncate max-w-xs" title={transaction.original_description}>
                        {transaction.original_description}
                      </div>
                    )}
                  </td>

                  {/* Category */}
                  <td className="py-3 px-4">
                    {editingId === transaction.id && editingField === 'category' ? (
                      <select
                        value={editValue}
                        onChange={(e) => handleCategoryChange(transaction.id, e.target.value || null)}
                        onBlur={cancelEdit}
                        autoFocus
                        className="bg-[#0a0f1d] border border-blue-500/50 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none"
                      >
                        <option value="">Uncategorized</option>
                        {categories.map((cat) => (
                          <option key={cat.id} value={cat.id}>
                            {cat.emoji} {cat.name}
                          </option>
                        ))}
                      </select>
                    ) : (
                      <button
                        onClick={() => handleCategoryEdit(transaction)}
                        className="text-sm text-gray-400 hover:text-white transition-colors text-left"
                      >
                        {transaction.category_id ? (
                          <span>
                            {transaction.category_emoji} {transaction.category_name}
                          </span>
                        ) : (
                          <span className="text-gray-600 italic">Uncategorized</span>
                        )}
                      </button>
                    )}
                  </td>

                  {/* Account */}
                  <td className="py-3 px-4 text-sm text-gray-400">
                    {transaction.account_name || '--'}
                  </td>

                  {/* Amount */}
                  <td className="py-3 px-4 text-right">
                    <span
                      className={`text-sm font-bold tabular-nums ${
                        transaction.amount < 0 ? 'text-red-400' : 'text-green-400'
                      }`}
                    >
                      {formatAmount(transaction.amount)}
                    </span>
                  </td>

                  {/* Notes Indicator */}
                  <td className="py-3 px-4 text-center">
                    {editingId === transaction.id && editingField === 'notes' ? (
                      <input
                        type="text"
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={() => handleNotesSave(transaction.id)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleNotesSave(transaction.id);
                          if (e.key === 'Escape') cancelEdit();
                        }}
                        autoFocus
                        placeholder="Add note..."
                        className="w-32 bg-[#0a0f1d] border border-blue-500/50 rounded px-2 py-1 text-sm text-gray-300 focus:outline-none"
                      />
                    ) : (
                      <button
                        onClick={() => handleNotesEdit(transaction)}
                        className={`p-1 rounded transition-colors ${
                          transaction.notes
                            ? 'text-yellow-500 hover:text-yellow-400'
                            : 'text-gray-600 hover:text-gray-400 opacity-0 group-hover:opacity-100'
                        }`}
                        title={transaction.notes || 'Add note'}
                      >
                        <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M18 13V5a2 2 0 00-2-2H4a2 2 0 00-2 2v8a2 2 0 002 2h3l3 3 3-3h3a2 2 0 002-2zM5 7a1 1 0 011-1h8a1 1 0 110 2H6a1 1 0 01-1-1zm1 3a1 1 0 100 2h3a1 1 0 100-2H6z" />
                        </svg>
                      </button>
                    )}
                  </td>

                  {/* Delete Button */}
                  <td className="py-3 px-4 text-center">
                    <button
                      onClick={() => setDeleteConfirm(transaction.id)}
                      className="p-1 rounded text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                      title="Delete transaction"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="px-8 py-4 flex items-center justify-between border-t border-white/5">
          <div className="text-sm text-gray-500">
            Showing {(currentPage - 1) * limit + 1} to {Math.min(currentPage * limit, total)} of{' '}
            {total.toLocaleString()} transactions
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setCurrentPage((p) => p - 1)}
              disabled={!canGoPrev}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                canGoPrev
                  ? 'text-gray-300 hover:bg-white/5'
                  : 'text-gray-600 cursor-not-allowed'
              }`}
            >
              Previous
            </button>
            <span className="text-sm text-gray-400">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage((p) => p + 1)}
              disabled={!canGoNext}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                canGoNext
                  ? 'text-gray-300 hover:bg-white/5'
                  : 'text-gray-600 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Delete Transaction?</h2>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete this transaction? This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-3 text-sm font-bold text-gray-400 hover:text-white border border-white/10 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteConfirm)}
                className="flex-1 px-4 py-3 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionsView;
