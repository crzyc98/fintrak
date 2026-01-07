
import React from 'react';
import { MOCK_RECURRING } from '../mockData';

const UpcomingRecurrings: React.FC = () => {
  return (
    <div className="bg-[#151b28] border border-gray-800/60 rounded-[24px] p-7 shadow-xl shadow-black/20">
      <div className="flex justify-between items-center mb-8">
        <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Next two weeks</h2>
        <button className="text-[10px] font-bold text-gray-600 hover:text-gray-300 uppercase tracking-widest transition-colors">Recurrings ↗</button>
      </div>

      <div className="space-y-6">
        {MOCK_RECURRING.map(item => {
          const date = new Date(item.dueDate);
          const month = date.toLocaleDateString('en-US', { month: 'short' }).toUpperCase();
          const day = date.toLocaleDateString('en-US', { day: 'numeric' });
          
          return (
            <div key={item.id} className="flex items-center justify-between group cursor-pointer hover:bg-gray-800/20 -mx-3 px-3 py-2 rounded-2xl transition-all">
              <div className="flex items-center min-w-0">
                <div className="flex flex-col items-center justify-center w-12 h-12 rounded-xl bg-gray-800/50 border border-gray-700/30 mr-4 shrink-0 shadow-inner">
                  <span className="text-[8px] font-black text-gray-500 leading-none mb-0.5">{month}</span>
                  <span className="text-lg font-black text-gray-100 leading-none">{day}</span>
                </div>
                <div className="flex flex-col min-w-0">
                  <div className="flex items-center">
                    <span className="text-sm font-bold text-gray-100 truncate mr-2">{item.name}</span>
                    {/* Fixed: Changed 'item.color' to 'item.categoryColor' as 'color' does not exist on the RecurringItem type */}
                    <div className={`w-2 h-2 rounded-full ${item.categoryColor} shadow-sm shadow-black/40`}></div>
                  </div>
                  <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest mt-1">{item.type}</span>
                </div>
              </div>
              <span className="text-sm font-black text-white ml-4 tabular-nums">${item.amount.toLocaleString()}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default UpcomingRecurrings;
