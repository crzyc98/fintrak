import React, { useState, useEffect, useMemo } from 'react';
import { CsvColumnMapping, AmountMode, CsvPreviewResponse } from '../src/services/api';

interface CsvColumnMapperProps {
  preview: CsvPreviewResponse;
  initialMapping?: CsvColumnMapping | null;
  onConfirm: (mapping: CsvColumnMapping) => void;
  onCancel: () => void;
}

const DATE_FORMATS = [
  { value: 'YYYY-MM-DD', label: 'YYYY-MM-DD (2024-01-15)' },
  { value: 'MM/DD/YYYY', label: 'MM/DD/YYYY (01/15/2024)' },
  { value: 'DD/MM/YYYY', label: 'DD/MM/YYYY (15/01/2024)' },
  { value: 'MM-DD-YYYY', label: 'MM-DD-YYYY (01-15-2024)' },
  { value: 'DD-MM-YYYY', label: 'DD-MM-YYYY (15-01-2024)' },
  { value: 'M/D/YYYY', label: 'M/D/YYYY (1/15/2024)' },
  { value: 'D/M/YYYY', label: 'D/M/YYYY (15/1/2024)' },
];

// Common column name patterns for auto-detection
const DATE_PATTERNS = ['date', 'transaction date', 'trans date', 'posted date', 'post date'];
const DESCRIPTION_PATTERNS = ['description', 'memo', 'narrative', 'details', 'transaction', 'payee'];
const AMOUNT_PATTERNS = ['amount', 'sum', 'value', 'total'];
const DEBIT_PATTERNS = ['debit', 'withdrawal', 'out', 'expense'];
const CREDIT_PATTERNS = ['credit', 'deposit', 'in', 'income'];
const CATEGORY_PATTERNS = ['category', 'type', 'classification', 'group', 'class'];

