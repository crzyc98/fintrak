import React, { useState, useEffect, useCallback } from 'react';
import ReviewTransactionList from './ReviewTransactionList';
import ReviewActionBar from './ReviewActionBar';
import {
  fetchReviewQueue,
  fetchReviewQueueCount,
  fetchCategories,
  bulkUpdateTransactions,
  triggerCategorization,
  ReviewQueueResponse,
  CategoryData,
} from '../src/services/api';

interface ReviewPageProps {
  onNavigateToDashboard?: () => void;
}

const ReviewPage: React.FC<ReviewPageProps> = ({ onNavigateToDashboard }) => {
  const [queue, setQueue] = useState<ReviewQueueResponse | null>(null);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [isBulkLoading, setIsBulkLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const [isCategorizingAI, setIsCategorizingAI] = useState(false);
  const [aiResult, setAiResult] = useState<string | null>(null);
  const LIMIT = 50;

  const loadQueue = useCallback(async (loadMore = false) => {
    try {
      if (loadMore) {
        setIsLoadingMore(true);
      } else {
        setIsLoading(true);
        setOffset(0);
      }
      setError(null);

      const currentOffset = loadMore ? offset : 0;
      const [queueData, countData] = await Promise.all([
        fetchReviewQueue(LIMIT, currentOffset),
        fetchReviewQueueCount(),
      ]);

      if (loadMore && queue) {
        // Merge new groups with existing
        const existingGroups = queue.groups;
        const newGroups = queueData.groups;

        // Merge transactions for same dates
        const mergedGroupsMap = new Map<string, typeof queueData.groups[0]>();
        for (const group of existingGroups) {
          mergedGroupsMap.set(group.date, group);
        }
        for (const group of newGroups) {
          const existing = mergedGroupsMap.get(group.date);
          if (existing) {
            mergedGroupsMap.set(group.date, {
              ...existing,
              transactions: [...existing.transactions, ...group.transactions],
            });
          } else {
            mergedGroupsMap.set(group.date, group);
          }
        }

        // Sort by date descending
        const mergedGroups = Array.from(mergedGroupsMap.values()).sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );

        setQueue({
          ...queueData,
          groups: mergedGroups,
          displayed_count: queue.displayed_count + queueData.displayed_count,
        });
        setOffset(currentOffset + LIMIT);
      } else {
        setQueue(queueData);
        setOffset(LIMIT);
      }

      setTotalCount(countData.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load review queue');
    } finally {
      setIsLoading(false);
      setIsLoadingMore(false);
    }
  }, [offset, queue]);

  const loadCategories = useCallback(async () => {
    try {
      const data = await fetchCategories();
      setCategories(data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  }, []);

  useEffect(() => {
    loadQueue();
    loadCategories();
  }, []);

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

  const toggleGroupSelection = (date: string, transactionIds: string[]) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      const allSelected = transactionIds.every((id) => prev.has(id));

      if (allSelected) {
        // Deselect all in group
        transactionIds.forEach((id) => next.delete(id));
      } else {
        // Select all in group
        transactionIds.forEach((id) => next.add(id));
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

  const handleSetCategory = async (categoryId: string) => {
    if (selectedIds.size === 0) return;

    try {
      setIsBulkLoading(true);
      setError(null);
      await bulkUpdateTransactions({
        transaction_ids: Array.from(selectedIds),
        operation: 'set_category',
        category_id: categoryId,
      });
      // Keep selection for chained actions
      await loadQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to set category');
    } finally {
      setIsBulkLoading(false);
    }
  };

  const handleAddNote = async (note: string) => {
    if (selectedIds.size === 0) return;

    try {
      setIsBulkLoading(true);
      setError(null);
      await bulkUpdateTransactions({
        transaction_ids: Array.from(selectedIds),
        operation: 'add_note',
        note,
      });
      // Keep selection for chained actions
      await loadQueue();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add note');
    } finally {
      setIsBulkLoading(false);
    }
  };

  const handleLoadMore = () => {
    loadQueue(true);
  };

  const handleAICategorize = async () => {
    try {
      setIsCategorizingAI(true);
      setError(null);
      setAiResult(null);

      const result = await triggerCategorization();

      if (result.success_count > 0) {
        setAiResult(
          `Classified ${result.success_count} transaction${result.success_count !== 1 ? 's' : ''} ` +
          `(${result.rule_match_count} by rules, ${result.ai_match_count} by AI)`
        );
        // Reload the queue and categories to reflect changes (AI may create new categories)
        await loadQueue();
        await loadCategories();
      } else if (result.transaction_count === 0) {
        setAiResult('No uncategorized transactions to process');
      } else {
        setAiResult(`Could not categorize transactions. ${result.error_message || ''}`);
      }

      // Clear result message after 5 seconds
      setTimeout(() => setAiResult(null), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run AI categorization');
    } finally {
      setIsCategorizingAI(false);
    }
  };

  // Show success state when all done
  if (!isLoading && queue && queue.groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <div className="w-24 h-24 rounded-full bg-green-500/10 flex items-center justify-center mb-6">
          <svg
            className="w-12 h-12 text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M5 13l4 4L19 7"
            ></path>
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-white mb-3">All caught up!</h2>
        <p className="text-gray-400 mb-6">
          You've reviewed all your transactions. Great job!
        </p>
        {onNavigateToDashboard && (
          <button
            onClick={onNavigateToDashboard}
            className="px-6 py-3 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-sm font-bold rounded-xl transition-all"
          >
            Back to Dashboard
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-xl font-bold text-white mb-1">Review Transactions</h1>
          <p className="text-sm text-gray-400">
            {totalCount} transaction{totalCount !== 1 ? 's' : ''} pending review
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleAICategorize}
            disabled={isCategorizingAI || totalCount === 0}
            className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-300 text-sm font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
          >
            {isCategorizingAI ? (
              <>
                <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Categorizing...
              </>
            ) : (
              <>
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                Auto-categorize
              </>
            )}
          </button>
          {onNavigateToDashboard && (
            <button
              onClick={onNavigateToDashboard}
              className="text-sm text-gray-400 hover:text-white transition-colors flex items-center"
            >
              <svg
                className="w-4 h-4 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M10 19l-7-7m0 0l7-7m-7 7h18"
                ></path>
              </svg>
              Back to Dashboard
            </button>
          )}
        </div>
      </div>

      {/* AI Result Message */}
      {aiResult && (
        <div className="mb-4 p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl text-purple-300 text-sm flex items-center">
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
          {aiResult}
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 overflow-hidden flex flex-col">
        {error && !queue && (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-red-400 text-sm mb-4">{error}</p>
              <button
                onClick={() => loadQueue()}
                className="text-blue-400 hover:text-blue-300 text-sm font-medium"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar pb-4">
          <ReviewTransactionList
            groups={queue?.groups || []}
            selectedIds={selectedIds}
            onToggleSelection={toggleSelection}
            onToggleGroupSelection={toggleGroupSelection}
            isLoading={isLoading}
            hasMore={queue?.has_more || false}
            onLoadMore={handleLoadMore}
            isLoadingMore={isLoadingMore}
            showGroupCheckboxes={true}
          />
        </div>
      </div>

      {/* Fixed Action Bar at bottom */}
      {selectedIds.size > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
          <ReviewActionBar
            selectedCount={selectedIds.size}
            onMarkReviewed={handleBulkReview}
            onSetCategory={handleSetCategory}
            onAddNote={handleAddNote}
            categories={categories}
            isLoading={isBulkLoading}
            error={error}
          />
        </div>
      )}
    </div>
  );
};

export default ReviewPage;
