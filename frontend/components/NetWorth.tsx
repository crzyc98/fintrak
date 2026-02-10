
import React, { useState, useEffect, useMemo } from 'react';
import { fetchAccounts, AccountData } from '../src/services/api';

const NetWorth: React.FC = () => {
  const [accounts, setAccounts] = useState<AccountData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAccounts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchAccounts();
      setAccounts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load accounts');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAccounts();
  }, []);

  const totals = useMemo(() => {
    const assets = accounts
      .filter((a) => a.is_asset)
      .reduce((sum, a) => sum + (a.current_balance || 0), 0);
    // Don't use Math.abs - negative liability balances (overpayments) should reduce total debt
    const debts = accounts
      .filter((a) => !a.is_asset)
      .reduce((sum, a) => sum + (a.current_balance || 0), 0);
    return { assets, debts, netWorth: assets - debts };
  }, [accounts]);

  const formatBalance = (cents: number): string => {
    return '$' + (cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 });
  };

  if (isLoading) {
    return (
      <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex items-center justify-center h-[460px] shadow-2xl shadow-black/40">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex flex-col items-center justify-center h-[460px] shadow-2xl shadow-black/40">
        <div className="text-red-400 mb-4">{error}</div>
        <button
          onClick={loadAccounts}
          className="text-sm font-semibold text-gray-400 hover:text-white transition-colors px-4 py-2 rounded-lg border border-white/10 hover:border-white/20"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] overflow-hidden relative group shadow-2xl shadow-black/40">
      <div className="flex justify-between items-start mb-6 relative z-10">
        <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Net worth</h2>
        <button className="text-sm font-semibold text-gray-400 hover:text-white transition-colors flex items-center group/btn">
          Accounts
          <svg className="w-3.5 h-3.5 ml-1 transition-transform group-hover/btn:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7"></path>
          </svg>
        </button>
      </div>

      <div className="flex space-x-12 mb-4 relative z-10">
        <div>
          <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] mr-2 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
            Assets
          </div>
          <div className="text-4xl font-extrabold text-white tracking-tight mb-3">{formatBalance(totals.assets)}</div>
        </div>
        <div>
          <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#f97316] mr-2 shadow-[0_0_8px_rgba(249,115,22,0.5)]"></div>
            Debts
          </div>
          <div className="text-4xl font-extrabold text-white tracking-tight mb-3">{formatBalance(totals.debts)}</div>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <div className="text-center">
          <svg className="w-10 h-10 text-gray-700 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"></path>
          </svg>
          <p className="text-gray-600 text-sm">Historical net worth tracking coming soon.</p>
          <p className="text-gray-700 text-xs mt-1">Record balance snapshots to track your progress over time.</p>
        </div>
      </div>
    </div>
  );
};

export default NetWorth;
