import React, { useState, useEffect, useMemo } from 'react';
import { Category, CategoryGroup, CategoryTreeNode, CATEGORY_GROUPS } from '../types';
import {
  fetchCategories,
  fetchCategoryTree,
  createCategory,
  updateCategory,
  deleteCategory,
} from '../src/services/api';
import CategoryForm from './forms/CategoryForm';

const CategoriesView: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryTree, setCategoryTree] = useState<CategoryTreeNode[]>([]);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | undefined>(undefined);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [flatData, treeData] = await Promise.all([
        fetchCategories(),
        fetchCategoryTree(),
      ]);
      setCategories(flatData);
      setCategoryTree(treeData);
      if (flatData.length > 0 && !selectedCategoryId) {
        setSelectedCategoryId(flatData[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load categories');
    } finally {
      setIsLoading(false);
    }
  };

  const selectedCategory = useMemo(
    () => categories.find((c) => c.id === selectedCategoryId),
    [categories, selectedCategoryId]
  );

  const categoriesByGroup = useMemo(() => {
    const groups: Record<CategoryGroup, CategoryTreeNode[]> = {} as Record<
      CategoryGroup,
      CategoryTreeNode[]
    >;
    CATEGORY_GROUPS.forEach((g) => {
      groups[g] = categoryTree.filter((c) => c.group_name === g);
    });
    return groups;
  }, [categoryTree]);

  const totalBudget = useMemo(
    () => categories.reduce((sum, c) => sum + (c.budget_amount || 0), 0),
    [categories]
  );

  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(expandedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedIds(next);
  };

  const handleCreateCategory = async (data: {
    name: string;
    emoji?: string;
    parent_id?: string;
    group_name: CategoryGroup;
    budget_amount?: number;
  }) => {
    await createCategory(data);
    await loadCategories();
    setShowForm(false);
  };

  const handleUpdateCategory = async (data: {
    name: string;
    emoji?: string;
    parent_id?: string;
    group_name: CategoryGroup;
    budget_amount?: number;
  }) => {
    if (!editingCategory) return;
    await updateCategory(editingCategory.id, data);
    await loadCategories();
    setEditingCategory(undefined);
    setShowForm(false);
  };

  const handleDeleteCategory = async (id: string) => {
    try {
      await deleteCategory(id);
      await loadCategories();
      if (selectedCategoryId === id) {
        setSelectedCategoryId(categories.length > 1 ? categories[0].id : null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete category');
    }
    setDeleteConfirm(null);
  };

  const formatBudget = (cents: number | null): string => {
    if (cents === null || cents === 0) return '--';
    return `$${(cents / 100).toLocaleString(undefined, { minimumFractionDigits: 2 })}`;
  };

  const renderCategoryNode = (node: CategoryTreeNode, depth: number = 0) => {
    const hasChildren = node.children && node.children.length > 0;
    const isExpanded = expandedIds.has(node.id);

    return (
      <div key={node.id}>
        <div
          onClick={() => setSelectedCategoryId(node.id)}
          className={`flex items-center px-4 py-3.5 rounded-xl cursor-pointer transition-all ${
            selectedCategoryId === node.id
              ? 'bg-blue-500/10 ring-1 ring-blue-500/20'
              : 'hover:bg-white/5'
          }`}
          style={{ paddingLeft: `${16 + depth * 24}px` }}
        >
          <div className="flex items-center flex-1 min-w-0">
            {hasChildren ? (
              <button
                onClick={(e) => toggleExpand(node.id, e)}
                className={`mr-2 transition-transform duration-200 ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              >
                <svg
                  className="w-3.5 h-3.5 text-gray-600"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            ) : (
              <div className="w-5.5 mr-2" />
            )}

            {node.emoji && <span className="mr-3 text-lg">{node.emoji}</span>}

            <span
              className={`text-sm font-bold truncate ${
                depth === 0 ? 'text-white' : 'text-gray-300'
              }`}
            >
              {node.name}
            </span>
          </div>

          <span className="text-sm font-bold text-gray-500 tabular-nums">
            {formatBudget(node.budget_amount)}
          </span>
        </div>

        {hasChildren && isExpanded && (
          <div className="relative">
            <div
              className="absolute left-0 top-0 bottom-0 w-0.5 bg-white/5"
              style={{ left: `${28 + depth * 24}px` }}
            />
            {node.children.map((child) => renderCategoryNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center bg-[#050910]">
        <div className="text-gray-500">Loading categories...</div>
      </div>
    );
  }

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Center Pane: Category List */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <h1 className="text-sm font-bold text-gray-300">Categories</h1>
          <button
            onClick={() => {
              setEditingCategory(undefined);
              setShowForm(true);
            }}
            className="text-gray-500 hover:text-white transition-colors"
            title="Add Category"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>
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

          {/* Summary Card */}
          <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-10 flex items-center justify-between shadow-2xl">
            <div className="flex-1 text-center">
              <div className="text-3xl font-black text-white">{categories.length}</div>
              <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">
                Categories
              </div>
            </div>
            <div className="w-px h-12 bg-white/10" />
            <div className="flex-1 text-center">
              <div className="text-3xl font-black text-white">{formatBudget(totalBudget)}</div>
              <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">
                Total Budget
              </div>
            </div>
          </div>

          {categories.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">No categories yet</p>
              <button
                onClick={() => {
                  setEditingCategory(undefined);
                  setShowForm(true);
                }}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm font-bold rounded-xl transition-colors"
              >
                Create Your First Category
              </button>
            </div>
          ) : (
            CATEGORY_GROUPS.map((group) => {
              const groupCategories = categoriesByGroup[group];
              if (groupCategories.length === 0) return null;

              return (
                <div key={group} className="mb-10">
                  <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-4 px-4">
                    <svg className="w-3.5 h-3.5 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" />
                    </svg>
                    {group}
                  </h2>
                  <div className="space-y-1">
                    {groupCategories.map((cat) => renderCategoryNode(cat))}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Pane: Category Details */}
      <div className="w-[450px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar border-l border-white/5">
        {selectedCategory ? (
          <div className="p-8">
            <div className="flex justify-between items-center mb-10">
              <h3 className="text-sm font-bold text-white">Category Details</h3>
              <div className="flex space-x-2">
                <button
                  onClick={() => {
                    setEditingCategory(selectedCategory);
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
                  onClick={() => setDeleteConfirm(selectedCategory.id)}
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

            <div className="mb-12">
              <div className="flex items-center mb-4">
                {selectedCategory.emoji && (
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-2xl mr-4">
                    {selectedCategory.emoji}
                  </div>
                )}
                <div>
                  <h2 className="text-3xl font-black text-white tracking-tight">
                    {selectedCategory.name}
                  </h2>
                  <span className="text-xs font-bold text-gray-500 uppercase">
                    {selectedCategory.group_name}
                  </span>
                </div>
              </div>

              <div className="mt-6">
                <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">
                  Monthly Budget
                </div>
                <div className="text-3xl font-black text-white tabular-nums tracking-tighter">
                  {formatBudget(selectedCategory.budget_amount)}
                </div>
                {!selectedCategory.budget_amount && (
                  <p className="text-xs text-gray-500 mt-1">No budget set</p>
                )}
              </div>
            </div>

            <div className="space-y-4 text-sm">
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Group</span>
                <span className="text-white font-medium">{selectedCategory.group_name}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Parent Category</span>
                <span className="text-white font-medium">
                  {selectedCategory.parent_id
                    ? categories.find((c) => c.id === selectedCategory.parent_id)?.name || '--'
                    : 'None (top-level)'}
                </span>
              </div>
              <div className="flex justify-between py-2 border-b border-white/5">
                <span className="text-gray-500">Created</span>
                <span className="text-white font-medium">
                  {new Date(selectedCategory.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">
            Select a category to view details
          </div>
        )}
      </div>

      {/* Category Form Modal */}
      {showForm && (
        <CategoryForm
          category={editingCategory}
          categories={categories}
          onSubmit={editingCategory ? handleUpdateCategory : handleCreateCategory}
          onCancel={() => {
            setShowForm(false);
            setEditingCategory(undefined);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-8 w-full max-w-md">
            <h2 className="text-xl font-bold text-white mb-4">Delete Category?</h2>
            <p className="text-gray-400 mb-6">
              Are you sure you want to delete this category? This action cannot be undone.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="flex-1 px-4 py-3 text-sm font-bold text-gray-400 hover:text-white border border-white/10 rounded-xl transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteCategory(deleteConfirm)}
                className="flex-1 px-4 py-3 text-sm font-bold text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoriesView;
