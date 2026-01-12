import React, { useState, useMemo } from 'react';
import { CsvParseResponse, ParsedTransaction } from '../src/services/api';

interface CsvImportPreviewProps {
  parseResult: CsvParseResponse;
  onConfirm: (selectedTransactions: ParsedTransaction[]) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const CsvImportPreview: React.FC<CsvImportPreviewProps> = ({
  parseResult,
  onConfirm,
  onCancel,
  isLoading = false,
}) => {
  // Track which warning transactions to include (all included by default)
  const [excludedWarnings, setExcludedWarnings] = useState<Set<number>>(new Set());

  const formatAmount = (cents: number): string => {
    const isNegative = cents < 0;
    const amount = Math.abs(cents) / 100;
    return `${isNegative ? '-' : ''}$${amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  };

  const formatDate = (dateStr: string): string => {
    try {
      return new Date(dateStr).toLocaleDateString();
    } catch {
      return dateStr;
    }
  };

  const toggleWarning = (rowNumber: number) => {
    setExcludedWarnings((prev) => {
      const next = new Set(prev);
      if (next.has(rowNumber)) {
        next.delete(rowNumber);
      } else {
        next.add(rowNumber);
      }
      return next;
    });
  };

  const validTransactions = useMemo(() =>
    parseResult.transactions.filter(t => t.status === 'valid'),
    [parseResult.transactions]
  );

  const warningTransactions = useMemo(() =>
    parseResult.transactions.filter(t => t.status === 'warning'),
    [parseResult.transactions]
  );

  const errorTransactions = useMemo(() =>
    parseResult.transactions.filter(t => t.status === 'error'),
    [parseResult.transactions]
  );

  const selectedTransactions = useMemo(() => {
    const valid = validTransactions;
    const includedWarnings = warningTransactions.filter(t => !excludedWarnings.has(t.row_number));
    return [...valid, ...includedWarnings];
  }, [validTransactions, warningTransactions, excludedWarnings]);

  const handleConfirm = () => {
    onConfirm(selectedTransactions);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-bold text-white">Import Preview</h2>
          <p className="text-sm text-gray-500 mt-1">
            Review transactions before importing
          </p>
        </div>

        {/* Stats Bar */}
        <div className="px-6 py-3 bg-gray-900/50 border-b border-white/10 flex space-x-6">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-sm text-gray-400">
              <span className="font-medium text-white">{parseResult.valid_count}</span> valid
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500" />
            <span className="text-sm text-gray-400">
              <span className="font-medium text-white">{parseResult.warning_count}</span> warnings
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-sm text-gray-400">
              <span className="font-medium text-white">{parseResult.error_count}</span> errors
            </span>
          </div>
          <div className="flex-1" />
          <div className="text-sm text-gray-400">
            <span className="font-medium text-blue-400">{selectedTransactions.length}</span> will be imported
          </div>
        </div>

        {/* Transaction List */}
        <div className="flex-1 overflow-y-auto">
          {/* Valid Transactions */}
          {validTransactions.length > 0 && (
            <div className="p-4">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3">
                Valid Transactions ({validTransactions.length})
              </h3>
              <div className="space-y-1">
                {validTransactions.slice(0, 50).map((tx) => (
                  <div
                    key={tx.row_number}
                    className="flex items-center px-3 py-2 rounded-lg bg-green-500/5 border border-green-500/10"
                  >
                    <div className="w-2 h-2 rounded-full bg-green-500 mr-3" />
                    <span className="text-xs text-gray-500 w-12">#{tx.row_number}</span>
                    <span className="text-sm text-gray-400 w-24">{formatDate(tx.date)}</span>
                    <span className="text-sm text-white flex-1 truncate">{tx.description}</span>
                    <span className={`text-sm font-medium tabular-nums ${
                      tx.amount < 0 ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {formatAmount(tx.amount)}
                    </span>
                  </div>
                ))}
                {validTransactions.length > 50 && (
                  <div className="text-center py-2 text-sm text-gray-500">
                    ... and {validTransactions.length - 50} more
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Warning Transactions (Duplicates) */}
          {warningTransactions.length > 0 && (
            <div className="p-4 border-t border-white/5">
              <h3 className="text-xs font-bold text-yellow-500 uppercase tracking-wider mb-2">
                Potential Duplicates ({warningTransactions.length})
              </h3>
              <p className="text-xs text-gray-500 mb-3">
                These transactions match existing records. Uncheck to exclude from import.
              </p>
              <div className="space-y-1">
                {warningTransactions.map((tx) => (
                  <div
                    key={tx.row_number}
                    className={`flex items-center px-3 py-2 rounded-lg border transition-all cursor-pointer ${
                      excludedWarnings.has(tx.row_number)
                        ? 'bg-gray-900/50 border-gray-700 opacity-50'
                        : 'bg-yellow-500/5 border-yellow-500/10'
                    }`}
                    onClick={() => toggleWarning(tx.row_number)}
                  >
                    <input
                      type="checkbox"
                      checked={!excludedWarnings.has(tx.row_number)}
                      onChange={() => toggleWarning(tx.row_number)}
                      onClick={(e) => e.stopPropagation()}
                      className="mr-3 rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500"
                    />
                    <div className="w-2 h-2 rounded-full bg-yellow-500 mr-3" />
                    <span className="text-xs text-gray-500 w-12">#{tx.row_number}</span>
                    <span className="text-sm text-gray-400 w-24">{formatDate(tx.date)}</span>
                    <span className="text-sm text-white flex-1 truncate">{tx.description}</span>
                    <span className={`text-sm font-medium tabular-nums ${
                      tx.amount < 0 ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {formatAmount(tx.amount)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Transactions */}
          {errorTransactions.length > 0 && (
            <div className="p-4 border-t border-white/5">
              <h3 className="text-xs font-bold text-red-500 uppercase tracking-wider mb-2">
                Errors ({errorTransactions.length})
              </h3>
              <p className="text-xs text-gray-500 mb-3">
                These rows could not be parsed and will be skipped.
              </p>
              <div className="space-y-1">
                {errorTransactions.slice(0, 20).map((tx) => (
                  <div
                    key={tx.row_number}
                    className="flex items-center px-3 py-2 rounded-lg bg-red-500/5 border border-red-500/10"
                  >
                    <div className="w-2 h-2 rounded-full bg-red-500 mr-3" />
                    <span className="text-xs text-gray-500 w-12">#{tx.row_number}</span>
                    <span className="text-sm text-red-400 flex-1">{tx.status_reason}</span>
                  </div>
                ))}
                {errorTransactions.length > 20 && (
                  <div className="text-center py-2 text-sm text-gray-500">
                    ... and {errorTransactions.length - 20} more errors
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {selectedTransactions.length} transaction{selectedTransactions.length !== 1 ? 's' : ''} will be imported
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white border border-white/10 rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={isLoading || selectedTransactions.length === 0}
              className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
                selectedTransactions.length > 0 && !isLoading
                  ? 'bg-blue-500 hover:bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Importing...
                </span>
              ) : (
                `Import ${selectedTransactions.length} Transaction${selectedTransactions.length !== 1 ? 's' : ''}`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CsvImportPreview;
