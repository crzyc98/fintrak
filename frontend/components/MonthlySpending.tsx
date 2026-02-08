
import React, { useState, useEffect } from 'react';
import { AreaChart, Area, ResponsiveContainer, YAxis, XAxis, ReferenceDot } from 'recharts';
import { fetchMonthlySpending, MonthlySpendingData } from '../src/services/api';

interface ChartDataPoint {
  day: number;
  amount: number;
  pace: number;
}

const MonthlySpending: React.FC = () => {
  const [data, setData] = useState<MonthlySpendingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMonthlySpending()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  // Convert cents to dollars for display
  const formatDollars = (cents: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(cents / 100);
  };

  // Convert API data to chart format (cents to display units)
  const chartData: ChartDataPoint[] = data?.chart_data.map((point) => ({
    day: point.day,
    amount: point.amount / 100,  // Convert to dollars for chart
    pace: point.pace / 100,
  })) || [{ day: 0, amount: 0, pace: 0 }];

  const lastPoint = chartData[chartData.length - 1];
  
  // Calculate pace difference for current point
  const paceDiff = lastPoint.amount - lastPoint.pace;
  const paceDiffDollars = Math.abs(Math.round(paceDiff));
  const isUnderPace = paceDiff < 0;
  const isOverPace = paceDiff > 0;

  // Calculate percentage change from last month (at same point)
  const lastMonthSamePointDollars = (data?.last_month_same_point || 0) / 100;
  const currentSpending = lastPoint.amount;
  const percentChange = lastMonthSamePointDollars > 0
    ? ((currentSpending - lastMonthSamePointDollars) / lastMonthSamePointDollars) * 100
    : 0;

  // Determine bubble color based on pace
  const getBubbleColor = () => {
    if (isUnderPace) return '#22c55e';  // Green when under
    if (paceDiff > lastPoint.pace * 0.15) return '#ef4444';  // Red when significantly over
    return '#facc15';  // Yellow when slightly over
  };

  const bubbleColor = getBubbleColor();

  // Custom component for the pace difference bubble
  const CustomCallout = (props: any) => {
    const { cx, cy } = props;
    const bubbleText = `${formatDollars(paceDiffDollars * 100)} ${isUnderPace ? 'under' : 'over'}`;
    const bubbleWidth = Math.max(85, bubbleText.length * 7);

    return (
      <g transform={`translate(${cx - bubbleWidth - 20}, ${cy - 12})`}>
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
          width={bubbleWidth} height="26"
          rx="10"
          fill={bubbleColor}
          filter="url(#bubbleShadow)"
        />
        <text
          x={bubbleWidth / 2} y="17"
          textAnchor="middle"
          fill="#020817"
          style={{ fontSize: '11px', fontWeight: '900', letterSpacing: '-0.02em' }}
        >
          {bubbleText}
        </text>
        {/* Pointer pointing to the dot */}
        <path d={`M ${bubbleWidth} 8 L ${bubbleWidth + 9} 13 L ${bubbleWidth} 18 Z`} fill={bubbleColor} />
      </g>
    );
  };

  const gradientStops = chartData.map((d, i) => {
    const offset = (i / (chartData.length - 1)) * 100;
    const diff = d.amount - d.pace;
    let color = '#22c55e';
    if (diff > d.pace * 0.15) color = '#ef4444';
    else if (diff > 0) color = '#facc15';
    return <stop key={i} offset={`${offset}%`} stopColor={color} />;
  });

  if (loading) {
    return (
      <div className="bg-[#020817] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] relative overflow-hidden shadow-2xl shadow-black/50">
        <div className="flex justify-between items-center relative z-20">
          <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Monthly spending</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Loading...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-[#020817] border border-white/10 rounded-3xl p-8 flex flex-col h-[460px] relative overflow-hidden shadow-2xl shadow-black/50">
        <div className="flex justify-between items-center relative z-20">
          <h2 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em]">Monthly spending</h2>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-red-400">Error: {error}</div>
        </div>
      </div>
    );
  }

  const isUp = percentChange > 0;
  const changeColor = isUp ? 'text-red-500' : 'text-green-500';

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
          <span className="text-5xl font-black text-white tracking-tighter">{formatDollars(data?.current_month_total || 0)}</span>
          <span className="text-2xl font-semibold text-gray-600">spent</span>
        </div>
        <div className="flex items-center mt-1 text-gray-500 text-sm font-medium tracking-tight">
          <span>{formatDollars(data?.last_month_same_point || 0)} at this point last month</span>
          {percentChange !== 0 && (
            <span className={`ml-2 flex items-center ${changeColor} font-bold`}>
              <svg className={`w-3 h-3 mr-0.5 ${isUp ? 'rotate-180' : ''}`} fill="currentColor" viewBox="0 0 20 20">
                <path d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"></path>
              </svg>
              {Math.abs(Math.round(percentChange))}%
            </span>
          )}
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0 h-[280px] z-10">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 0, right: 0, left: 0, bottom: 0 }}>
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
              fill={bubbleColor}
              stroke="#020817"
              strokeWidth={3}
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
