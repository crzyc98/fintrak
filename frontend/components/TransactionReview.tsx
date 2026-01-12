import React, { useState, useEffect, useCallback } from 'react';
import ReviewTransactionList from './ReviewTransactionList';
import {
  fetchReviewQueue,
  fetchReviewQueueCount,
  bulkUpdateTransactions,
  ReviewQueueResponse,
} from '../src/services/api';

interface TransactionReviewProps {
  onNavigateToReview?: () => void;
}

const TransactionReview: React.FC<TransactionReviewProps> = ({ onNavigateToReview }) => {
  const [queue, setQueue] = useState<ReviewQueueResponse | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isBulkLoading, setIsBulkLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [queueData, countData] = await Promise.all([
        fetchReviewQueue(5, 0),
        fetchReviewQueueCount(),
      ]);
      setQueue(queueData);
      setTotalCount(countData.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load review queue');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

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

  const handleBulkReview = async () => {
    if (selectedIds.size === 0) return;

    try {
      setIsBulkLoading(true);
      setError(null);
      await bulkUpdateTransactions({
        transaction_ids: Array.from(selectedIds),
        operation: 'mark_reviewed',
      });
      setSelectedIds(new Set());
      await loadQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to mark as reviewed');
    } finally {
      setIsBulkLoading(false);
    }
  };

  const handleViewAll = () => {
    if (onNavigateToReview) {
      onNavigateToReview();
    }
  };

  if (error && !queue) {
    return (
      <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 flex flex-col h-full">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-sm font-semibold text-gray-400">Transactions to review</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-sm mb-4">{error}</p>
            <button
              onClick={loadQueue}
              className="text-blue-400 hover:text-blue-300 text-sm font-medium"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 flex flex-col h-full relative">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-sm font-semibold text-gray-400">
          Transactions to review
          {totalCount > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-blue-500/20 text-blue-400 text-xs font-bold rounded-full">
              {totalCount}
            </span>
          )}
        </h2>
        {totalCount > 5 && (
          <button
            onClick={handleViewAll}
            className="text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center"
          >
            View all
            <svg
              className="w-3.5 h-3.5 ml-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2.5"
                d="M9 5l7 7-7 7"
              ></path>
            </svg>
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar pb-24">
        <ReviewTransactionList
          groups={queue?.groups || []}
          selectedIds={selectedIds}
          onToggleSelection={toggleSelection}
          isLoading={isLoading}
          emptyMessage="All caught up! No transactions to review."
        />
      </div>

      {queue && queue.groups.length > 0 && (
        <div className="absolute bottom-6 left-6 right-6">
          <button
            onClick={handleBulkReview}
            disabled={selectedIds.size === 0 || isBulkLoading}
            className={`w-full border text-white text-[11px] font-bold uppercase tracking-wider py-3.5 rounded-xl transition-all flex items-center justify-center shadow-xl shadow-black/40 ${
              selectedIds.size > 0 && !isBulkLoading
                ? 'bg-[#3b82f6] border-[#3b82f6] hover:bg-[#2563eb]'
                : 'bg-[#0a0f1d] border-white/10 opacity-50 cursor-not-allowed'
            }`}
          >
            {isBulkLoading ? (
              <svg
                className="animate-spin h-4 w-4 mr-2"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            ) : (
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2.5"
                  d="M5 13l4 4L19 7"
                ></path>
              </svg>
            )}
            {selectedIds.size > 0
              ? `Mark ${selectedIds.size} as reviewed`
              : 'Select transactions to review'}
          </button>
        </div>
      )}

      {error && queue && (
        <div className="absolute bottom-20 left-6 right-6">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2 text-red-400 text-xs">
            {error}
          </div>
        </div>
      )}
    </div>
  );
};

export default TransactionReview;
