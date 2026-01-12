import React, { useState } from 'react';
import { CategoryData } from '../src/services/api';

interface ReviewActionBarProps {
  selectedCount: number;
  onMarkReviewed: () => Promise<void>;
  onSetCategory: (categoryId: string) => Promise<void>;
  onAddNote: (note: string) => Promise<void>;
  categories: CategoryData[];
  isLoading: boolean;
  error?: string | null;
}

const ReviewActionBar: React.FC<ReviewActionBarProps> = ({
  selectedCount,
  onMarkReviewed,
  onSetCategory,
  onAddNote,
  categories,
  isLoading,
  error,
}) => {
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const showSuccess = (message: string) => {
    setSuccessMessage(message);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  const handleMarkReviewed = async () => {
    await onMarkReviewed();
    showSuccess(`Marked ${selectedCount} transaction${selectedCount > 1 ? 's' : ''} as reviewed`);
  };

  const handleCategorySelect = async (categoryId: string) => {
    setShowCategoryDropdown(false);
    await onSetCategory(categoryId);
    const category = categories.find((c) => c.id === categoryId);
    showSuccess(
      `Set category to "${category?.name || 'Unknown'}" for ${selectedCount} transaction${
        selectedCount > 1 ? 's' : ''
      }`
    );
  };

  const handleAddNote = async () => {
    if (!noteText.trim()) return;
    setShowNoteModal(false);
    await onAddNote(noteText.trim());
    showSuccess(`Added note to ${selectedCount} transaction${selectedCount > 1 ? 's' : ''}`);
    setNoteText('');
  };

  if (selectedCount === 0) {
    return null;
  }

  return (
    <>
      <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-4 shadow-xl">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold text-white">
              {selectedCount} selected
            </span>
          </div>

          <div className="flex items-center space-x-3">
            {/* Mark Reviewed Button */}
            <button
              onClick={handleMarkReviewed}
              disabled={isLoading}
              className="flex items-center px-4 py-2 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-xs font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <LoadingSpinner />
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
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              )}
              Mark Reviewed
            </button>

            {/* Category Dropdown */}
            <div className="relative">
              <button
                onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
                disabled={isLoading}
                className="flex items-center px-4 py-2 bg-[#1a1f2e] hover:bg-[#252b3b] border border-white/10 text-white text-xs font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
                    d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                  ></path>
                </svg>
                Set Category
                <svg
                  className="w-3 h-3 ml-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M19 9l-7 7-7-7"
                  ></path>
                </svg>
              </button>

              {showCategoryDropdown && (
                <div className="absolute right-0 mt-2 w-64 bg-[#0a0f1d] border border-white/10 rounded-xl shadow-2xl z-50 max-h-80 overflow-y-auto custom-scrollbar">
                  {categories.length === 0 ? (
                    <div className="px-4 py-3 text-gray-500 text-sm">No categories available</div>
                  ) : (
                    categories.map((category) => (
                      <button
                        key={category.id}
                        onClick={() => handleCategorySelect(category.id)}
                        className="w-full flex items-center px-4 py-3 hover:bg-white/5 text-left transition-colors"
                      >
                        {category.emoji && (
                          <span className="mr-3 text-base">{category.emoji}</span>
                        )}
                        <span className="text-sm text-white">{category.name}</span>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Add Note Button */}
            <button
              onClick={() => setShowNoteModal(true)}
              disabled={isLoading}
              className="flex items-center px-4 py-2 bg-[#1a1f2e] hover:bg-[#252b3b] border border-white/10 text-white text-xs font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
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
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                ></path>
              </svg>
              Add Note
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-3 px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-xs">
            {error}
          </div>
        )}

        {/* Success Message */}
        {successMessage && (
          <div className="mt-3 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-xs">
            {successMessage}
          </div>
        )}
      </div>

      {/* Note Modal */}
      {showNoteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl">
            <h3 className="text-lg font-bold text-white mb-4">Add Note</h3>
            <p className="text-sm text-gray-400 mb-4">
              This note will be appended to {selectedCount} transaction
              {selectedCount > 1 ? 's' : ''}.
            </p>
            <textarea
              value={noteText}
              onChange={(e) => setNoteText(e.target.value)}
              placeholder="Enter your note..."
              className="w-full h-32 bg-[#1a1f2e] border border-white/10 rounded-lg px-4 py-3 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none"
              maxLength={1000}
              autoFocus
            />
            <div className="flex justify-between items-center mt-2 mb-4">
              <span className="text-xs text-gray-500">{noteText.length}/1000</span>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowNoteModal(false);
                  setNoteText('');
                }}
                className="px-4 py-2 text-gray-400 hover:text-white text-sm font-medium transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAddNote}
                disabled={!noteText.trim() || isLoading}
                className="px-4 py-2 bg-[#3b82f6] hover:bg-[#2563eb] text-white text-sm font-bold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? <LoadingSpinner /> : 'Add Note'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close dropdown */}
      {showCategoryDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowCategoryDropdown(false)}
        />
      )}
    </>
  );
};

const LoadingSpinner: React.FC = () => (
  <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
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
);

export default ReviewActionBar;
