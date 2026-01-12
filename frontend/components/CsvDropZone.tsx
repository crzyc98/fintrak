import React, { useState, useRef, useCallback } from 'react';

interface CsvDropZoneProps {
  onFileSelect: (fileContent: string, fileName: string) => void;
  disabled?: boolean;
}

const CsvDropZone: React.FC<CsvDropZoneProps> = ({ onFileSelect, disabled = false }) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      alert('Please select a CSV file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      // Convert to base64
      const base64 = btoa(content);
      onFileSelect(base64, file.name);
    };
    reader.onerror = () => {
      alert('Failed to read file');
    };
    reader.readAsBinaryString(file);
  }, [onFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) {
      setIsDragging(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, [disabled, handleFile]);

  const handleClick = useCallback(() => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [disabled]);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
    // Reset input so same file can be selected again
    e.target.value = '';
  }, [handleFile]);

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all
        ${disabled
          ? 'border-gray-700 bg-gray-900/50 cursor-not-allowed opacity-50'
          : isDragging
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-gray-700 hover:border-gray-500 hover:bg-white/5'
        }
      `}
    >
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv"
        onChange={handleFileInput}
        className="hidden"
        disabled={disabled}
      />

      <div className="flex flex-col items-center space-y-3">
        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
          isDragging ? 'bg-blue-500/20' : 'bg-gray-800'
        }`}>
          <svg
            className={`w-6 h-6 ${isDragging ? 'text-blue-400' : 'text-gray-500'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>

        <div>
          <p className={`text-sm font-medium ${isDragging ? 'text-blue-400' : 'text-gray-400'}`}>
            {isDragging ? 'Drop CSV file here' : 'Drop CSV file or click to browse'}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Import transactions from your bank
          </p>
        </div>
      </div>
    </div>
  );
};

export default CsvDropZone;
