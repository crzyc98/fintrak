import React from 'react';
import { DateGroupedTransactions, TransactionData } from '../src/services/api';

interface ReviewTransactionListProps {
  groups: DateGroupedTransactions[];
  selectedIds: Set<string>;
  onToggleSelection: (id: string) => void;
  onToggleGroupSelection?: (date: string, transactionIds: string[]) => void;
  isLoading?: boolean;
  hasMore?: boolean;
  onLoadMore?: () => void;
  isLoadingMore?: boolean;
  emptyMessage?: string;
  showGroupCheckboxes?: boolean;
}

const ReviewTransactionList: React.FC<ReviewTransactionListProps> = ({
  groups,
  selectedIds,
  onToggleSelection,
  onToggleGroupSelection,
  isLoading = false,
  hasMore = false,
  onLoadMore,
  isLoadingMore = false,
  emptyMessage = "All caught up! No transactions to review.",
  showGroupCheckboxes = false,
}) => {
  const formatAmount = (amount: number): string => {
    const absAmount = Math.abs(amount / 100);
    return absAmount.toLocaleString('en-US', {
      style: 'currency',
      currency: 'USD',
    });
  };

  const getCategoryStyle = (categoryName: string | undefined): string => {
    if (!categoryName) return 'bg-gray-800/50 text-gray-400';

    const name = categoryName.toLowerCase();
    if (name.includes('restaurant') || name.includes('food') || name.includes('dining')) {
      return 'bg-orange-500/20 text-orange-400';
    }
    if (name.includes('grocery') || name.includes('groceries')) {
      return 'bg-green-500/20 text-green-400';
    }
    if (name.includes('subscription') || name.includes('streaming')) {
      return 'bg-pink-500/20 text-pink-400';
    }
    if (name.includes('transport') || name.includes('transit') || name.includes('uber') || name.includes('lyft')) {
      return 'bg-blue-500/20 text-blue-400';
    }
    if (name.includes('shopping') || name.includes('retail')) {
      return 'bg-purple-500/20 text-purple-400';
    }
    if (name.includes('utility') || name.includes('utilities')) {
      return 'bg-yellow-500/20 text-yellow-400';
    }
    return 'bg-gray-700/50 text-gray-300';
  };

  const isGroupFullySelected = (transactions: TransactionData[]): boolean => {
    return transactions.every(tx => selectedIds.has(tx.id));
  };

  const isGroupPartiallySelected = (transactions: TransactionData[]): boolean => {
    const selected = transactions.filter(tx => selectedIds.has(tx.id)).length;
    return selected > 0 && selected < transactions.length;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex items-center space-x-3 text-gray-400">
          <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <span className="text-sm">Loading transactions...</span>
        </div>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center mb-4">
          <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
          </svg>
        </div>
        <p className="text-gray-400 text-sm">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {groups.map((group) => (
        <div key={group.date}>
          <div className="flex items-center mb-5">
            {showGroupCheckboxes && onToggleGroupSelection && (
              <GroupCheckbox
                isChecked={isGroupFullySelected(group.transactions)}
                isIndeterminate={isGroupPartiallySelected(group.transactions)}
                onChange={() => onToggleGroupSelection(group.date, group.transactions.map(tx => tx.id))}
              />
            )}
            <h3 className="text-[10px] font-bold text-gray-600 uppercase tracking-widest">
              {group.date_label}
            </h3>
          </div>
          <div className="space-y-5">
            {group.transactions.map((tx) => (
              <TransactionRow
                key={tx.id}
                transaction={tx}
                isSelected={selectedIds.has(tx.id)}
                onToggle={() => onToggleSelection(tx.id)}
                formatAmount={formatAmount}
                getCategoryStyle={getCategoryStyle}
              />
            ))}
          </div>
        </div>
      ))}

      {hasMore && onLoadMore && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onLoadMore}
            disabled={isLoadingMore}
            className="px-6 py-2.5 bg-[#0a0f1d] border border-white/10 hover:border-white/20 text-gray-300 text-xs font-semibold rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoadingMore ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading...
              </span>
            ) : (
              'Load more'
            )}
          </button>
        </div>
      )}
    </div>
  );
};

interface GroupCheckboxProps {
  isChecked: boolean;
  isIndeterminate: boolean;
  onChange: () => void;
}

const GroupCheckbox: React.FC<GroupCheckboxProps> = ({ isChecked, isIndeterminate, onChange }) => {
  const checkboxRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    if (checkboxRef.current) {
      checkboxRef.current.indeterminate = isIndeterminate;
    }
  }, [isIndeterminate]);

  return (
    <label className="mr-3 cursor-pointer">
      <input
        ref={checkboxRef}
        type="checkbox"
        checked={isChecked}
        onChange={onChange}
        className="sr-only"
      />
      <div
        className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-all ${
          isChecked
            ? 'bg-[#3b82f6] border-[#3b82f6]'
            : isIndeterminate
            ? 'bg-[#3b82f6]/50 border-[#3b82f6]'
            : 'border-gray-700 hover:border-gray-500'
        }`}
      >
        {isChecked && (
          <svg className="w-2.5 h-2.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path>
          </svg>
        )}
        {isIndeterminate && !isChecked && (
          <div className="w-2 h-0.5 bg-white rounded"></div>
        )}
      </div>
    </label>
  );
};

interface TransactionRowProps {
  transaction: TransactionData;
  isSelected: boolean;
  onToggle: () => void;
  formatAmount: (amount: number) => string;
  getCategoryStyle: (category: string | undefined) => string;
}

const TransactionRow: React.FC<TransactionRowProps> = ({
  transaction,
  isSelected,
  onToggle,
  formatAmount,
  getCategoryStyle,
}) => {
  return (
    <div
      className="flex items-center group cursor-pointer"
      onClick={onToggle}
    >
      <div
        className={`w-5 h-5 rounded-full border-2 mr-5 flex items-center justify-center transition-all ${
          isSelected
            ? 'bg-[#3b82f6] border-[#3b82f6]'
            : 'border-gray-800 group-hover:border-gray-600'
        }`}
      >
        {isSelected && (
          <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path>
          </svg>
        )}
      </div>

      <div className="flex-1 flex items-center justify-between">
        <div className="flex items-center min-w-0">
          <span
            className={`text-[13px] font-semibold mr-3 transition-colors ${
              isSelected ? 'text-gray-600 line-through' : 'text-gray-300'
            }`}
          >
            {transaction.description}
          </span>
        </div>

        <div className="flex items-center space-x-6">
          {transaction.category_name ? (
            <span
              className={`px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest flex items-center ${
                isSelected ? 'opacity-30' : ''
              } ${getCategoryStyle(transaction.category_name)}`}
            >
              {transaction.category_emoji && (
                <span className="mr-1.5">{transaction.category_emoji}</span>
              )}
              {transaction.category_name}
            </span>
          ) : (
            <span
              className={`px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest ${
                isSelected ? 'opacity-30' : ''
              } bg-gray-800/50 text-gray-500`}
            >
              Uncategorized
            </span>
          )}
          <span
            className={`text-[13px] font-bold tabular-nums transition-colors ${
              isSelected ? 'text-gray-600' : transaction.amount < 0 ? 'text-white' : 'text-green-400'
            }`}
          >
            {transaction.amount < 0 ? '-' : '+'}
            {formatAmount(transaction.amount)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ReviewTransactionList;
