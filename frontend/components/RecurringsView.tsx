
import React, { useState, useMemo } from 'react';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, CartesianGrid } from 'recharts';
import { MOCK_RECURRING } from '../mockData';
import { RecurringItem } from '../types';

const RecurringsView: React.FC = () => {
  const [selectedRecurringId, setSelectedRecurringId] = useState<string | null>('rec-youtube');

  const selectedItem = useMemo(() => 
    MOCK_RECURRING.find(r => r.id === selectedRecurringId), 
  [selectedRecurringId]);

  const leftToPay = MOCK_RECURRING.filter(r => r.status === 'Overdue').reduce((acc, r) => acc + r.amount, 0);
  const paidSoFar = MOCK_RECURRING.filter(r => r.status === 'Paid').reduce((acc, r) => acc + r.amount, 0);

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Main List Area */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <h1 className="text-sm font-bold text-gray-300">Recurrings</h1>
          <button className="text-gray-500 hover:text-white transition-colors">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4"></path></svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
          {/* Tracker Hero Card */}
          <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-10 flex items-center justify-between shadow-2xl relative overflow-hidden">
             <div className="flex-1 text-center">
                <div className="text-3xl font-black text-white">${leftToPay.toLocaleString(undefined, {minimumFractionDigits: 0})}</div>
                <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">left to pay</div>
             </div>
             <div className="relative w-28 h-28 shrink-0 mx-8">
                <div className="absolute inset-0 rounded-full border-[10px] border-white/5" />
                <div className="absolute inset-0 rounded-full border-[10px] border-blue-500/20" />
             </div>
             <div className="flex-1 text-center">
                <div className="text-3xl font-black text-white">${paidSoFar.toLocaleString(undefined, {minimumFractionDigits: 0})}</div>
                <div className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mt-1">paid so far</div>
             </div>
          </div>

          <div>
             <div className="flex items-center justify-between px-4 mb-6">
                <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">
                   <svg className="w-3.5 h-3.5 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"></path></svg>
                   This month
                </h2>
             </div>

             <div className="space-y-1">
                {MOCK_RECURRING.map(item => (
                   <div 
                    key={item.id} 
                    onClick={() => setSelectedRecurringId(item.id)}
                    className={`flex items-center px-4 py-3.5 rounded-xl cursor-pointer transition-all ${
                      selectedRecurringId === item.id ? 'bg-blue-500/10 ring-1 ring-blue-500/20' : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="w-20 shrink-0">
                       <span className={`text-[11px] font-bold ${item.status === 'Overdue' ? 'text-blue-500/80' : 'text-gray-600'}`}>
                         {item.status}
                       </span>
                    </div>
                    
                    <div className="flex items-center flex-1 min-w-0 mr-4">
                       <div className="w-8 h-8 rounded-lg bg-gray-800 flex items-center justify-center text-lg mr-3 shadow-inner">
                         {item.icon}
                       </div>
                       <div className="flex flex-col min-w-0">
                          <span className="text-sm font-bold text-white truncate">{item.name}</span>
                          <span className="text-[10px] font-bold text-blue-400/70">{item.frequency}</span>
                       </div>
                    </div>

                    <div className="flex items-center space-x-8 shrink-0">
                       <div className={`px-2 py-0.5 rounded text-[9px] font-black tracking-widest ${item.categoryColor}`}>
                         {item.category}
                       </div>
                       <div className="text-sm font-bold text-white tabular-nums w-20 text-right">
                         ${item.amount.toLocaleString(undefined, {minimumFractionDigits: 2})}
                       </div>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        </div>
      </div>

      {/* Right Detail Pane */}
      <div className="w-[450px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar border-l border-white/5">
        {selectedItem ? (
          <div className="p-8">
             <div className="flex justify-between items-center mb-10">
                <h3 className="text-sm font-bold text-white">Monthly recurring</h3>
                <div className="flex space-x-2">
                   <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500 transition-colors"><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z"></path></svg></button>
                   <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500 transition-colors"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg></button>
                </div>
             </div>

             <div className="mb-12">
                <div className={`inline-flex px-2 py-0.5 rounded text-[9px] font-black tracking-widest mb-3 ${selectedItem.categoryColor}`}>
                  {selectedItem.category}
                </div>
                <div className="flex items-center justify-between mb-2">
                   <div className="flex items-center">
                      <div className="w-10 h-10 rounded-xl bg-gray-800 flex items-center justify-center text-xl mr-4 shadow-xl">{selectedItem.icon}</div>
                      <h2 className="text-3xl font-black text-white tracking-tight">{selectedItem.name}</h2>
                   </div>
                   <div className="text-right">
                      <div className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-1">Next payment</div>
                      <div className="text-2xl font-black text-white tabular-nums tracking-tighter">${selectedItem.amount.toFixed(2)}</div>
                      <div className="text-[10px] font-bold text-gray-600 mt-1">around <span className="text-gray-300">{selectedItem.dueDate}</span></div>
                   </div>
                </div>
             </div>

             {/* Rules Section */}
             <div className="mb-12">
                <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-4">Rules</h4>
                <div className="flex flex-wrap gap-2">
                   {selectedItem.rules ? (
                     <>
                        <div className="bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-400 flex items-center">
                           named <span className="text-gray-100 ml-1">{selectedItem.rules.name}</span>
                        </div>
                        <div className="bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-400 flex items-center">
                           from <span className="text-gray-100 ml-1.5 mr-1.5">${selectedItem.rules.minAmount.toFixed(2)}</span> to <span className="text-gray-100 ml-1.5">${selectedItem.rules.maxAmount.toFixed(2)}</span>
                        </div>
                        <div className="bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-400 flex items-center">
                           every <span className="text-gray-100 ml-1">{selectedItem.rules.frequency}</span>
                        </div>
                        <div className="bg-blue-500/10 border border-blue-500/20 px-3 py-1.5 rounded-lg text-xs font-bold text-blue-400 flex items-center">
                           on <span className="text-gray-100 ml-1">{selectedItem.rules.dayOfMonth}</span>
                        </div>
                     </>
                   ) : (
                     <div className="text-xs font-bold text-gray-600">No rules defined for this recurring payment.</div>
                   )}
                </div>
             </div>

             {/* Spending Trend Chart */}
             <div className="h-[180px] -mx-8 mb-10 relative">
                <ResponsiveContainer width="100%" height="100%">
                   <AreaChart data={selectedItem.history || []}>
                      <defs>
                        <linearGradient id="recTrendGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#ec4899" stopOpacity={0.15}/>
                          <stop offset="100%" stopColor="#ec4899" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
                      <XAxis dataKey="date" hide />
                      <YAxis hide />
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#ec4899" 
                        strokeWidth={3} 
                        fill="url(#recTrendGrad)" 
                        dot={(props: any) => {
                          const isLast = props.index === (selectedItem.history?.length || 0) - 1;
                          return isLast ? (
                            <circle cx={props.cx} cy={props.cy} r={6} fill="#ec4899" stroke="#050910" strokeWidth={3} />
                          ) : (
                            <circle cx={props.cx} cy={props.cy} r={3} fill="#ec4899" />
                          );
                        }} 
                      />
                   </AreaChart>
                </ResponsiveContainer>
                <div className="absolute top-0 right-8 px-2 py-0.5 bg-gray-900 border border-white/5 rounded text-[10px] font-black text-white">${selectedItem.amount.toFixed(2)}</div>
                <div className="flex justify-between px-8 mt-4 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                   <span>Jun 2022</span>
                   <span>Oct</span>
                   <span>Jan 2023</span>
                   <span>May 2023</span>
                </div>
             </div>

             {/* Key Metrics Table */}
             <div className="mb-12">
                <div className="flex justify-between items-center mb-6">
                   <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest flex items-center">Key metrics</h4>
                   <div className="flex space-x-12 text-[10px] font-black text-gray-600 uppercase tracking-widest">
                      <span className="w-24 text-right">Spent per year</span>
                      <span className="w-24 text-right">Avg transaction</span>
                   </div>
                </div>
                <div className="space-y-4">
                   {selectedItem.metrics?.map(m => (
                      <div key={m.year} className="flex justify-between items-center">
                         <span className="text-xs font-bold text-blue-400">{m.year}</span>
                         <div className="flex space-x-12 shrink-0">
                            <span className="text-xs font-bold text-white tabular-nums w-24 text-right">${m.spent.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                            <span className="text-xs font-bold text-white tabular-nums w-24 text-right">${m.avgTransaction.toLocaleString(undefined, {minimumFractionDigits: 2})}</span>
                         </div>
                      </div>
                   ))}
                </div>
             </div>

             {/* Last Account Used */}
             {selectedItem.lastAccount && (
               <div>
                  <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest mb-6">Last account used</h4>
                  <div className="flex items-center p-4 bg-white/5 rounded-2xl border border-white/5">
                     <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center mr-4">
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20"><path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4zM18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM5 13a1 1 0 112 0 1 1 0 01-2 0zm7 0a1 1 0 112 0 1 1 0 01-2 0z"></path></svg>
                     </div>
                     <div className="flex flex-col flex-1">
                        <span className="text-sm font-bold text-white">{selectedItem.lastAccount.name}</span>
                        <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mt-0.5">**** {selectedItem.lastAccount.lastFour}</span>
                     </div>
                     <div className="text-right">
                        <span className="text-sm font-bold text-white">${selectedItem.amount.toFixed(2)}</span>
                     </div>
                  </div>
               </div>
             )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">Select a recurring payment to view details</div>
        )}
      </div>
    </div>
  );
};

export default RecurringsView;
