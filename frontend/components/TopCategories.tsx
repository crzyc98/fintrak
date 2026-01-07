
import React, { useState } from 'react';
import { MOCK_CATEGORIES } from '../mockData';

const TopCategories: React.FC = () => {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(['c1']));

  const toggleExpand = (id: string) => {
    const next = new Set(expanded);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpanded(next);
  };

  const mainCategories = MOCK_CATEGORIES.filter(c => !c.parentId);
  const getSubCategories = (parentId: string) => MOCK_CATEGORIES.filter(c => c.parentId === parentId);

  return (
    <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 h-full">
      <div className="flex justify-between items-center mb-10">
        <h2 className="text-sm font-semibold text-gray-400">Top categories</h2>
        <button className="text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center">
          Categories <svg className="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7"></path></svg>
        </button>
      </div>

      <div className="space-y-8">
        {mainCategories.map(cat => {
          const subs = getSubCategories(cat.id);
          const isExpanded = expanded.has(cat.id);
          const percent = Math.min((cat.spent / cat.budget) * 100, 100);

          return (
            <div key={cat.id} className="space-y-4">
              <div className="flex items-center justify-between group cursor-pointer" onClick={() => toggleExpand(cat.id)}>
                <div className="flex items-center min-w-0">
                  <div className={`transition-all duration-300 ${isExpanded ? 'rotate-180' : ''}`}>
                    <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
                  </div>
                  <div className="w-5 h-5 rounded-md bg-[#2d1b4e] flex items-center justify-center text-[10px] font-black text-[#a78bfa] ml-2 mr-3">2</div>
                  <span className="text-sm font-semibold text-gray-300">{cat.name}</span>
                </div>
                <div className="flex items-center space-x-6">
                  <span className="text-xs font-bold text-gray-300 tabular-nums">${cat.spent}</span>
                  <div className="w-24 h-1.5 bg-[#1e293b] rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-orange-500 rounded-full" 
                      style={{ width: `${percent}%` }}
                    ></div>
                  </div>
                  <span className="text-xs font-medium text-gray-500 w-10 text-right tabular-nums">${cat.budget}</span>
                </div>
              </div>

              {isExpanded && subs.length > 0 && (
                <div className="ml-[18px] space-y-4 pt-1 border-l-2 border-white/5 pl-6 relative">
                  {subs.map(sub => (
                    <div key={sub.id} className="flex items-center justify-between">
                       <div className="flex items-center min-w-0">
                         <span className="text-sm font-medium text-gray-500">{sub.icon} {sub.name}</span>
                       </div>
                       <div className="flex items-center space-x-6">
                         <span className="text-xs font-semibold text-gray-400 tabular-nums">${sub.spent}</span>
                         <div className="w-24 h-1.5 bg-[#1e293b]/50 rounded-full overflow-hidden">
                           <div 
                             className={`h-full ${sub.spent > sub.budget ? 'bg-[#ef4444]' : 'bg-[#10b981]'}`} 
                             style={{ width: `${Math.min((sub.spent / sub.budget) * 100, 100)}%` }}
                           ></div>
                         </div>
                         <span className="text-xs font-medium text-gray-600 w-10 text-right tabular-nums">${sub.budget}</span>
                       </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TopCategories;
