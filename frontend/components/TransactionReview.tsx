
import React, { useState } from 'react';
import { MOCK_TRANSACTIONS } from '../mockData';

const TransactionReview: React.FC = () => {
  const [reviewedIds, setReviewedIds] = useState<Set<string>>(new Set());

  const toggleReview = (id: string) => {
    const next = new Set(reviewedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setReviewedIds(next);
  };

  const grouped = MOCK_TRANSACTIONS.reduce((acc, tx) => {
    if (!acc[tx.date]) acc[tx.date] = [];
    acc[tx.date].push(tx);
    return acc;
  }, {} as Record<string, typeof MOCK_TRANSACTIONS>);

  return (
    <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 flex flex-col h-full relative">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-sm font-semibold text-gray-400">Transactions to review</h2>
        <button className="text-[11px] font-semibold text-blue-400 hover:text-blue-300 transition-colors flex items-center">
          View all <svg className="w-3.5 h-3.5 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7"></path></svg>
        </button>
      </div>

      <div className="flex-1 space-y-8 overflow-y-auto pr-2 custom-scrollbar pb-24">
        {Object.entries(grouped).map(([date, txs]) => (
          <div key={date}>
            <h3 className="text-[10px] font-bold text-gray-600 uppercase tracking-widest mb-5">{date}</h3>
            <div className="space-y-5">
              {txs.map(tx => (
                <div 
                  key={tx.id} 
                  className="flex items-center group cursor-pointer"
                  onClick={() => toggleReview(tx.id)}
                >
                  <div className={`w-5 h-5 rounded-full border-2 mr-5 flex items-center justify-center transition-all ${reviewedIds.has(tx.id) ? 'bg-[#3b82f6] border-[#3b82f6]' : 'border-gray-800 group-hover:border-gray-600'}`}>
                    {reviewedIds.has(tx.id) && <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="4" d="M5 13l4 4L19 7"></path></svg>}
                  </div>
                  
                  <div className="flex-1 flex items-center justify-between">
                    <div className="flex items-center min-w-0">
                       <span className={`text-[13px] font-semibold mr-3 transition-colors ${reviewedIds.has(tx.id) ? 'text-gray-600 line-through' : 'text-gray-300'}`}>
                         {tx.recurring && <span className="mr-2 text-blue-500 font-bold opacity-80">🅁</span>}
                         {tx.merchant}
                       </span>
                    </div>
                    
                    <div className="flex items-center space-x-6">
                      <span className={`px-2.5 py-1 rounded-md text-[9px] font-bold uppercase tracking-widest flex items-center ${reviewedIds.has(tx.id) ? 'opacity-30' : ''} ${
                        tx.category === 'SUBSCRIPTION' ? 'bg-[#0f2e2d] text-[#10b981]' : 
                        tx.category === 'GROCERIES' ? 'bg-[#122b12] text-[#22c55e]' : 
                        tx.category === 'TRANSIT' ? 'bg-[#1e2a3b] text-[#3b82f6]' : 
                        'bg-[#2d1b1b] text-[#ef4444]'
                      }`}>
                        {tx.category === 'GROCERIES' && <span className="mr-1.5">🥑</span>}
                        {tx.category === 'SUBSCRIPTION' && <span className="mr-1.5 text-[8px]">💳</span>}
                        {tx.category}
                      </span>
                      <span className={`text-[13px] font-bold tabular-nums transition-colors ${reviewedIds.has(tx.id) ? 'text-gray-600' : 'text-white'}`}>
                        ${tx.amount.toFixed(2)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="absolute bottom-6 left-6 right-6">
         <button className="w-full bg-[#0a0f1d] border border-white/10 hover:border-white/20 text-white text-[11px] font-bold uppercase tracking-wider py-3.5 rounded-xl transition-all flex items-center justify-center shadow-xl shadow-black/40">
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7"></path></svg>
            Mark 6 as reviewed
         </button>
      </div>
    </div>
  );
};

export default TransactionReview;
