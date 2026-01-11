import React, { useState, useEffect } from 'react';
import { Category, CategoryGroup, CATEGORY_GROUPS } from '../../types';

interface CategoryFormProps {
  category?: Category;
  categories: Category[];
  onSubmit: (data: {
    name: string;
    emoji?: string;
    parent_id?: string;
    group_name: CategoryGroup;
    budget_amount?: number;
  }) => Promise<void>;
  onCancel: () => void;
}

interface FormErrors {
  name?: string;
  parent_id?: string;
  group_name?: string;
  budget_amount?: string;
}

const CategoryForm: React.FC<CategoryFormProps> = ({
  category,
  categories,
  onSubmit,
  onCancel,
}) => {
  const [name, setName] = useState(category?.name || '');
  const [emoji, setEmoji] = useState(category?.emoji || '');
  const [parentId, setParentId] = useState(category?.parent_id || '');
  const [groupName, setGroupName] = useState<CategoryGroup>(
    category?.group_name || 'Essential'
  );
  const [budgetAmount, setBudgetAmount] = useState<string>(
    category?.budget_amount ? (category.budget_amount / 100).toString() : ''
  );
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (category) {
      setName(category.name);
      setEmoji(category.emoji || '');
      setParentId(category.parent_id || '');
      setGroupName(category.group_name);
      setBudgetAmount(
        category.budget_amount ? (category.budget_amount / 100).toString() : ''
      );
    }
  }, [category]);

  const getDescendantIds = (catId: string): Set<string> => {
    const descendants = new Set<string>();
    const findDescendants = (id: string) => {
      categories.forEach((c) => {
        if (c.parent_id === id) {
          descendants.add(c.id);
          findDescendants(c.id);
        }
      });
    };
    findDescendants(catId);
    return descendants;
  };

  const availableParents = categories.filter((c) => {
    if (!category) return true;
    if (c.id === category.id) return false;
    const descendants = getDescendantIds(category.id);
    return !descendants.has(c.id);
  });

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Name is required';
    } else if (name.length > 100) {
      newErrors.name = 'Name must be 100 characters or less';
    }

    if (!groupName) {
      newErrors.group_name = 'Group is required';
    }

    if (budgetAmount && isNaN(parseFloat(budgetAmount))) {
      newErrors.budget_amount = 'Budget must be a valid number';
    }

    if (budgetAmount && parseFloat(budgetAmount) < 0) {
      newErrors.budget_amount = 'Budget cannot be negative';
    }

    if (category && parentId === category.id) {
      newErrors.parent_id = 'Category cannot be its own parent';
    }

    if (category && parentId) {
      const descendants = getDescendantIds(category.id);
      if (descendants.has(parentId)) {
        newErrors.parent_id = 'Cannot select a descendant as parent (circular reference)';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      const budgetCents = budgetAmount
        ? Math.round(parseFloat(budgetAmount) * 100)
        : undefined;

      await onSubmit({
        name: name.trim(),
        emoji: emoji.trim() || undefined,
        parent_id: parentId || undefined,
        group_name: groupName,
        budget_amount: budgetCents,
      });
    } catch (err) {
      console.error('Failed to save category:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-[#0a0f1d] border border-white/10 rounded-2xl p-8 w-full max-w-md">
        <h2 className="text-xl font-bold text-white mb-6">
          {category ? 'Edit Category' : 'Create Category'}
        </h2>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex space-x-4">
            <div className="flex-1">
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                Category Name
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={`w-full bg-[#050910] border ${
                  errors.name ? 'border-red-500' : 'border-white/10'
                } rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500`}
                placeholder="e.g., Groceries"
                maxLength={100}
              />
              {errors.name && (
                <p className="mt-1 text-xs text-red-500">{errors.name}</p>
              )}
            </div>
            <div className="w-24">
              <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
                Emoji
              </label>
              <input
                type="text"
                value={emoji}
                onChange={(e) => setEmoji(e.target.value)}
                className="w-full bg-[#050910] border border-white/10 rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500 text-center"
                placeholder="🛒"
                maxLength={10}
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              Group
            </label>
            <select
              value={groupName}
              onChange={(e) => setGroupName(e.target.value as CategoryGroup)}
              className={`w-full bg-[#050910] border ${
                errors.group_name ? 'border-red-500' : 'border-white/10'
              } rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500`}
            >
              {CATEGORY_GROUPS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
            {errors.group_name && (
              <p className="mt-1 text-xs text-red-500">{errors.group_name}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              Parent Category (Optional)
            </label>
            <select
              value={parentId}
              onChange={(e) => setParentId(e.target.value)}
              className={`w-full bg-[#050910] border ${
                errors.parent_id ? 'border-red-500' : 'border-white/10'
              } rounded-xl px-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500`}
            >
              <option value="">No parent (top-level)</option>
              {availableParents.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.emoji ? `${c.emoji} ` : ''}{c.name}
                </option>
              ))}
            </select>
            {errors.parent_id && (
              <p className="mt-1 text-xs text-red-500">{errors.parent_id}</p>
            )}
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">
              Monthly Budget (Optional)
            </label>
            <div className="relative">
              <span className="absolute left-4 top-3 text-gray-500">$</span>
              <input
                type="text"
                value={budgetAmount}
                onChange={(e) => setBudgetAmount(e.target.value)}
                className={`w-full bg-[#050910] border ${
                  errors.budget_amount ? 'border-red-500' : 'border-white/10'
                } rounded-xl pl-8 pr-4 py-3 text-white text-sm focus:outline-none focus:border-blue-500`}
                placeholder="0.00"
              />
            </div>
            {errors.budget_amount && (
              <p className="mt-1 text-xs text-red-500">{errors.budget_amount}</p>
            )}
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-4 py-3 text-sm font-bold text-gray-400 hover:text-white border border-white/10 rounded-xl transition-colors"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-3 text-sm font-bold text-white bg-blue-500 hover:bg-blue-600 rounded-xl transition-colors disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : category ? 'Save Changes' : 'Create Category'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CategoryForm;
