import React, { useState, useEffect, useMemo } from 'react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';
import { Account, AccountType, ACCOUNT_TYPES } from '../types';
import {
  fetchAccounts,
  createAccount,
  updateAccount,
  deleteAccount,
  previewCsv,
  parseCsv,
  createTransactionsFromCsv,
  updateAccountMapping,
  createBalanceSnapshot,
  CsvPreviewResponse,
  CsvParseResponse,
  CsvColumnMapping,
  ParsedTransaction,
} from '../src/services/api';
import AccountForm from './forms/AccountForm';
import CsvDropZone from './CsvDropZone';
import CsvColumnMapper from './CsvColumnMapper';
import CsvImportPreview from './CsvImportPreview';

interface AccountsViewProps {
  triggerNewAccount?: boolean;
  onNewAccountHandled?: () => void;
}

const AccountsView: React.FC<AccountsViewProps> = ({
  triggerNewAccount,
  onNewAccountHandled,
}) => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingAccount, setEditingAccount] = useState<Account | undefined>(undefined);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [showBalanceForm, setShowBalanceForm] = useState(false);
  const [balanceAmount, setBalanceAmount] = useState('');
  const [balanceDate, setBalanceDate] = useState(new Date().toISOString().split('T')[0]);
  const [balanceError, setBalanceError] = useState<string | null>(null);
  const [balanceSuccess, setBalanceSuccess] = useState<string | null>(null);

  // CSV Import state
  const [csvFileContent, setCsvFileContent] = useState<string | null>(null);
  const [csvFileName, setCsvFileName] = useState<string | null>(null);
  const [csvPreview, setCsvPreview] = useState<CsvPreviewResponse | null>(null);
  const [csvParseResult, setCsvParseResult] = useState<CsvParseResponse | null>(null);
  const [csvMapping, setCsvMapping] = useState<CsvColumnMapping | null>(null);
  const [showColumnMapper, setShowColumnMapper] = useState(false);
  const [showImportPreview, setShowImportPreview] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importError, setImportError] = useState<string | null>(null);
  const [importSuccess, setImportSuccess] = useState<string | null>(null);

  useEffect(() => {
    loadAccounts();
  }, []);

  useEffect(() => {
    if (triggerNewAccount) {
      setEditingAccount(undefined);
      setShowForm(true);
      onNewAccountHandled?.();
    }
  }, [triggerNewAccount, onNewAccountHandled]);

  const loadAccounts = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchAccounts();
      setAccounts(data);
      if (data.length > 0 && !selectedAccountId) {
        setSelectedAccountId(data[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load accounts');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedAccount = useMemo(
    () => accounts.find((a) => a.id === selectedAccountId),
    [accounts, selectedAccountId]
  );

  const accountGroups = useMemo(() => {
    const groups: Record<AccountType, Account[]> = {} as Record<AccountType, Account[]>;
    ACCOUNT_TYPES.forEach((type) => {
      groups[type] = accounts
        .filter((a) => a.type === type)
        .sort((a, b) => a.name.localeCompare(b.name));
    });
    return groups;
  }, [accounts]);

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

  const handleCreateAccount = async (data: { name: string; type: AccountType; institution?: string }) => {
    await createAccount(data);
    await loadAccounts();
    setShowForm(false);
  };

  const handleUpdateAccount = async (data: { name: string; type: AccountType; institution?: string }) => {
    if (!editingAccount) return;
    await updateAccount(editingAccount.id, data);
    await loadAccounts();
    setEditingAccount(undefined);
    setShowForm(false);
  };

  const handleDeleteAccount = async (id: string) => {
    try {
      await deleteAccount(id);
      await loadAccounts();
      if (selectedAccountId === id) {
        setSelectedAccountId(accounts.length > 1 ? accounts[0].id : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete account');
    }
    setDeleteConfirm(null);
  };

  const formatBalance = (cents: number | null): string => {
    if (cents === null) return '--';
    return `$${(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  };

  // CSV Import handlers
  const resetImportState = () => {
    setCsvFileContent(null);
    setCsvFileName(null);
    setCsvPreview(null);
    setCsvParseResult(null);
    setCsvMapping(null);
    setShowColumnMapper(false);
    setShowImportPreview(false);
    setIsImporting(false);
    setImportError(null);
  };

  const handleCsvFileSelect = async (fileContent: string, fileName: string) => {
    if (!selectedAccount) return;

    setImportError(null);
    setImportSuccess(null);
    setCsvFileContent(fileContent);
    setCsvFileName(fileName);

    try {
      // Preview the CSV to get headers and sample data
      const preview = await previewCsv(fileContent);
      setCsvPreview(preview);

      // Check if account has saved mapping
      if (selectedAccount.csv_column_mapping) {
        // Use saved mapping - skip column mapper and go directly to parse
        const mapping = selectedAccount.csv_column_mapping;
        setCsvMapping(mapping);
        const parseResult = await parseCsv(selectedAccount.id, fileContent, mapping);
        setCsvParseResult(parseResult);
        setShowImportPreview(true);
      } else {
        // No saved mapping - show column mapper
        setShowColumnMapper(true);
      }
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to preview CSV');
      resetImportState();
    }
  };

  const handleColumnMappingConfirm = async (mapping: CsvColumnMapping) => {
    if (!selectedAccount || !csvFileContent) return;

    setImportError(null);
    setCsvMapping(mapping);
    setShowColumnMapper(false);

    try {
      const parseResult = await parseCsv(selectedAccount.id, csvFileContent, mapping);
      setCsvParseResult(parseResult);
      setShowImportPreview(true);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to parse CSV');
      resetImportState();
    }
  };

  const handleImportConfirm = async (selectedTransactions: ParsedTransaction[]) => {
    if (!selectedAccount || !csvMapping) return;

    setIsImporting(true);
    setImportError(null);

    try {
      const result = await createTransactionsFromCsv(
        selectedAccount.id,
        selectedTransactions,
        csvMapping,
        true // save mapping to account
      );

      // Reload accounts to get updated mapping
      await loadAccounts();

      setImportSuccess(`Successfully imported ${result.created_count} transaction${result.created_count !== 1 ? 's' : ''}`);
      resetImportState();

      // Clear success message after 5 seconds
      setTimeout(() => setImportSuccess(null), 5000);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to import transactions');
      setIsImporting(false);
    }
  };

  const handleReconfigureMapping = () => {
    if (!selectedAccount) return;
    // Start the reconfigure flow with saved mapping as initial values
    setShowColumnMapper(true);
  };

  const handleReconfigureMappingConfirm = async (mapping: CsvColumnMapping) => {
    if (!selectedAccount) return;

    setImportError(null);

    try {
      await updateAccountMapping(selectedAccount.id, mapping);
      await loadAccounts();
      setShowColumnMapper(false);
      setImportSuccess('Column mapping updated successfully');
      setTimeout(() => setImportSuccess(null), 3000);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to update mapping');
    }
  };

  const handleRecordBalance = async () => {
    if (!selectedAccount) return;

    const amount = parseFloat(balanceAmount);
    if (isNaN(amount)) {
      setBalanceError('Please enter a valid amount');
      return;
    }

    setBalanceError(null);

    try {
      await createBalanceSnapshot(selectedAccount.id, {
        balance: amount,
        snapshot_date: balanceDate,
      });
      await loadAccounts();
      setShowBalanceForm(false);
      setBalanceAmount('');
      setBalanceDate(new Date().toISOString().split('T')[0]);
      setBalanceSuccess('Balance recorded successfully');
      setTimeout(() => setBalanceSuccess(null), 3000);
    } catch (err) {
      setBalanceError(err instanceof Error ? err.message : 'Failed to record balance');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050910]">
        <div className="text-gray-500">Loading accounts...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Center Pane: Account List */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <h1 className="text-sm font-bold text-gray-300">Accounts</h1>
          <div className="flex space-x-4">
            <button
              onClick={() => {
                setEditingAccount(undefined);
                setShowForm(true);
              }}
              className="text-gray-500 hover:text-white"
              title="Add Account"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
              {error}
              <button onClick={() => setError(null)} className="ml-4 text-red-300 hover:text-white">
                Dismiss
              </button>
            </div>
          )}

          {/* Top Summary */}
          <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-10 relative overflow-hidden shadow-2xl">
            <div className="flex space-x-12 mb-4 relative z-10">
              <div>
                <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mr-2" /> Assets
                </div>
                <div className="text-3xl font-black text-white">{formatBalance(totals.assets)}</div>
              </div>
              <div>
                <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-orange-500 mr-2" /> Debts
                </div>
                <div className="text-3xl font-black text-white">{formatBalance(totals.debts)}</div>
              </div>
              <div>
                <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-green-500 mr-2" /> Net Worth
                </div>
                <div className="text-3xl font-black text-white">{formatBalance(totals.netWorth)}</div>
              </div>
            </div>
          </div>

          {/* Account Lists by Type */}
          {accounts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No accounts yet</p>
              <button
                onClick={() => {
                  setEditingAccount(undefined);
                  setShowForm(true);
                }}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-bold rounded-xl transition-colors"
              >
                Create Your First Account
              </button>
            </div>
          ) : (
            ACCOUNT_TYPES.map((type) => {
              const typeAccounts = accountGroups[type];
              if (typeAccounts.length === 0) return null;

              return (
                <div key={type} className="mb-10">
                  <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-6">
                    <svg className="w-3 h-3 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" />
                    </svg>
                    {type}
                  </h2>
                  <div className="space-y-1">
                    {typeAccounts.map((account) => (
                      <div
                        key={account.id}
                        onClick={() => setSelectedAccountId(account.id)}
                        className={`flex items-center px-4 py-4 rounded-xl cursor-pointer transition-all ${
                          selectedAccountId === account.id
                            ? 'bg-blue-500/10 ring-1 ring-blue-500/20'
                            : 'hover:bg-white/5'
                        }`}
                      >
                        <div className="w-10 h-10 rounded-full bg-gray-800 flex items-center justify-center text-white font-bold text-xs mr-4 shrink-0">
                          {account.name.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0 pr-4">
                          <div className="flex items-center">
                            <span className="text-sm font-bold text-white truncate mr-2">
                              {account.name}
                            </span>
                          </div>
                          {account.institution && (
                            <span className="text-[11px] font-semibold text-gray-500">
                              {account.institution}
                            </span>
                          )}
                        </div>
                        <div className="text-sm font-bold text-white tabular-nums">
                          {formatBalance(account.current_balance)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Pane: Account Details */}
      <div className="w-[450px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar border-l border-white/5">
        {selectedAccount ? (
          <div className="p-8">
            <div className="flex justify-between items-center mb-10">
              <h3 className="text-sm font-bold text-white">Account Details</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setEditingAccount(selectedAccount);
                    setShowForm(true);
                  }}
                  className="p-2 hover:bg-white/5 rounded-lg text-gray-500 hover:text-white"
                  title="Edit"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="2"
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                </button>
                <button
                  onClick={() => setDeleteConfirm(selectedAccount.id)}
                  className="p-2 hover:bg-red-500/10 rounded-lg text-gray-500 hover:text-red-400"
                  title="Delete"
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
              </div>
            </div>

            <div className="mb-8">
              <div className="flex items-center mb-2">
                <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center text-blue-400 font-bold text-sm mr-3">
                  {selectedAccount.name.charAt(0)}
                </div>
                <span className="text-xs font-bold text-gray-500 uppercase">{selectedAccount.type}</span>
              </div>
              <h2 className="text-3xl font-black text-white tracking-tight mb-2">
                {selectedAccount.name}
              </h2>
              {selectedAccount.institution && (
                <p className="text-sm text-gray-500">{selectedAccount.institution}</p>
              )}
              <div className="mt-4">
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
                  Current Balance
                </div>
                <div className="text-3xl font-black text-white tabular-nums tracking-tighter">
                  {formatBalance(selectedAccount.current_balance)}
                </div>
                {selectedAccount.current_balance === null && (
                  <p className="text-xs text-gray-500 mt-1">No balance recorded yet</p>
                )}
                <button
                  onClick={() => setShowBalanceForm(true)}
                  className="mt-3 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Record Balance
                </button>
                {balanceSuccess && (
                  <div className="mt-2 text-xs text-green-400">{balanceSuccess}</div>
                )}
              </div>
            </div>

            <div className="space-y-4 text-sm">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Account Type</span>
                <span className="text-white font-medium">{selectedAccount.type}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Asset/Liability</span>
                <span className={`font-medium ${selectedAccount.is_asset ? 'text-green-400' : 'text-orange-400'}`}>
                  {selectedAccount.is_asset ? 'Asset' : 'Liability'}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Created</span>
                <span className="text-white font-medium">
                  {new Date(selectedAccount.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            {/* CSV Import Section */}
            <div className="mt-8 pt-8 border-t border-white/5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-white">Import Transactions</h3>
                {selectedAccount.csv_column_mapping && (
                  <button
                    onClick={handleReconfigureMapping}
                    className="text-xs text-gray-500 hover:text-blue-400 transition-colors"
                  >
                    Re-configure mapping
                  </button>
                )}
              </div>

              {/* Success message */}
              {importSuccess && (
                <div className="mb-4 p-3 bg-green-500/10 border border-green-500/20 rounded-xl text-green-400 text-sm flex items-center">
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                  </svg>
                  {importSuccess}
                </div>
              )}

              {/* Error message */}
              {importError && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                  {importError}
                  <button
                    onClick={() => setImportError(null)}
                    className="ml-2 text-red-300 hover:text-white"
                  >
                    Dismiss
                  </button>
                </div>
              )}

              {/* Saved mapping indicator */}
              {selectedAccount.csv_column_mapping && (
                <div className="mb-4 p-3 bg-blue-500/5 border border-blue-500/10 rounded-xl">
                  <div className="flex items-center text-xs text-blue-400">
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Column mapping saved - drop CSV to import quickly
                  </div>
                </div>
              )}

              <CsvDropZone
                onFileSelect={handleCsvFileSelect}
                disabled={isImporting}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">
            Select an account to view details
          </div>
        )}
      </div>

      {/* Account Form Modal */}
      {showForm && (
        <AccountForm
          account={editingAccount}
          onSubmit={editingAccount ? handleUpdateAccount : handleCreateAccount}
          onCancel={() => {
            setShowForm(false);
            setEditingAccount(undefined);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Delete Account?</h2>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete this account? This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-3 text-sm font-bold text-gray-400 hover:text-white border border-white/10 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteAccount(deleteConfirm)}
                className="flex-1 px-4 py-3 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CSV Column Mapper Modal */}
      {showColumnMapper && csvPreview && (
        <CsvColumnMapper
          preview={csvPreview}
          initialMapping={csvFileContent ? null : selectedAccount?.csv_column_mapping}
          onConfirm={csvFileContent ? handleColumnMappingConfirm : handleReconfigureMappingConfirm}
          onCancel={() => {
            setShowColumnMapper(false);
            if (csvFileContent) {
              resetImportState();
            }
          }}
        />
      )}

      {/* CSV Import Preview Modal */}
      {showImportPreview && csvParseResult && (
        <CsvImportPreview
          parseResult={csvParseResult}
          onConfirm={handleImportConfirm}
          onCancel={() => {
            setShowImportPreview(false);
            resetImportState();
          }}
          isLoading={isImporting}
        />
      )}

      {/* Balance Recording Modal */}
      {showBalanceForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-2">Record Balance</h2>
            <p className="text-gray-500 text-sm mb-6">
              Enter the account balance as of a specific date. The system will compute the current balance by adding transactions after this date.
            </p>

            {balanceError && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                {balanceError}
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">
                  Balance Amount ($)
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={balanceAmount}
                  onChange={(e) => setBalanceAmount(e.target.value)}
                  placeholder="0.00"
                  className="w-full px-4 py-3 bg-[#050910] border border-white/10 rounded-xl text-white placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">
                  As of Date
                </label>
                <input
                  type="date"
                  value={balanceDate}
                  onChange={(e) => setBalanceDate(e.target.value)}
                  className="w-full px-4 py-3 bg-[#050910] border border-white/10 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                />
              </div>
            </div>

            <div className="flex space-x-4 mt-6">
              <button
                onClick={() => {
                  setShowBalanceForm(false);
                  setBalanceError(null);
                  setBalanceAmount('');
                  setBalanceDate(new Date().toISOString().split('T')[0]);
                }}
                className="flex-1 px-4 py-3 text-sm font-bold text-gray-400 hover:text-white border border-white/10 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRecordBalance}
                className="flex-1 px-4 py-3 text-sm font-bold text-white bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors"
              >
                Save Balance
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountsView;
