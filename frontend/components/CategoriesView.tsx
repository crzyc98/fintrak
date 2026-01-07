
import React, { useState, useMemo } from 'react';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, CartesianGrid, LineChart, Line } from 'recharts';
import { MOCK_CATEGORIES } from '../mockData';
import { Category } from '../types';

const CategoriesView: React.FC = () => {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['cat-household', 'cat-food', 'cat-shopping']));
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>('sub-home');

  const selectedCategory = useMemo(() => {
    let found: Category | null = null;
    MOCK_CATEGORIES.forEach(c => {
      if (c.id === selectedCategoryId) found = c;
      c.subCategories?.forEach(s => {
        if (s.id === selectedCategoryId) found = s;
      });
    });
    return found;
  }, [selectedCategoryId]);

  const toggleExpand = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const next = new Set(expandedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setExpandedIds(next);
  };

  const totalBudget = MOCK_CATEGORIES.reduce((acc, c) => acc + c.budget, 0);
  const totalSpent = MOCK_CATEGORIES.reduce((acc, c) => acc + c.spent, 0);

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Center Pane: Category List */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <h1 className="text-sm font-bold text-gray-300">Categories</h1>
          <button className="text-gray-500 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
          {/* Summary Card */}
          <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-10 flex items-center justify-between shadow-2xl relative overflow-hidden group">
             <div className="flex-1 text-center">
                <div className="text-3xl font-black text-white">$0</div>
                <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">spent in Jan</div>
             </div>
             <div className="relative w-24 h-24 shrink-0 mx-8">
                <div className="absolute inset-0 rounded-full border-[8px] border-white/5" />
                <div className="absolute inset-0 rounded-full border-[8px] border-blue-500/20" />
             </div>
             <div className="flex-1 text-center">
                <div className="text-3xl font-black text-white">${totalBudget.toLocaleString()}</div>
                <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">total budget</div>
             </div>
          </div>

          <div className="mb-10">
             <div className="flex items-center justify-between px-4 mb-4">
                <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">
                   <svg className="w-3.5 h-3.5 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"></path></svg>
                   Regular categories
                </h2>
                <div className="flex space-x-20 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                   <span className="w-16">Spent</span>
                   <span className="w-16 text-right">Budget</span>
                </div>
             </div>

             <div className="space-y-1">
                {MOCK_CATEGORIES.map(category => (
                   <div key={category.id} className="space-y-1">
                      <div 
                        onClick={() => setSelectedCategoryId(category.id)}
                        className={`flex items-center px-4 py-3.5 rounded-xl cursor-pointer transition-all ${
                          selectedCategoryId === category.id ? 'bg-blue-500/10 ring-1 ring-blue-500/20' : 'hover:bg-white/5'
                        }`}
                      >
                         <div className="flex items-center flex-1 min-w-0">
                            {category.subCategories ? (
                               <button 
                                 onClick={(e) => toggleExpand(category.id, e)}
                                 className={`mr-2 transition-transform duration-200 ${expandedIds.has(category.id) ? 'rotate-180' : ''}`}
                               >
                                  <svg className="w-3.5 h-3.5 text-gray-600" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg>
                               </button>
                            ) : <div className="w-5.5 mr-2" />}
                            
                            {category.subCategories && (
                               <div className="w-5 h-5 rounded bg-gray-800 flex items-center justify-center text-[10px] font-black text-gray-400 mr-3">
                                  {category.subCategories.length}
                               </div>
                            )}
                            <span className="text-sm font-bold text-white truncate">{category.name}</span>
                         </div>

                         <div className="flex items-center space-x-6 shrink-0">
                            <span className="text-sm font-bold text-white tabular-nums w-16">${category.spent}</span>
                            <div className="w-32 h-2 bg-white/5 rounded-full overflow-hidden">
                               <div className="h-full bg-blue-500/30 rounded-full" style={{ width: `${(category.spent/category.budget)*100}%` }} />
                            </div>
                            <span className="text-sm font-bold text-gray-500 tabular-nums w-16 text-right">${category.budget.toLocaleString()}</span>
                         </div>
                      </div>

                      {expandedIds.has(category.id) && category.subCategories && (
                         <div className="ml-10 space-y-1 relative before:absolute before:left-0 before:top-0 before:bottom-0 before:w-0.5 before:bg-white/5">
                            {category.subCategories.map(sub => (
                               <div 
                                 key={sub.id} 
                                 onClick={() => setSelectedCategoryId(sub.id)}
                                 className={`flex items-center pl-8 pr-4 py-3.5 rounded-xl cursor-pointer transition-all ${
                                   selectedCategoryId === sub.id ? 'bg-blue-500/10 ring-1 ring-blue-500/20' : 'hover:bg-white/5'
                                 }`}
                               >
                                  <div className="flex items-center flex-1 min-w-0">
                                     <span className="mr-3 text-lg">{sub.icon}</span>
                                     <span className="text-sm font-bold text-gray-300 truncate">{sub.name}</span>
                                  </div>
                                  <div className="flex items-center space-x-6 shrink-0">
                                     <span className="text-sm font-bold text-gray-400 tabular-nums w-16">${sub.spent}</span>
                                     <div className="w-32 h-2 bg-white/5 rounded-full overflow-hidden">
                                        <div className="h-full bg-blue-500/20 rounded-full" style={{ width: `${(sub.spent/sub.budget)*100}%` }} />
                                     </div>
                                     <span className="text-sm font-bold text-gray-600 tabular-nums w-16 text-right">${sub.budget.toLocaleString()}</span>
                                  </div>
                               </div>
                            ))}
                         </div>
                      )}
                   </div>
                ))}
             </div>
          </div>
        </div>
      </div>

      {/* Right Pane: Category Deep Dive */}
      <div className="w-[450px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar border-l border-white/5">
        {selectedCategory ? (
          <div className="p-8">
             <div className="flex justify-between items-center mb-10">
                <h3 className="text-sm font-bold text-white">Category</h3>
                <div className="flex space-x-2">
                   <button className="bg-white/5 hover:bg-white/10 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all">Edit budget</button>
                   <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500"><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z"></path></svg></button>
                   <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg></button>
                </div>
             </div>

             <div className="mb-12">
                <div className="flex items-center mb-4">
                   <div className="w-8 h-8 rounded-lg bg-orange-500/10 flex items-center justify-center text-lg mr-3 shadow-lg">{selectedCategory.icon}</div>
                   <h2 className="text-3xl font-black text-white tracking-tight">{selectedCategory.name}</h2>
                </div>
                <div className="flex items-baseline justify-between mb-2">
                   <span className="text-xs font-bold text-gray-500 uppercase tracking-widest">Spent in Jan</span>
                   <div className="text-right">
                      <div className="text-3xl font-black text-white tabular-nums tracking-tighter">$0.00</div>
                      <div className="text-xs font-bold text-blue-400 mt-1">${selectedCategory.budget.toFixed(2)} left</div>
                   </div>
                </div>
             </div>

             {/* Spending Trend Chart */}
             <div className="h-[180px] -mx-8 mb-10 relative">
                <ResponsiveContainer width="100%" height="100%">
                   <AreaChart data={selectedCategory.history || []}>
                      <defs>
                        <linearGradient id="catTrendGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#22c55e" stopOpacity={0.15}/>
                          <stop offset="100%" stopColor="#22c55e" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                      <XAxis dataKey="date" hide />
                      <YAxis hide />
                      <Area type="monotone" dataKey="value" stroke="#22c55e" strokeWidth={3} fill="url(#catTrendGrad)" dot={{r:3, fill: '#22c55e'}} />
                   </AreaChart>
                </ResponsiveContainer>
                <div className="absolute top-0 right-8 px-2 py-0.5 bg-gray-900 border border-white/5 rounded text-[10px] font-black text-white">$151.89</div>
                <div className="flex justify-between px-8 mt-4 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                   <span>Jul 2024</span>
                   <span>Oct</span>
                   <span>Jan 2025</span>
                   <span>Apr</span>
                   <span>Jul</span>
                   <span>Oct</span>
                   <span>Jan 2026</span>
                </div>
             </div>

             {/* Key Metrics Table */}
             <div className="mb-12">
                <div className="flex justify-between items-center mb-6">
                   <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest flex items-center">Key metrics <div className="ml-2 w-3.5 h-3.5 rounded-full border border-gray-700 flex items-center justify-center text-[8px] font-bold">i</div></h4>
                   <div className="flex space-x-12 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                      <span className="w-24 text-right">Spent per year</span>
                      <span className="w-20 text-right">Avg monthly</span>
                   </div>
                </div>
                <div className="space-y-4">
                   {selectedCategory.metrics?.map(m => (
                      <div key={m.year} className="flex justify-between items-center">
                         <span className="text-xs font-bold text-blue-400">{m.year}</span>
                         <div className="flex space-x-12 shrink-0">
                            <span className="text-xs font-bold text-white tabular-nums w-24 text-right">${m.spent.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                            <span className="text-xs font-bold text-white tabular-nums w-20 text-right">${m.avgMonthly.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                         </div>
                      </div>
                   ))}
                </div>
             </div>

             {/* History Sections */}
             <div className="space-y-12">
                <div>
                   <div className="flex justify-between items-baseline mb-6">
                      <h4 className="text-sm font-bold text-white">January 2026</h4>
                      <span className="text-sm font-bold text-white tabular-nums">$0.00</span>
                   </div>
                   <div className="text-xs font-bold text-blue-400/60 text-center py-4 border border-dashed border-white/5 rounded-xl">No transactions this month</div>
                </div>
                <div>
                   <div className="flex justify-between items-baseline mb-6">
                      <h4 className="text-sm font-bold text-white">December 2025</h4>
                      <span className="text-sm font-bold text-white tabular-nums">$0.00</span>
                   </div>
                   <div className="text-xs font-bold text-blue-400/60 text-center py-4 border border-dashed border-white/5 rounded-xl">No transactions this month</div>
                </div>
             </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">Select a category to view analysis</div>
        )}
      </div>
    </div>
  );
};

export default CategoriesView;
