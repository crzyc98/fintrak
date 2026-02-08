import React, { useState, useEffect } from 'react';
import {
  CategoryMappingSuggestion,
  CategoryData,
  fetchCategories,
  createCategory,
} from '../src/services/api';

interface CategoryMappingReviewProps {
  suggestions: CategoryMappingSuggestion[];
  onConfirm: (
    mappings: Array<{ source_category: string; target_category_id: string }>,
    saveMappings: boolean
  ) => void;
  onCancel: () => void;
  onSkip: () => void;
  isLoading?: boolean;
}

interface MappingState {
  source_category: string;
  target_category_id: string | null;
  target_category_name: string | null;
  target_category_emoji: string | null;
  confidence: number;
  skipped: boolean;
}

const CategoryMappingReview: React.FC<CategoryMappingReviewProps> = ({
  suggestions,
  onConfirm,
  onCancel,
  onSkip,
  isLoading = false,
}) => {
  const [mappings, setMappings] = useState<MappingState[]>([]);
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [saveMappingsForFuture, setSaveMappingsForFuture] = useState(true);
  const [categoriesLoading, setCategoriesLoading] = useState(true);

  // State for inline category creation
  const [creatingForIndex, setCreatingForIndex] = useState<number | null>(null);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryEmoji, setNewCategoryEmoji] = useState('');
  const [newCategoryGroup, setNewCategoryGroup] = useState('Essential');
  const [isCreatingCategory, setIsCreatingCategory] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  useEffect(() => {
    // Initialize mappings from suggestions
    setMappings(
      suggestions.map((s) => ({
        source_category: s.source_category,
        target_category_id: s.target_category_id,
        target_category_name: s.target_category_name,
        target_category_emoji: s.target_category_emoji,
        confidence: s.confidence,
        skipped: false,
      }))
    );

    // Load categories for dropdown
    fetchCategories()
      .then(setCategories)
      .catch(console.error)
      .finally(() => setCategoriesLoading(false));
  }, [suggestions]);

  const handleCategoryChange = (index: number, categoryId: string) => {
    setMappings((prev) => {
      const next = [...prev];
      const category = categories.find((c) => c.id === categoryId);
      next[index] = {
        ...next[index],
        target_category_id: categoryId || null,
        target_category_name: category?.name || null,
        target_category_emoji: category?.emoji || null,
        skipped: false,
      };
      return next;
    });
  };

  const handleSkipToggle = (index: number) => {
    setMappings((prev) => {
      const next = [...prev];
      next[index] = {
        ...next[index],
        skipped: !next[index].skipped,
      };
      return next;
    });
  };

  const handleStartCreateCategory = (index: number) => {
    // Pre-fill the name with the source category (cleaned up a bit)
    const sourceCategory = mappings[index].source_category;
    // Try to extract a clean name from formats like "Restaurant-Restaurant" or "Merchandise & Supplies-Groceries"
    const parts = sourceCategory.split('-');
    const cleanName = parts[parts.length - 1].trim();

    setCreatingForIndex(index);
    setNewCategoryName(cleanName);
    setNewCategoryEmoji('');
    setNewCategoryGroup('Essential');
    setCreateError(null);
  };

  const handleCancelCreateCategory = () => {
    setCreatingForIndex(null);
    setNewCategoryName('');
    setNewCategoryEmoji('');
    setNewCategoryGroup('Essential');
    setCreateError(null);
  };

  const handleCreateCategory = async () => {
    if (!newCategoryName.trim()) {
      setCreateError('Category name is required');
      return;
    }

    if (creatingForIndex === null) return;

    setIsCreatingCategory(true);
    setCreateError(null);

    try {
      const newCategory = await createCategory({
        name: newCategoryName.trim(),
        emoji: newCategoryEmoji.trim() || undefined,
        group_name: newCategoryGroup,
      });

      // Add to categories list
      setCategories((prev) => [...prev, newCategory]);

      // Update the mapping to use the new category
      setMappings((prev) => {
        const next = [...prev];
        next[creatingForIndex] = {
          ...next[creatingForIndex],
          target_category_id: newCategory.id,
          target_category_name: newCategory.name,
          target_category_emoji: newCategory.emoji,
          skipped: false,
        };
        return next;
      });

      // Close the create form
      handleCancelCreateCategory();
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create category');
    } finally {
      setIsCreatingCategory(false);
    }
  };

  const handleConfirm = () => {
    const validMappings = mappings
      .filter((m) => !m.skipped && m.target_category_id)
      .map((m) => ({
        source_category: m.source_category,
        target_category_id: m.target_category_id!,
      }));

    onConfirm(validMappings, saveMappingsForFuture);
  };

  const getConfidenceColor = (confidence: number): string => {
    if (confidence >= 0.7) return 'text-green-400';
    if (confidence >= 0.5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getConfidenceLabel = (confidence: number): string => {
    if (confidence >= 0.7) return 'High';
    if (confidence >= 0.5) return 'Medium';
    return 'Low';
  };

  // Group categories by group_name for better organization in dropdown
  const groupedCategories: Record<string, CategoryData[]> = categories.reduce<Record<string, CategoryData[]>>(
    (acc, cat) => {
      const group = cat.group_name || 'Other';
      if (!acc[group]) acc[group] = [];
      acc[group].push(cat);
      return acc;
    },
    {}
  );

  const validMappingsCount = mappings.filter(
    (m) => !m.skipped && m.target_category_id
  ).length;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-white/10">
          <h2 className="text-lg font-bold text-white">Map Categories</h2>
          <p className="text-sm text-gray-500 mt-1">
            We found {suggestions.length} category name{suggestions.length !== 1 ? 's' : ''} that don't match existing categories.
            Review the AI suggestions below and adjust if needed.
          </p>
        </div>

        {/* Info Banner */}
        <div className="px-6 py-3 bg-blue-500/10 border-b border-blue-500/20">
          <div className="flex items-center space-x-3">
            <div className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <svg className="w-3 h-3 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-blue-300">
              AI-suggested mappings are pre-selected. You can override any selection using the dropdown, or click + to create a new category.
            </p>
          </div>
        </div>

        {/* Mapping List */}
        <div className="flex-1 overflow-y-auto p-4">
          {categoriesLoading ? (
            <div className="flex items-center justify-center py-8">
              <svg className="animate-spin h-6 w-6 text-gray-500" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              <span className="ml-2 text-gray-500">Loading categories...</span>
            </div>
          ) : (
            <div className="space-y-3">
              {mappings.map((mapping, index) => (
                <div
                  key={mapping.source_category}
                  className={`p-4 rounded-xl border transition-all ${
                    mapping.skipped
                      ? 'bg-gray-900/50 border-gray-700 opacity-50'
                      : mapping.target_category_id
                        ? 'bg-green-500/5 border-green-500/20'
                        : 'bg-orange-500/5 border-orange-500/20'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <span className="text-sm font-medium text-white">
                        "{mapping.source_category}"
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getConfidenceColor(mapping.confidence)} bg-gray-800`}>
                        {getConfidenceLabel(mapping.confidence)} confidence
                      </span>
                    </div>
                    <button
                      onClick={() => handleSkipToggle(index)}
                      className={`text-xs px-2 py-1 rounded transition-colors ${
                        mapping.skipped
                          ? 'text-blue-400 hover:text-blue-300'
                          : 'text-gray-500 hover:text-gray-300'
                      }`}
                    >
                      {mapping.skipped ? 'Include' : 'Skip'}
                    </button>
                  </div>

                  {creatingForIndex === index ? (
                    /* Inline category creation form */
                    <div className="space-y-3 mt-2 p-3 bg-[#050910] rounded-lg border border-blue-500/30">
                      <div className="text-xs font-medium text-blue-400 mb-2">Create New Category</div>

                      {createError && (
                        <div className="text-xs text-red-400 bg-red-500/10 px-2 py-1 rounded">
                          {createError}
                        </div>
                      )}

                      <div className="flex space-x-2">
                        <input
                          type="text"
                          value={newCategoryEmoji}
                          onChange={(e) => setNewCategoryEmoji(e.target.value)}
                          placeholder="Emoji"
                          maxLength={4}
                          className="w-16 px-2 py-1.5 bg-gray-900 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                        />
                        <input
                          type="text"
                          value={newCategoryName}
                          onChange={(e) => setNewCategoryName(e.target.value)}
                          placeholder="Category name"
                          className="flex-1 px-2 py-1.5 bg-gray-900 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                        />
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-500">Group:</span>
                        <select
                          value={newCategoryGroup}
                          onChange={(e) => setNewCategoryGroup(e.target.value)}
                          className="flex-1 px-2 py-1.5 bg-gray-900 border border-white/10 rounded text-white text-sm focus:outline-none focus:ring-1 focus:ring-blue-500/50"
                        >
                          <option value="Essential">Essential</option>
                          <option value="Lifestyle">Lifestyle</option>
                          <option value="Income">Income</option>
                          <option value="Transfer">Transfer</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>

                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={handleCancelCreateCategory}
                          disabled={isCreatingCategory}
                          className="px-3 py-1.5 text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                        >
                          Cancel
                        </button>
                        <button
                          onClick={handleCreateCategory}
                          disabled={isCreatingCategory || !newCategoryName.trim()}
                          className="px-3 py-1.5 text-xs font-medium bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors disabled:opacity-50"
                        >
                          {isCreatingCategory ? 'Creating...' : 'Create'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    /* Category selection dropdown */
                    <div className="flex items-center space-x-2">
                      <svg className="w-4 h-4 text-gray-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 8l4 4m0 0l-4 4m4-4H3" />
                      </svg>
                      <select
                        value={mapping.target_category_id || ''}
                        onChange={(e) => handleCategoryChange(index, e.target.value)}
                        disabled={mapping.skipped}
                        className="flex-1 px-3 py-2 bg-[#050910] border border-white/10 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50 disabled:opacity-50"
                      >
                        <option value="">-- No category --</option>
                        {Object.entries(groupedCategories).map(([group, cats]) => (
                          <optgroup key={group} label={group}>
                            {cats.map((cat) => (
                              <option key={cat.id} value={cat.id}>
                                {cat.emoji ? `${cat.emoji} ` : ''}{cat.name}
                              </option>
                            ))}
                          </optgroup>
                        ))}
                      </select>
                      <button
                        onClick={() => handleStartCreateCategory(index)}
                        disabled={mapping.skipped}
                        className="px-2 py-2 text-xs text-blue-400 hover:text-blue-300 hover:bg-blue-500/10 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
                        title="Create new category"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Save Option */}
        <div className="px-6 py-3 border-t border-white/5">
          <label className="flex items-center space-x-3 cursor-pointer">
            <input
              type="checkbox"
              checked={saveMappingsForFuture}
              onChange={(e) => setSaveMappingsForFuture(e.target.checked)}
              className="rounded border-gray-600 bg-gray-800 text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">
              Save mappings for future imports from this account
            </span>
          </label>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-white/10 flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {validMappingsCount} of {mappings.length} categories mapped
          </div>
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white border border-white/10 rounded-lg transition-colors disabled:opacity-50"
            >
              Cancel Import
            </button>
            <button
              onClick={onSkip}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white border border-white/10 rounded-lg transition-colors disabled:opacity-50"
            >
              Skip Mapping
            </button>
            <button
              onClick={handleConfirm}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Applying...
                </span>
              ) : (
                'Apply Mappings'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CategoryMappingReview;
