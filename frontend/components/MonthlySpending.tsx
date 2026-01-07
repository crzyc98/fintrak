
import React from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis, ReferenceDot } from 'recharts';
import { SPENDING_CHART_DATA } from '../mockData';

const MonthlySpending: React.FC = () => {
  const lastPoint = SPENDING_CHART_DATA[SPENDING_CHART_DATA.length - 1];
  
  // Custom component for the "$100 under" bubble
  const CustomCallout = (props: any) => {
    const { cx, cy } = props;
    // Position bubble slightly to the left of the point with a sharp tail
    return (
      <g transform={`translate(${cx - 105}, ${cy - 12})`}>
        <filter id="bubbleShadow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur in="SourceAlpha" stdDeviation="4" />
          <feOffset dx="0" dy="4" result="offsetblur" />
          <feComponentTransfer>
            <feFuncA type="linear" slope="0.3" />
          </feComponentTransfer>
          <feMerge>
            <feMergeNode />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        <rect 
          x="0" y="0" 
          width="85" height="26" 
          rx="10" 
          fill="#22c55e" 
          filter="url(#bubbleShadow)"
        />
        <text 
          x="42.5" y="17" 
          textAnchor="middle" 
          fill="#020817" 
          style={{ fontSize: '11px', fontWeight: '900', letterSpacing: '-0.02em' }}
        >
          $100 under
        </text>
        {/* Pointer pointing to the dot */}
        <path d="M 85 8 L 94 13 L 85 18 Z" fill="#22c55e" />
      </g>
    );
  };

  const gradientStops = SPENDING_CHART_DATA.map((d, i) => {
    const offset = (i / (SPENDING_CHART_DATA.length - 1)) * 100;
    const diff = d.amount - d.pace;
    let color = '#22c55e'; 
    if (diff > 15) color = '#ef4444'; 
    else if (diff > -15) color = '#facc15'; 
    return <stop key={i} offset={`${offset}%`} stopColor={color} />;
  });

  return (
    <div className="bg-[#020817] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] relative overflow-hidden shadow-2xl shadow-black/50">
      <div className="flex justify-between items-center relative z-20">
        <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Monthly spending</h2>
        <button className="text-sm font-semibold text-gray-400 hover:text-white transition-colors flex items-center group">
          Transactions 
          <svg className="w-4 h-4 ml-1 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7"></path>
          </svg>
        </button>
      </div>

      <div className="flex flex-col items-center justify-center mt-6 mb-4 relative z-20">
        <div className="flex items-baseline space-x-2">
          <span className="text-5xl font-black text-white tracking-tighter">$1,000</span>
          <span className="text-2xl font-semibold text-gray-600">spent</span>
        </div>
        <div className="flex items-center mt-1 text-gray-500 text-sm font-medium tracking-tight">
          <span>$500 spent last month</span>
          <span className="ml-2 flex items-center text-red-500 font-bold">
            <svg className="w-3 h-3 mr-0.5 rotate-180" fill="currentColor" viewBox="0 0 20 20">
              <path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"></path>
            </svg>
            12%
          </span>
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-[280px] z-10">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={SPENDING_CHART_DATA} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="copilotStroke" x1="0" y1="0" x2="1" y2="0">
                {gradientStops}
              </linearGradient>
              <linearGradient id="copilotFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" stopOpacity={0.2}/>
                <stop offset="100%" stopColor="#22c55e" stopOpacity={0}/>
              </linearGradient>
            </defs>

            <YAxis hide domain={[0, (dataMax: number) => dataMax + 80]} padding={{ top: 0, bottom: 0 }} />
            <XAxis hide dataKey="day" padding={{ left: 0, right: 0 }} />

            <Area 
              type="linear" 
              dataKey="pace" 
              stroke="#1e293b" 
              strokeWidth={1.5}
              strokeDasharray="8 6"
              fill="transparent"
              dot={false}
              isAnimationActive={false}
              baseValue={0}
            />

            <Area 
              type="monotone" 
              dataKey="amount" 
              stroke="url(#copilotStroke)" 
              strokeWidth={5}
              fill="url(#copilotFill)" 
              dot={false}
              animationDuration={1500}
              baseValue={0}
            />

            <ReferenceDot
              x={lastPoint.day}
              y={lastPoint.amount}
              r={7}
              fill="#22c55e"
              stroke="#020817"
              strokeWidth={3}
              className="drop-shadow-[0_0_15px_rgba(34,197,94,0.8)]"
            />

            <ReferenceDot
              x={lastPoint.day}
              y={lastPoint.amount}
              shape={<CustomCallout />}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default MonthlySpending;
