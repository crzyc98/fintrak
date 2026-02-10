
import React, { useState, useEffect, useCallback } from 'react';
import { generateInsights, InsightResponse } from '../src/services/api';

type InsightMode = 'summary' | 'report';
type InsightPeriod = 'current_month' | 'last_month' | 'last_3_months';

const PERIOD_LABELS: Record<InsightPeriod, string> = {
  current_month: 'This Month',
  last_month: 'Last Month',
  last_3_months: 'Last 3 Months',
};

const COOLDOWN_SECONDS = 30;

const formatDollars = (cents: number): string => {
  return '$' + (cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 });
};

const SpendingInsights: React.FC = () => {
  const [mode, setMode] = useState<InsightMode>('summary');
  const [period, setPeriod] = useState<InsightPeriod>('current_month');
  const [data, setData] = useState<InsightResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleGenerate = useCallback(async () => {
    if (isLoading || cooldown > 0) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await generateInsights({
        period,
        type: mode,
      });
      setData(result);
      setCooldown(COOLDOWN_SECONDS);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate insights');
    } finally {
      setIsLoading(false);
    }
  }, [mode, period, isLoading, cooldown]);

  const handleModeChange = (newMode: InsightMode) => {
    if (newMode !== mode) {
      setMode(newMode);
      setData(null);
      setError(null);
    }
  };

  const handlePeriodChange = (newPeriod: InsightPeriod) => {
    if (newPeriod !== period) {
      setPeriod(newPeriod);
      setData(null);
      setError(null);
    }
  };

  // Initial state — no data yet
  if (!data && !isLoading && !error) {
    return (
      <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] overflow-hidden shadow-2xl shadow-black/40">
        <div className="flex justify-between items-start mb-6">
          <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Spending Insights</h2>
          <ModeToggle mode={mode} onChange={handleModeChange} />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center">
          <svg className="w-10 h-10 text-gray-700 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
          </svg>
          <p className="text-gray-400 text-sm mb-1">AI-powered spending analysis</p>
          <p className="text-gray-600 text-xs mb-4">Get a {mode === 'report' ? 'detailed report' : 'quick summary'} of your spending patterns</p>
          <div className="mb-5">
            <PeriodSelector period={period} onChange={handlePeriodChange} />
          </div>
          <button
            onClick={handleGenerate}
            className="px-6 py-2.5 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-sm font-semibold rounded-xl transition-colors shadow-[0_4px_12px_rgba(59,130,246,0.3)]"
          >
            Generate {mode === 'report' ? 'Report' : 'Insights'}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] overflow-hidden shadow-2xl shadow-black/40">
      <div className="flex justify-between items-start mb-2">
        <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Spending Insights</h2>
        <ModeToggle mode={mode} onChange={handleModeChange} />
      </div>
      <div className="mb-3">
        <PeriodSelector period={period} onChange={handlePeriodChange} />
      </div>

      {/* Loading state */}
      {isLoading && (
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-8 h-8 border-2 border-[#3b82f6]/30 border-t-[#3b82f6] rounded-full animate-spin mb-4"></div>
          <p className="text-gray-400 text-sm">Analyzing your spending...</p>
        </div>
      )}

      {/* Error state */}
      {!isLoading && error && (
        <div className="flex-1 flex flex-col items-center justify-center">
          <p className="text-red-400 text-sm mb-4">{error}</p>
          <button
            onClick={handleGenerate}
            disabled={cooldown > 0}
            className="text-sm font-semibold text-gray-400 hover:text-white transition-colors px-4 py-2 rounded-lg border border-white/10 hover:border-white/20 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {cooldown > 0 ? `Retry in ${cooldown}s` : 'Retry'}
          </button>
        </div>
      )}

      {/* Insufficient data state */}
      {!isLoading && !error && data?.insufficient_data && (
        <div className="flex-1 flex flex-col items-center justify-center">
          <svg className="w-10 h-10 text-gray-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <p className="text-gray-400 text-sm text-center px-4">{data.insufficient_data_message}</p>
        </div>
      )}

      {/* Success state */}
      {!isLoading && !error && data && !data.insufficient_data && (
        <div className="flex-1 overflow-y-auto pr-1 space-y-4 scrollbar-thin">
          {/* Summary */}
          {data.summary && (
            <p className="text-gray-300 text-sm leading-relaxed">{data.summary}</p>
          )}

          {/* Top Categories */}
          {data.top_categories.length > 0 && (
            <div>
              <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] mr-2 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
                Top Categories
              </div>
              <div className="space-y-1.5">
                {data.top_categories.map((cat) => (
                  <div key={cat.category_id} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400">
                      {cat.category_emoji && <span className="mr-1.5">{cat.category_emoji}</span>}
                      {cat.category_name}
                    </span>
                    <span className="flex items-center gap-2">
                      <span className="text-white font-medium">{formatDollars(cat.total_amount_cents)}</span>
                      {cat.change_percentage !== null && (
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          cat.change_percentage > 0
                            ? 'bg-[#ef4444]/15 text-[#ef4444]'
                            : 'bg-[#10b981]/15 text-[#10b981]'
                        }`}>
                          {cat.change_percentage > 0 ? '+' : ''}{cat.change_percentage}%
                        </span>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Anomalies */}
          {data.anomalies.length > 0 && (
            <div>
              <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#f97316] mr-2 shadow-[0_0_8px_rgba(249,115,22,0.5)]"></div>
                Unusual Activity
              </div>
              {data.anomaly_explanations && (
                <p className="text-gray-400 text-xs leading-relaxed mb-2">{data.anomaly_explanations}</p>
              )}
              <div className="space-y-1.5">
                {data.anomalies.map((a) => (
                  <div key={a.transaction_id} className="flex items-center justify-between text-sm">
                    <span className="text-gray-400 truncate mr-2">{a.description}</span>
                    <span className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-white font-medium">{formatDollars(a.amount_cents)}</span>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-[#f97316]/15 text-[#f97316]">
                        {a.deviation_factor}x avg
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {data.suggestions.length > 0 && (
            <div>
              <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
                <div className="w-1.5 h-1.5 rounded-full bg-[#10b981] mr-2 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                Suggestions
              </div>
              <ul className="space-y-1">
                {data.suggestions.map((s, i) => (
                  <li key={i} className="text-gray-400 text-xs leading-relaxed flex">
                    <span className="text-gray-600 mr-2">&bull;</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Regenerate button */}
      {!isLoading && data && (
        <div className="mt-3 pt-3 border-t border-white/5">
          <button
            onClick={handleGenerate}
            disabled={cooldown > 0}
            className="w-full text-center text-xs font-semibold text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {cooldown > 0 ? `Regenerate in ${cooldown}s` : 'Regenerate'}
          </button>
        </div>
      )}
    </div>
  );
};

const ModeToggle: React.FC<{ mode: InsightMode; onChange: (mode: InsightMode) => void }> = ({
  mode,
  onChange,
}) => (
  <div className="flex bg-[#111827] rounded-lg border border-white/5 p-0.5">
    <button
      onClick={() => onChange('summary')}
      className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all ${
        mode === 'summary'
          ? 'bg-[#3b82f6] text-white shadow-[0_2px_8px_rgba(59,130,246,0.3)]'
          : 'text-gray-500 hover:text-gray-300'
      }`}
    >
      Summary
    </button>
    <button
      onClick={() => onChange('report')}
      className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all ${
        mode === 'report'
          ? 'bg-[#3b82f6] text-white shadow-[0_2px_8px_rgba(59,130,246,0.3)]'
          : 'text-gray-500 hover:text-gray-300'
      }`}
    >
      Full Report
    </button>
  </div>
);

const PeriodSelector: React.FC<{ period: InsightPeriod; onChange: (p: InsightPeriod) => void }> = ({
  period,
  onChange,
}) => (
  <div className="flex bg-[#111827] rounded-lg border border-white/5 p-0.5 w-fit">
    {(Object.keys(PERIOD_LABELS) as InsightPeriod[]).map((p) => (
      <button
        key={p}
        onClick={() => onChange(p)}
        className={`px-3 py-1 rounded-md text-[10px] font-bold tracking-wider transition-all ${
          period === p
            ? 'bg-white/10 text-gray-200'
            : 'text-gray-500 hover:text-gray-300'
        }`}
      >
        {PERIOD_LABELS[p]}
      </button>
    ))}
  </div>
);

export default SpendingInsights;
