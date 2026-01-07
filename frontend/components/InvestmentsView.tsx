
import React, { useState, useMemo } from 'react';
import { AreaChart, Area, ResponsiveContainer, LineChart, Line, XAxis, YAxis } from 'recharts';
import { MOCK_ACCOUNTS, TOP_MOVERS, LIVE_BALANCE_HISTORY } from '../mockData';
import { Account } from '../types';

const InvestmentsView: React.FC = () => {
  const [selectedAccountId, setSelectedAccountId] = useState<string | null>('4');
  const [timeframe, setTimeframe] = useState('ALL');

  const selectedAccount = useMemo(() => 
    MOCK_ACCOUNTS.find(a => a.id === selectedAccountId), 
  [selectedAccountId]);

  const investmentAccounts = useMemo(() => 
    MOCK_ACCOUNTS.filter(a => a.type === 'Investment'), 
  []);

  // Split history into actual and estimate segments for dotted effect
  const chartData = useMemo(() => {
    return LIVE_BALANCE_HISTORY;
  }, []);

  return (
    <div className="flex h-full -mt-4 -mx-10 overflow-hidden bg-[#050910]">
      {/* Center Pane: Overview */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-white/5">
        <div className="px-8 py-4 flex items-center justify-between border-b border-white/5">
          <h1 className="text-sm font-bold text-gray-300">Investments</h1>
          <div className="flex space-x-4">
             <button className="text-gray-500 hover:text-white transition-colors"><svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4h16M4 12h16m-7 6h7"></path></svg></button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar p-8">
          {/* Live Balance Estimate Hero Card */}
          <div className="bg-[#0a0f1d] border border-white/5 rounded-3xl p-8 mb-10 relative overflow-hidden shadow-2xl group">
             <div className="text-center relative z-10">
                <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2">Live balance estimate</h3>
                <div className="flex items-center justify-center space-x-2 mb-1">
                   <div className="text-4xl font-black text-white">$2,119,906</div>
                   <div className="w-4 h-4 rounded-full border border-gray-600 flex items-center justify-center text-[10px] text-gray-500 font-bold">i</div>
                </div>
                <div className="inline-flex items-center text-xs font-black text-green-500 bg-green-500/10 px-2 py-0.5 rounded">↗ 0.00%</div>
             </div>

             <div className="h-[240px] mt-4 -mx-8">
                <ResponsiveContainer width="100%" height="100%">
                   <AreaChart data={chartData} margin={{top: 0, right: 30, left: 30, bottom: 0}}>
                      <defs>
                        <linearGradient id="liveGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#22c55e" stopOpacity={0.15}/>
                          <stop offset="100%" stopColor="#22c55e" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#22c55e" 
                        strokeWidth={3} 
                        fill="url(#liveGrad)" 
                        dot={(props: any) => {
                           if (props.payload.estimate) {
                              return <circle cx={props.cx} cy={props.cy} r={4} fill="#22c55e" stroke="#0a0f1d" strokeWidth={2} />;
                           }
                           return null;
                        }}
                      />
                      {/* Dotted estimate segment - purely visual for the last point */}
                      <Line 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#22c55e" 
                        strokeWidth={3} 
                        strokeDasharray="5 5" 
                        dot={false}
                        connectNulls
                      />
                   </AreaChart>
                </ResponsiveContainer>
             </div>

             <div className="flex justify-center space-x-6 mt-4">
                {['1W', '1M', '3M', 'YTD', '1Y', 'ALL'].map(f => (
                  <button key={f} className={`text-[10px] font-black tracking-widest ${f === '1W' ? 'text-white bg-white/10 px-2.5 py-1 rounded-full' : 'text-gray-600'}`}>{f}</button>
                ))}
             </div>
          </div>

          {/* Top Movers Section */}
          <div className="mb-10">
             <div className="flex justify-between items-center mb-6">
                <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">
                   <svg className="w-3.5 h-3.5 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"></path></svg>
                   Your top movers for today
                </h2>
                <button className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center">Last Price <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg></button>
             </div>
             
             <div className="flex space-x-4 overflow-x-auto pb-4 custom-scrollbar">
                {TOP_MOVERS.map(mover => (
                   <div key={mover.symbol} className="min-w-[140px] bg-[#0a0f1d] border border-white/5 rounded-2xl p-4 shadow-xl">
                      <div className="flex flex-col mb-4">
                         <span className="text-[11px] font-black text-white mb-0.5">{mover.symbol}</span>
                         <span className="text-[10px] font-bold text-gray-500">{mover.name}</span>
                      </div>
                      <div className="h-10 mb-4">
                         <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={mover.sparkline}>
                               <Line type="monotone" dataKey="val" stroke="#22c55e" strokeWidth={2} dot={false} />
                            </LineChart>
                         </ResponsiveContainer>
                      </div>
                      <div className="inline-flex items-center text-[10px] font-black text-green-500 bg-green-500/10 px-2 py-0.5 rounded">↗ {mover.changePercent}%</div>
                   </div>
                ))}
             </div>
          </div>

          {/* Accounts List */}
          <div>
             <div className="flex justify-between items-center mb-6">
                <h2 className="flex items-center text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">
                   <svg className="w-3.5 h-3.5 mr-2 rotate-90" fill="currentColor" viewBox="0 0 20 20"><path d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"></path></svg>
                   Accounts
                </h2>
                <button className="text-[10px] font-black text-gray-500 uppercase tracking-widest flex items-center">1W Balance Change <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg></button>
             </div>
             
             <div className="space-y-1">
                {investmentAccounts.map(account => (
                   <div 
                    key={account.id} 
                    onClick={() => setSelectedAccountId(account.id)}
                    className={`flex items-center px-4 py-4 rounded-xl cursor-pointer transition-all ${
                      selectedAccountId === account.id ? 'bg-blue-500/10 ring-1 ring-blue-500/20' : 'hover:bg-white/5'
                    }`}
                  >
                    <div className={`w-10 h-10 rounded-full ${account.logoColor || 'bg-gray-800'} flex items-center justify-center text-white font-bold text-xs mr-4 shrink-0 overflow-hidden`}>
                      {account.name.includes('Ethereum') ? <span className="text-xl">⟠</span> : account.name.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0 pr-4">
                       <div className="flex items-center">
                         <span className="text-sm font-bold text-white truncate mr-2">{account.name}</span>
                       </div>
                       <span className="text-[11px] font-semibold text-gray-500">{account.lastSynced}</span>
                    </div>
                    <div className="flex items-center space-x-6 text-right shrink-0">
                       <div className={`px-2 py-0.5 rounded text-[10px] font-black ${account.oneWeekChange === 0 ? 'text-gray-500 bg-gray-500/10' : 'text-green-500 bg-green-500/10'}`}>
                         {account.oneWeekChange && account.oneWeekChange > 0 ? `↗ ${account.oneWeekChange}%` : account.oneWeekChange === 0 ? '= 0.00%' : `↘ ${Math.abs(account.oneWeekChange || 0)}%`}
                       </div>
                       <div className="text-sm font-bold text-white tabular-nums w-24">${account.balance.toLocaleString()}</div>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        </div>
      </div>

      {/* Right Detail Pane */}
      <div className="w-[450px] flex flex-col bg-[#050910] overflow-y-auto custom-scrollbar border-l border-white/5">
        {selectedAccount ? (
          <div className="p-8">
            <div className="flex justify-between items-center mb-10">
               <h3 className="text-sm font-bold text-white">{selectedAccount.name.includes('401k') ? '401k' : 'Brokerage'}</h3>
               <div className="flex space-x-2">
                 <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500"><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M6 10a2 2 0 11-4 0 2 2 0 014 0zM12 10a2 2 0 11-4 0 2 2 0 014 0zM16 12a2 2 0 100-4 2 2 0 000 4z"></path></svg></button>
                 <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500"><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg></button>
               </div>
            </div>

            <div className="mb-8">
               <div className="flex items-center mb-2">
                  <div className={`w-6 h-6 rounded-full ${selectedAccount.logoColor} mr-3 flex items-center justify-center text-[10px] text-white font-bold`}>
                    {selectedAccount.name.includes('Ethereum') ? '⟠' : selectedAccount.name.charAt(0)}
                  </div>
                  <span className="text-xs font-bold text-gray-600">1960</span>
                  <span className="text-xs font-bold text-gray-500 ml-2">{selectedAccount.lastSynced}</span>
               </div>
               <h2 className="text-3xl font-black text-white tracking-tight mb-2">{selectedAccount.name}</h2>
               <div className="flex items-center justify-between">
                  <div className="text-3xl font-black text-white tabular-nums tracking-tighter">${selectedAccount.balance.toLocaleString()}</div>
                  <div className="flex space-x-2">
                    <div className={`text-[10px] font-black px-2 py-0.5 rounded ${selectedAccount.trendPercent >= 0 ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                      {selectedAccount.trendPercent >= 0 ? '+ $11,434' : '— $51,464'}
                    </div>
                    <div className={`text-[10px] font-black px-2 py-0.5 rounded ${selectedAccount.trendPercent >= 0 ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                      {selectedAccount.trendPercent >= 0 ? '↗' : '↘'} {Math.abs(selectedAccount.trendPercent)}%
                    </div>
                  </div>
               </div>
            </div>

            <div className="h-[180px] -mx-8 mb-10">
               <ResponsiveContainer width="100%" height="100%">
                 <AreaChart data={selectedAccount.sparkline}>
                    <defs>
                      <linearGradient id="detailGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={selectedAccount.trendPercent >= 0 ? "#22c55e" : "#ef4444"} stopOpacity={0.2}/>
                        <stop offset="100%" stopColor={selectedAccount.trendPercent >= 0 ? "#22c55e" : "#ef4444"} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <Area 
                        type="stepAfter" 
                        dataKey="val" 
                        stroke={selectedAccount.trendPercent >= 0 ? "#22c55e" : "#ef4444"} 
                        strokeWidth={3} 
                        fill="url(#detailGrad)" 
                    />
                 </AreaChart>
               </ResponsiveContainer>
               <div className="flex justify-center space-x-4 mt-2">
                  {['1W', '1M', '3M', 'YTD', '1Y', 'ALL'].map(f => (
                    <button key={f} className={`text-[10px] font-black tracking-widest ${f === 'ALL' ? 'text-blue-500 bg-blue-500/10 px-2 rounded-full' : 'text-gray-600'}`}>{f}</button>
                  ))}
               </div>
            </div>

            {selectedAccount.allocations && (
              <div className="mb-12">
                <div className="flex justify-between items-center mb-6">
                  <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Allocations</h4>
                  <button className="text-[10px] font-bold text-gray-500 uppercase flex items-center">By Percentage <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg></button>
                </div>
                <div className="space-y-4">
                  {selectedAccount.allocations.map(a => (
                    <div key={a.label} className="flex items-center justify-between">
                       <span className="text-xs font-bold text-gray-400 w-24">{a.label}</span>
                       <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden mx-4">
                          <div className={`h-full ${a.color}`} style={{ width: `${a.percent}%` }} />
                       </div>
                       <span className="text-xs font-bold text-gray-400 w-8 text-right">{a.percent}%</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {selectedAccount.holdings && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Holdings</h4>
                  <button className="text-[10px] font-bold text-gray-500 uppercase flex items-center">Last Price <svg className="w-3 h-3 ml-1" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd"></path></svg></button>
                </div>
                <div className="space-y-6">
                  {selectedAccount.holdings.map(h => (
                    <div key={h.ticker} className="flex items-center justify-between">
                       <div className="flex flex-col min-w-0 pr-4">
                          <span className="text-xs font-black text-blue-400 mb-0.5">{h.ticker}</span>
                          <span className="text-[11px] font-semibold text-gray-400 truncate">{h.name}</span>
                       </div>
                       <div className="flex items-center space-x-6 text-right shrink-0">
                          <div className="bg-blue-500/10 text-blue-400 text-[10px] font-black px-2 py-0.5 rounded">= 0.00%</div>
                          <span className="text-xs font-bold text-white w-16 tabular-nums">${h.value.toFixed(2)}</span>
                       </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-600 text-sm font-medium">Select an account to view details</div>
        )}
      </div>
    </div>
  );
};

export default InvestmentsView;