const CsvColumnMapper: React.FC<CsvColumnMapperProps> = ({
  preview,
  initialMapping,
  onConfirm,
  onCancel,
}) => {
  const [dateColumn, setDateColumn] = useState<string>('');
  const [descriptionColumn, setDescriptionColumn] = useState<string>('');
  const [amountMode, setAmountMode] = useState<AmountMode>('single');
  const [amountColumn, setAmountColumn] = useState<string>('');
  const [debitColumn, setDebitColumn] = useState<string>('');
  const [creditColumn, setCreditColumn] = useState<string>('');
  const [dateFormat, setDateFormat] = useState<string>('YYYY-MM-DD');
  const [categoryColumn, setCategoryColumn] = useState<string>('');

  const matchColumn = (header: string, patterns: string[]): boolean => {
    const headerLower = header.toLowerCase().trim();
    return patterns.some(pattern => headerLower.includes(pattern));
  };

  // Auto-detect columns on mount
  useEffect(() => {
    if (initialMapping) {
      setDateColumn(initialMapping.date_column);
      setDescriptionColumn(initialMapping.description_column);
      setAmountMode(initialMapping.amount_mode);
      setAmountColumn(initialMapping.amount_column || '');
      setDebitColumn(initialMapping.debit_column || '');
      setCreditColumn(initialMapping.credit_column || '');
      setDateFormat(initialMapping.date_format);
      setCategoryColumn(initialMapping.category_column || '');
      return;
    }

    if (preview.suggested_mapping) {
      const m = preview.suggested_mapping;
      setDateColumn(m.date_column);
      setDescriptionColumn(m.description_column);
      setAmountMode(m.amount_mode);
      setAmountColumn(m.amount_column || '');
      setDebitColumn(m.debit_column || '');
      setCreditColumn(m.credit_column || '');
      setDateFormat(m.date_format);
      setCategoryColumn(m.category_column || '');
      return;
    }

    // Manual auto-detection
    for (const header of preview.headers) {
      if (!dateColumn && matchColumn(header, DATE_PATTERNS)) {
        setDateColumn(header);
      } else if (!descriptionColumn && matchColumn(header, DESCRIPTION_PATTERNS)) {
        setDescriptionColumn(header);
      } else if (!amountColumn && matchColumn(header, AMOUNT_PATTERNS)) {
        setAmountColumn(header);
      } else if (!debitColumn && matchColumn(header, DEBIT_PATTERNS)) {
        setDebitColumn(header);
      } else if (!creditColumn && matchColumn(header, CREDIT_PATTERNS)) {
        setCreditColumn(header);
      } else if (!categoryColumn && matchColumn(header, CATEGORY_PATTERNS)) {
        setCategoryColumn(header);
      }
    }
  }, [preview, initialMapping]);

  // Determine if we should suggest split mode
  useEffect(() => {
    if (!amountColumn && debitColumn && creditColumn) {
      setAmountMode('split');
    }
  }, [amountColumn, debitColumn, creditColumn]);

  const isValid = useMemo(() => {
    if (!dateColumn || !descriptionColumn) return false;
    if (amountMode === 'single' && !amountColumn) return false;
    if (amountMode === 'split' && (!debitColumn || !creditColumn)) return false;
    return true;
  }, [dateColumn, descriptionColumn, amountMode, amountColumn, debitColumn, creditColumn]);

  const datePreview = useMemo(() => {
    if (!dateColumn || preview.sample_rows.length === 0) return null;
    const colIndex = preview.headers.indexOf(dateColumn);
    if (colIndex === -1) return null;
    return preview.sample_rows[0][colIndex];
  }, [dateColumn, preview]);

  const handleConfirm = () => {
    const mapping: CsvColumnMapping = {
      date_column: dateColumn,
      description_column: descriptionColumn,
      amount_mode: amountMode,
      amount_column: amountMode === 'single' ? amountColumn : null,
      debit_column: amountMode === 'split' ? debitColumn : null,
      credit_column: amountMode === 'split' ? creditColumn : null,
      date_format: dateFormat,
      category_column: categoryColumn || null,
    };
    onConfirm(mapping);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-bold text-white">Configure Column Mapping</h2>
          <p className="text-sm text-gray-500 mt-1">
            Map CSV columns to transaction fields ({preview.row_count} rows detected)
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Sample Data Preview */}
          <div>
            <h3 className="text-sm font-medium text-gray-400 mb-3">CSV Preview</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/10">
                    {preview.headers.map((header, i) => (
                      <th key={i} className="px-3 py-2 text-left text-gray-500 font-medium">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.sample_rows.slice(0, 3).map((row, i) => (
                    <tr key={i} className="border-b border-white/5">
                      {row.map((cell, j) => (
                        <td key={j} className="px-3 py-2 text-gray-400 truncate max-w-[150px]">
                          {cell}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Column Mapping */}
          <div className="grid grid-cols-2 gap-4">
            {/* Date Column */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Date Column *
              </label>
              <select
                value={dateColumn}
                onChange={(e) => setDateColumn(e.target.value)}
                className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select column...</option>
                {preview.headers.map((header) => (
                  <option key={header} value={header}>{header}</option>
                ))}
              </select>
            </div>

            {/* Date Format */}
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Date Format
                {datePreview && (
                  <span className="text-gray-600 ml-2">
                    (sample: {datePreview})
                  </span>
                )}
              </label>
              <select
                value={dateFormat}
                onChange={(e) => setDateFormat(e.target.value)}
                className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                {DATE_FORMATS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            {/* Description Column */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Description Column *
              </label>
              <select
                value={descriptionColumn}
                onChange={(e) => setDescriptionColumn(e.target.value)}
                className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="">Select column...</option>
                {preview.headers.map((header) => (
                  <option key={header} value={header}>{header}</option>
                ))}
              </select>
            </div>

            {/* Category Column (Optional) */}
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-400 mb-2">
                Category Column <span className="text-gray-600">(optional)</span>
              </label>
              <select
                value={categoryColumn}
                onChange={(e) => setCategoryColumn(e.target.value)}
                className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
              >
                <option value="">No category mapping</option>
                {preview.headers.map((header) => (
                  <option key={header} value={header}>{header}</option>
                ))}
              </select>
              <p className="text-xs text-gray-600 mt-1">
                Map a category column to auto-assign categories during import
              </p>
            </div>
          </div>

          {/* Amount Mode Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-3">
              Amount Format
            </label>
            <div className="flex space-x-4">
              <button
                onClick={() => setAmountMode('single')}
                className={`flex-1 px-4 py-3 rounded-lg border text-sm font-medium transition-all ${
                  amountMode === 'single'
                    ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                    : 'border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <div className="font-semibold">Single Amount Column</div>
                <div className="text-xs mt-1 opacity-70">Negative = debit, Positive = credit</div>
              </button>
              <button
                onClick={() => setAmountMode('split')}
                className={`flex-1 px-4 py-3 rounded-lg border text-sm font-medium transition-all ${
                  amountMode === 'split'
                    ? 'border-blue-500 bg-blue-500/10 text-blue-400'
                    : 'border-white/10 text-gray-400 hover:border-white/20'
                }`}
              >
                <div className="font-semibold">Separate Debit/Credit</div>
                <div className="text-xs mt-1 opacity-70">Two columns for debit and credit</div>
              </button>
            </div>
          </div>

          {/* Amount Columns */}
          <div className="grid grid-cols-2 gap-4">
            {amountMode === 'single' ? (
              <div className="col-span-2">
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  Amount Column *
                </label>
                <select
                  value={amountColumn}
                  onChange={(e) => setAmountColumn(e.target.value)}
                  className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                >
                  <option value="">Select column...</option>
                  {preview.headers.map((header) => (
                    <option key={header} value={header}>{header}</option>
                  ))}
                </select>
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Debit Column *
                  </label>
                  <select
                    value={debitColumn}
                    onChange={(e) => setDebitColumn(e.target.value)}
                    className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select column...</option>
                    {preview.headers.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">
                    Credit Column *
                  </label>
                  <select
                    value={creditColumn}
                    onChange={(e) => setCreditColumn(e.target.value)}
                    className="w-full bg-gray-900 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-blue-500 focus:outline-none"
                  >
                    <option value="">Select column...</option>
                    {preview.headers.map((header) => (
                      <option key={header} value={header}>{header}</option>
                    ))}
                  </select>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex justify-end space-x-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white border border-white/10 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!isValid}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              isValid
                ? 'bg-blue-500 hover:bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-500 cursor-not-allowed'
            }`}
          >
            Preview Import
          </button>
        </div>
      </div>
    </div>
  );
};

export default CsvColumnMapper;
