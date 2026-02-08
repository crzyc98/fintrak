
import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { AreaChart, Area, BarChart, Bar, ResponsiveContainer, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import {
  fetchAccounts,
  fetchTransactions,
  fetchCategories,
  AccountData,
  TransactionData,
  CategoryData,
} from '../src/services/api';

type Timeframe = 'Daily' | 'Monthly' | 'Quarterly' | 'Yearly';

const CreditSpendingView: React.FC = () => {
  const [timeframe, setTimeframe] = useState<Timeframe>('Monthly');
  const [dateRange, setDateRange] = useState({ start: '2022-01-01', end: '2026-12-31' });

  // Data state
  const [accounts, setAccounts] = useState<AccountData[]>([]);
  const [transactions, setTransactions] = useState<TransactionData[]>([]);
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter for credit accounts only
  const creditAccounts = useMemo(() =>
    accounts.filter(a => a.type === 'Credit'),
  [accounts]);

  const [selectedAccountIds, setSelectedAccountIds] = useState<Set<string>>(new Set());

  // Initialize selected accounts when credit accounts load
  useEffect(() => {
    if (creditAccounts.length > 0 && selectedAccountIds.size === 0) {
      setSelectedAccountIds(new Set(creditAccounts.map(a => a.id)));
    }
  }, [creditAccounts]);

  const toggleAccount = (id: string) => {
    const next = new Set(selectedAccountIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedAccountIds(next);
  };

  // Load reference data (accounts and categories)
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
        setError(err instanceof Error ? err.message : 'Failed to load data');
      }
    };
    loadReferenceData();
  }, []);

  // Load transactions for selected accounts
  const loadTransactions = useCallback(async () => {
    if (selectedAccountIds.size === 0) {
      setTransactions([]);
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      // Fetch transactions for each selected account, paginating through all
      const allTransactions: TransactionData[] = [];
      const PAGE_SIZE = 200;

      for (const accountId of selectedAccountIds) {
        let offset = 0;
        let hasMore = true;

        while (hasMore) {
          const response = await fetchTransactions({
            account_id: accountId,
            date_from: dateRange.start,
            date_to: dateRange.end,
            limit: PAGE_SIZE,
            offset,
          });
          allTransactions.push(...response.items);
          hasMore = response.has_more;
          offset += PAGE_SIZE;
        }
      }

      setTransactions(allTransactions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transactions');
    } finally {
      setIsLoading(false);
    }
  }, [selectedAccountIds, dateRange]);

  useEffect(() => {
    if (accounts.length > 0) {
      loadTransactions();
    }
  }, [loadTransactions, accounts.length]);

  // Filter for spending (negative amounts = outflows for credit cards)
  const spendingTransactions = useMemo(() => {
    return transactions.filter(t => t.amount < 0);
  }, [transactions]);

  const totalSpent = useMemo(() =>
    Math.abs(spendingTransactions.reduce((acc, t) => acc + t.amount, 0)) / 100,
  [spendingTransactions]);

  const chartData = useMemo(() => {
    const dataMap: Record<string, number> = {};

    spendingTransactions.forEach(t => {
      const date = new Date(t.date + 'T00:00:00');
      let key = '';

      if (timeframe === 'Yearly') {
        key = date.getFullYear().toString();
      } else if (timeframe === 'Quarterly') {
        const q = Math.floor(date.getMonth() / 3) + 1;
        key = `${date.getFullYear()} Q${q}`;
      } else if (timeframe === 'Monthly') {
        key = date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
      } else {
        // Daily
        key = t.date;
      }

      dataMap[key] = (dataMap[key] || 0) + Math.abs(t.amount) / 100;
    });

    if (timeframe === 'Daily') {
      // For Daily, we sort and return cumulative points
      const sortedKeys = Object.keys(dataMap).sort();
      let cumulative = 0;
      return sortedKeys.map(k => {
        cumulative += dataMap[k];
        return { label: k, amount: cumulative };
      });
    }

    // For others, return discrete period totals
    return Object.entries(dataMap)
      .map(([label, amount]) => ({ label, amount }))
      .sort((a, b) => {
        // Parse labels for chronological sorting
        if (timeframe === 'Yearly') {
          return parseInt(a.label) - parseInt(b.label);
        } else if (timeframe === 'Quarterly') {
          // Format: "2025 Q1"
          const [yearA, qA] = a.label.split(' Q');
          const [yearB, qB] = b.label.split(' Q');
          const numA = parseInt(yearA) * 10 + parseInt(qA);
          const numB = parseInt(yearB) * 10 + parseInt(qB);
          return numA - numB;
        } else {
          // Monthly format: "Jan 25" - parse to date for comparison
          const parseMonthLabel = (label: string) => {
            const months: Record<string, number> = {
              'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
              'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
            };
            const [mon, yr] = label.split(' ');
            const year = 2000 + parseInt(yr);
            return year * 12 + (months[mon] || 0);
          };
          return parseMonthLabel(a.label) - parseMonthLabel(b.label);
        }
      });
  }, [spendingTransactions, timeframe]);

  // Build category lookup
  const categoryMap = useMemo(() => {
    const map: Record<string, CategoryData> = {};
    categories.forEach(c => {
      map[c.id] = c;
    });
    return map;
  }, [categories]);

  const categoryBreakdown = useMemo(() => {
    const categorySums: Record<string, { spent: number; emoji: string; name: string }> = {};

    spendingTransactions.forEach(t => {
      const categoryId = t.category_id || 'uncategorized';
      const category = t.category_id ? categoryMap[t.category_id] : null;
      const name = category?.name || t.category_name || 'Uncategorized';
      const emoji = category?.emoji || t.category_emoji || '🔹';

      if (!categorySums[categoryId]) {
        categorySums[categoryId] = { spent: 0, emoji, name };
      }
      categorySums[categoryId].spent += Math.abs(t.amount) / 100;
    });

    return Object.entries(categorySums)
      .map(([id, data]) => [data.name, { spent: data.spent, icon: data.emoji }] as [string, { spent: number; icon: string }])
      .sort((a, b) => b[1].spent - a[1].spent);
  }, [spendingTransactions, categoryMap]);

  // Get account lookup
  const accountMap = useMemo(() => {
    const map: Record<string, AccountData> = {};
    accounts.forEach(a => {
      map[a.id] = a;
    });
    return map;
  }, [accounts]);

  const isPeriodView = timeframe === 'Yearly' || timeframe === 'Quarterly' || timeframe === 'Monthly';

  const formatCurrency = (cents: number): string => {
    const dollars = Math.abs(cents) / 100;
    return dollars.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  };

  if (error) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050910]">
        <div className="text-center">
          <div className="text-red-400 text-lg font-bold mb-2">Error loading data</div>
          <div className="text-gray-500 text-sm">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg text-sm font-bold hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Sidebar: Account Selection */}
      <div className="w-80 flex flex-col border-r border-white/5">
        <div className="px-8 py-4 border-b border-white/5 flex items-center justify-between">
          <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Select Accounts</h2>
          <button
            className="text-[10px] font-bold text-blue-400 hover:text-blue-300 transition-colors"
            onClick={() => setSelectedAccountIds(new Set(creditAccounts.map(a => a.id)))}
          >
            All
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar">
          {creditAccounts.length === 0 && !isLoading && (
            <div className="text-center py-8">
              <div className="text-gray-500 text-sm">No credit accounts found</div>
              <div className="text-gray-600 text-xs mt-1">Add a Credit account to get started</div>
            </div>
          )}
          {creditAccounts.map(account => (
            <div
              key={account.id}
              onClick={() => toggleAccount(account.id)}
              className={`flex items-center p-4 rounded-2xl cursor-pointer border transition-all ${
                selectedAccountIds.has(account.id)
                  ? 'bg-blue-500/10 border-blue-500/30'
                  : 'bg-white/5 border-transparent opacity-60 hover:opacity-100'
              }`}
            >
              <div className={`w-4 h-4 rounded border flex items-center justify-center mr-4 transition-colors ${
                selectedAccountIds.has(account.id) ? 'bg-blue-500 border-blue-500' : 'border-gray-700'
              }`}>
                {selectedAccountIds.has(account.id) && <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path></svg>}
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-bold text-white truncate">{account.name}</div>
                {account.institution && (
                  <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-0.5">{account.institution}</div>
                )}
              </div>
              {account.current_balance !== null && (
                <div className="text-right">
                  <div className="text-sm font-bold text-white">${formatCurrency(account.current_balance)}</div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Main Analysis Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="p-8 flex-1 overflow-y-auto custom-scrollbar">

          {/* Controls Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="bg-[#0a0f1d] border border-white/5 p-1 rounded-xl flex space-x-1">
              {(['Daily', 'Monthly', 'Quarterly', 'Yearly'] as Timeframe[]).map(t => (
                <button
                  key={t}
                  onClick={() => setTimeframe(t)}
                  className={`px-4 py-1.5 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                    timeframe === t ? 'bg-[#3b82f6] text-white shadow-lg shadow-blue-500/20' : 'text-gray-500 hover:text-gray-300'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>

            <div className="flex items-center bg-[#0a0f1d] border border-white/5 px-4 py-2 rounded-xl group cursor-pointer hover:border-white/10 transition-colors">
              <svg className="w-4 h-4 text-gray-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2-2v12a2 2 0 002 2z"></path></svg>
              <span className="text-xs font-bold text-gray-300">
                {new Date(dateRange.start).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} — {new Date(dateRange.end).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
              </span>
              <svg className="w-3.5 h-3.5 text-gray-600 ml-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 9l-7 7-7-7"></path></svg>
            </div>
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-gray-500 text-sm">Loading spending data...</div>
            </div>
          )}

          {/* Hero Chart Pane */}
          {!isLoading && (
            <>
              <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-8 shadow-2xl relative overflow-hidden group">
                <div className="flex justify-between items-start relative z-10 mb-8">
                  <div>
                    <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2">Aggregated Credit Spending</h3>
                    <div className="text-5xl font-black text-white tracking-tighter">${totalSpent.toLocaleString(undefined, { minimumFractionDigits: 2 })}</div>
                    <div className="text-xs font-bold text-gray-500 mt-2">Total spent across {selectedAccountIds.size} account{selectedAccountIds.size !== 1 ? 's' : ''} in the selected range</div>
                  </div>
                  <div className="text-right">
                     <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-1">{timeframe} Average</div>
                     <div className="text-2xl font-black text-white">
                        ${(totalSpent / (chartData.length || 1)).toLocaleString(undefined, { maximumFractionDigits: 0 })}
                     </div>
                  </div>
                </div>

                {chartData.length === 0 ? (
                  <div className="h-[300px] flex items-center justify-center">
                    <div className="text-gray-500 text-sm">No spending data for the selected period</div>
                  </div>
                ) : (
                  <div className="h-[300px] -mx-8 relative">
                    <ResponsiveContainer width="100%" height="100%">
                      {isPeriodView ? (
                        <BarChart data={chartData} margin={{ top: 20, right: 40, left: 40, bottom: 0 }}>
                          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                          <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#4b5563', fontWeight: 700 }} dy={10} />
                          <YAxis hide domain={[0, 'auto']} />
                          <Tooltip
                            cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-[#0a0f1d] border border-white/10 p-4 rounded-2xl shadow-2xl backdrop-blur-md">
                                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">{payload[0].payload.label}</div>
                                    <div className="text-lg font-black text-white">${payload[0].value?.toLocaleString()}</div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Bar dataKey="amount" radius={[6, 6, 0, 0]} barSize={timeframe === 'Monthly' ? undefined : 40}>
                            {chartData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={index === chartData.length - 1 ? '#3b82f6' : '#1e293b'} fillOpacity={index === chartData.length - 1 ? 1 : 0.6} />
                            ))}
                          </Bar>
                        </BarChart>
                      ) : (
                        <AreaChart data={chartData} margin={{ top: 20, right: 40, left: 40, bottom: 0 }}>
                          <defs>
                            <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.2}/>
                              <stop offset="100%" stopColor="#3b82f6" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                          <XAxis dataKey="label" hide />
                          <YAxis hide domain={[0, 'auto']} />
                          <Tooltip
                            cursor={{ stroke: '#3b82f6', strokeWidth: 1, strokeDasharray: '4 4' }}
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                return (
                                  <div className="bg-[#0a0f1d] border border-white/10 p-4 rounded-2xl shadow-2xl backdrop-blur-md">
                                    <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">{payload[0].payload.label}</div>
                                    <div className="text-lg font-black text-white">${payload[0].value?.toLocaleString()}</div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Area
                            type="monotone"
                            dataKey="amount"
                            stroke="#3b82f6"
                            strokeWidth={4}
                            fill="url(#spendGrad)"
                            animationDuration={1000}
                          />
                        </AreaChart>
                      )}
                    </ResponsiveContainer>
                  </div>
                )}
              </div>

              {/* Breakdown Grid */}
              <div className="grid grid-cols-2 gap-8">
                {/* Category Mix */}
                <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 shadow-xl">
                  <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-8">Category Mix</h4>
                  {categoryBreakdown.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-gray-500 text-sm">No category data</div>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {categoryBreakdown.slice(0, 10).map(([name, data]) => {
                        const percent = totalSpent > 0 ? (data.spent / totalSpent) * 100 : 0;
                        return (
                          <div key={name} className="space-y-2">
                            <div className="flex justify-between items-center text-xs font-bold">
                              <span className="flex items-center text-gray-300">
                                <span className="mr-2">{data.icon}</span> {name}
                              </span>
                              <span className="text-white">${data.spent.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                            </div>
                            <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                              <div className="h-full bg-blue-500/40 rounded-full" style={{ width: `${percent}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Top Transactions */}
                <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 shadow-xl">
                  <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-8">Top Transactions</h4>
                  {spendingTransactions.length === 0 ? (
                    <div className="text-center py-8">
                      <div className="text-gray-500 text-sm">No transactions</div>
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {spendingTransactions
                        .sort((a, b) => Math.abs(b.amount) - Math.abs(a.amount))
                        .slice(0, 7)
                        .map(tx => {
                          const category = tx.category_id ? categoryMap[tx.category_id] : null;
                          const emoji = category?.emoji || tx.category_emoji || '💳';
                          const account = accountMap[tx.account_id];
                          return (
                            <div key={tx.id} className="flex items-center justify-between group cursor-pointer">
                              <div className="flex items-center min-w-0">
                                <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center mr-3 text-lg transition-transform group-hover:scale-110 shadow-lg">{emoji}</div>
                                <div className="flex flex-col min-w-0">
                                  <span className="text-xs font-bold text-white truncate group-hover:text-blue-400 transition-colors">{tx.description}</span>
                                  <span className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mt-0.5">
                                    {tx.date} {account ? `• ${account.name}` : ''}
                                  </span>
                                </div>
                              </div>
                              <span className="text-sm font-black text-white tabular-nums">${formatCurrency(tx.amount)}</span>
                            </div>
                          );
                        })}
                    </div>
                  )}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreditSpendingView;
