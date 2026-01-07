
import React, { useState, useMemo } from 'react';
import { MOCK_TRANSACTIONS } from '../mockData';
import { Transaction } from '../types';

const TransactionsView: React.FC = () => {
  const [selectedTxId, setSelectedTxId] = useState<string | null>('t2'); // YouTube TV selected by default for demo
  const [searchQuery, setSearchQuery] = useState('');

  const selectedTx = useMemo(() => 
    MOCK_TRANSACTIONS.find(t => t.id === selectedTxId), 
  [selectedTxId]);

  // Simple grouping: Month -> Date -> Txs
  const groupedTransactions = useMemo(() => {
    const months: Record<string, Record<string, Transaction[]>> = {};
    MOCK_TRANSACTIONS.forEach(tx => {
      if (!months[tx.month]) months[tx.month] = {};
      if (!months[tx.month][tx.displayDate]) months[tx.month][tx.displayDate] = [];
      months[tx.month][tx.displayDate].push(tx);
    });
    return months;
  }, []);

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Main List Area */}
      <div className={`flex-1 flex flex-col min-w-0 border-r border-white/5`}>
        {/* Header toolbar */}
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center space-x-4">
             <div className="flex items-center text-sm font-semibold text-gray-300">
               <input type="checkbox" className="mr-3 w-4 h-4 bg-transparent border-white/20 rounded" />
               Transactions
             </div>
          </div>
          <div className="flex items-center space-x-4">
            <button className="text-gray-500 hover:text-white"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg></button>
            <button className="text-gray-500 hover:text-white"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg></button>
            <div className="relative">
              <input 
                type="text" 
                placeholder="Search" 
                className="bg-[#0a0f1d] border border-white/5 rounded-lg pl-8 pr-4 py-1.5 text-xs font-medium w-48 focus:w-64 transition-all focus:outline-none"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <svg className="w-4 h-4 absolute left-2.5 top-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
            </div>
            <button className="text-gray-500 hover:text-white"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16m-7 6h7"></path></svg></button>
          </div>
        </div>

        {/* Scrollable Feed */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-8 py-6">
          {Object.entries(groupedTransactions).map(([month, dates]) => (
            <div key={month} className="mb-10">
              <div className="flex justify-between items-baseline mb-4">
                <h2 className="text-2xl font-bold text-white tracking-tight">{month}</h2>
                <span className="text-xl font-bold text-white tabular-nums">$1,901.67</span>
              </div>
              
              {Object.entries(dates).map(([date, txs]) => (
                <div key={date} className="mb-6">
                  <h3 className="text-[11px] font-bold text-blue-400/80 mb-4">{date}</h3>
                  <div className="space-y-1">
                    {txs.map(tx => (
                      <div 
                        key={tx.id} 
                        onClick={() => setSelectedTxId(tx.id)}
                        className={`group relative flex items-center px-4 py-3 rounded-lg cursor-pointer transition-all ${
                          selectedTxId === tx.id ? 'bg-[#3b82f6]/10' : 'hover:bg-white/5'
                        }`}
                      >
                        {selectedTxId === tx.id && (
                          <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-blue-500 rounded-full" />
                        )}
                        <input type="checkbox" className="mr-4 w-4 h-4 bg-transparent border-white/10 rounded cursor-pointer" onClick={(e) => e.stopPropagation()} />
                        <div className="flex-1 flex items-center justify-between min-w-0 pr-4">
                          <div className="flex flex-col min-w-0">
                            <div className="flex items-center">
                              <span className="text-sm font-semibold text-gray-100 truncate mr-2">{tx.merchant}</span>
                              <span className="text-xs font-medium text-gray-500 truncate">{tx.accountName}</span>
                            </div>
                          </div>
                          <div className="flex items-center space-x-6">
                             <div className={`flex items-center px-2 py-0.5 rounded-full text-[10px] font-black tracking-widest ${tx.categoryColor}`}>
                               <span className="mr-1">{tx.categoryIcon || '🔹'}</span>
                               {tx.category}
                             </div>
                             <div className="flex items-center">
                               <span className={`text-sm font-bold tabular-nums ${tx.amount > 0 ? 'text-green-500' : 'text-white'}`}>
                                 {tx.amount > 0 ? `$${tx.amount.toFixed(2)}` : `$${Math.abs(tx.amount).toFixed(2)}`}
                               </span>
                               <div className="ml-3 flex space-x-0.5">
                                 <div className="w-1 h-1 rounded-full bg-blue-500/50" />
                                 <div className="w-1 h-1 rounded-full bg-blue-500/50" />
                               </div>
                             </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* Right Detail Pane */}
      <div className="w-[400px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar">
        {selectedTx ? (
          <div className="p-8">
            <div className="flex justify-between items-center mb-8">
              <span className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Recurring transaction</span>
              <div className="flex space-x-2">
                <button className="p-1.5 hover:bg-white/5 rounded-lg text-gray-500"><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z"></path></svg></button>
                <button className="bg-[#3b82f6] text-white px-4 py-1.5 rounded-lg text-xs font-bold shadow-lg shadow-blue-500/20">Review</button>
              </div>
            </div>

            <div className="mb-10">
              <span className="text-[11px] font-bold text-blue-400 mb-2 block">{selectedTx.displayDate}</span>
              <h3 className="text-3xl font-black text-white mb-2 tracking-tight">{selectedTx.merchant}</h3>
              <div className="flex items-center text-gray-400 mb-4">
                <div className="w-4 h-4 rounded-full bg-blue-500/40 mr-2" />
                <span className="text-sm font-semibold">{selectedTx.accountName}</span>
              </div>
              <div className="text-3xl font-black text-white tracking-tighter">
                ${Math.abs(selectedTx.amount).toFixed(2)}
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-center justify-between group cursor-pointer p-2 -m-2 hover:bg-white/5 rounded-xl">
                 <span className="text-sm font-semibold text-gray-500">Category</span>
                 <div className={`flex items-center px-3 py-1 rounded-full text-[10px] font-black tracking-widest ${selectedTx.categoryColor}`}>
                    <span className="mr-1.5">{selectedTx.categoryIcon}</span>
                    {selectedTx.category}
                    <svg className="w-3 h-3 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M9 5l7 7-7 7"></path></svg>
                 </div>
              </div>
              
              <div className="flex items-center justify-between group cursor-pointer p-2 -m-2 hover:bg-white/5 rounded-xl">
                 <span className="text-sm font-semibold text-gray-500">Recurring</span>
                 <div className="flex items-center text-xs font-bold text-gray-300">
                    <span className="bg-gray-800/50 p-1 rounded mr-2">🅁</span>
                    {selectedTx.merchant}
                    <svg className="w-3 h-3 ml-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M9 5l7 7-7 7"></path></svg>
                 </div>
              </div>

              <div className="flex items-center justify-between group cursor-pointer p-2 -m-2 hover:bg-white/5 rounded-xl">
                 <span className="text-sm font-semibold text-gray-500">Tags</span>
                 <button className="w-6 h-6 rounded-full border border-dashed border-gray-700 flex items-center justify-center text-gray-500 hover:border-gray-500">+</button>
              </div>

              <div className="pt-4">
                <textarea 
                  placeholder="Add a note..." 
                  className="w-full bg-transparent border-none p-0 text-sm font-medium text-gray-300 focus:ring-0 placeholder-gray-700 resize-none h-24"
                />
              </div>
            </div>

            {/* Transaction History Section */}
            <div className="mt-12 border-t border-white/5 pt-8">
              <div className="flex justify-between items-baseline mb-6">
                <h4 className="text-sm font-bold text-white tracking-tight">March 2023</h4>
                <span className="text-sm font-bold text-white tabular-nums">$139.08</span>
              </div>
              <div className="space-y-6">
                <div className="text-[10px] font-bold text-blue-400/80 mb-4 uppercase tracking-widest">Wednesday, March 29</div>
                <div className="flex items-center justify-between">
                   <div className="flex items-center">
                     <input type="checkbox" className="mr-4 w-4 h-4 bg-transparent border-white/10 rounded" />
                     <div className="flex flex-col">
                       <span className="text-sm font-bold text-gray-200">{selectedTx.merchant}</span>
                     </div>
                   </div>
                   <div className="flex items-center space-x-4">
                      <div className="bg-pink-500/10 text-pink-400 text-[9px] font-black px-2 py-0.5 rounded-full tracking-widest flex items-center">
                        🛍️ SHOP...
                      </div>
                      <span className="text-sm font-bold text-white tabular-nums">$69.54</span>
                      <div className="w-1 h-1 rounded-full bg-blue-500/50" />
                   </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">
            Select a transaction to review details
          </div>
        )}
      </div>
    </div>
  );
};

export default TransactionsView;
