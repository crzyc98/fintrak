
import React, { useState } from 'react';
import { LineChart, Line, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { NET_WORTH_DATA } from '../mockData';

const NetWorth: React.FC = () => {
  const [timeframe, setTimeframe] = useState('YTD');
  const frames = ['1W', '1M', '3M', 'YTD', '1Y', 'ALL'];

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#0a0f1d] border border-white/10 p-3 rounded-xl shadow-2xl backdrop-blur-md">
          <div className="space-y-2">
            <div className="flex items-center justify-between space-x-8">
              <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wider">Assets</span>
              <span className="text-sm font-bold text-white">${payload[0].value.toLocaleString()}</span>
            </div>
            <div className="flex items-center justify-between space-x-8">
              <span className="text-[10px] font-bold text-orange-400 uppercase tracking-wider">Debts</span>
              <span className="text-sm font-bold text-white">${payload[1].value.toLocaleString()}</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-[#0a0f1d] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] overflow-hidden relative group shadow-2xl shadow-black/40">
      <div className="flex justify-between items-start mb-6 relative z-10">
        <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Net worth</h2>
        <button className="text-sm font-semibold text-gray-400 hover:text-white transition-colors flex items-center group/btn">
          Accounts 
          <svg className="w-3.5 h-3.5 ml-1 transition-transform group-hover/btn:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7"></path>
          </svg>
        </button>
      </div>

      <div className="flex space-x-12 mb-4 relative z-10">
        <div>
          <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#3b82f6] mr-2 shadow-[0_0_8px_rgba(59,130,246,0.5)]"></div>
            Assets
          </div>
          <div className="text-4xl font-extrabold text-white tracking-tight mb-3">$100,000</div>
          <div className="inline-flex items-center bg-[#10b981]/15 text-[#10b981] text-[10px] font-black px-2 py-0.5 rounded border border-[#10b981]/20 uppercase">
             <svg className="w-3 h-3 mr-0.5" fill="currentColor" viewBox="0 0 20 20"><path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"></path></svg>
             32%
          </div>
        </div>
        <div>
          <div className="flex items-center text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-[#f97316] mr-2 shadow-[0_0_8px_rgba(249,115,22,0.5)]"></div>
            Debts
          </div>
          <div className="text-4xl font-extrabold text-white tracking-tight mb-3">$5,000</div>
          <div className="inline-flex items-center bg-[#ef4444]/15 text-[#ef4444] text-[10px] font-black px-2 py-0.5 rounded border border-[#ef4444]/20 uppercase">
             <svg className="w-3 h-3 mr-0.5 rotate-180" fill="currentColor" viewBox="0 0 20 20"><path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"></path></svg>
             16%
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 relative -mx-8">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={NET_WORTH_DATA} margin={{ top: 20, right: 40, left: 40, bottom: 150 }}>
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.02)" strokeDasharray="3 3" />
            <YAxis yAxisId="left" hide domain={[0, 'dataMax + 20000']} />
            <YAxis yAxisId="right" orientation="right" hide domain={[0, 'dataMax + 15000']} />
            <Tooltip cursor={{ stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1 }} content={<CustomTooltip />} />
            
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="assets" 
              stroke="#3b82f6" 
              strokeWidth={5} 
              dot={{ r: 3, fill: '#3b82f6', strokeWidth: 2, stroke: '#0a0f1d' }} 
              activeDot={{ r: 6, strokeWidth: 3, stroke: 'rgba(59,130,246,0.2)', fill: '#fff' }}
              animationDuration={1000}
            />
            <Line 
              yAxisId="right"
              type="monotone" 
              dataKey="debts" 
              stroke="#f97316" 
              strokeWidth={4} 
              strokeDasharray="10 6"
              dot={{ r: 3, fill: '#f97316', strokeWidth: 2, stroke: '#0a0f1d' }} 
              activeDot={{ r: 5, strokeWidth: 3, stroke: 'rgba(249,115,22,0.2)', fill: '#f97316' }}
              animationDuration={1200}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-8 pt-12 bg-gradient-to-t from-[#0a0f1d] via-[#0a0f1d]/90 to-transparent">
        <div className="bg-[#111827] px-2 py-2 rounded-2xl flex items-center justify-between border border-white/5 shadow-2xl">
          {frames.map(frame => (
            <button
              key={frame}
              onClick={() => setTimeframe(frame)}
              className={`flex-1 py-2 rounded-xl text-[10px] font-black tracking-widest transition-all ${
                timeframe === frame 
                  ? 'bg-[#3b82f6] text-white shadow-[0_4px_12px_rgba(59,130,246,0.4)]' 
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {frame}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default NetWorth;
