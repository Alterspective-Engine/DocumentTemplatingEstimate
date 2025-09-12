import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import './MiniGraph.css';

interface MiniGraphProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  showTrend?: boolean;
  label?: string;
}

export const MiniGraph: React.FC<MiniGraphProps> = ({
  data,
  width = 60,
  height = 20,
  color = '#4ECDC4',
  showTrend = true,
  label
}) => {
  if (!data || data.length < 2) {
    return null;
  }

  // Calculate trend
  const lastValue = data[data.length - 1];
  const previousValue = data[data.length - 2];
  const change = lastValue - previousValue;
  const changePercent = previousValue !== 0 ? (change / previousValue) * 100 : 0;
  const trend = change > 0 ? 'up' : change < 0 ? 'down' : 'stable';

  // Normalize data for SVG path
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const points = data.map((value, index) => {
    const x = (index / (data.length - 1)) * width;
    const y = height - ((value - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');

  // Create gradient areas
  const areaPoints = `0,${height} ${points} ${width},${height}`;

  return (
    <div className="mini-graph-container">
      <svg 
        width={width} 
        height={height} 
        className="mini-graph"
        role="img"
        aria-label={`${label || 'Value'} trend: ${changePercent.toFixed(1)}%`}
      >
        <defs>
          <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.3" />
            <stop offset="100%" stopColor={color} stopOpacity="0.05" />
          </linearGradient>
        </defs>
        
        {/* Area fill */}
        <polygon
          points={areaPoints}
          fill={`url(#gradient-${color})`}
        />
        
        {/* Line */}
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        
        {/* Current value dot */}
        <circle
          cx={width}
          cy={height - ((lastValue - min) / range) * height}
          r="2"
          fill={color}
          className="pulse-dot"
        />
      </svg>
      
      {showTrend && (
        <div className={`trend-indicator ${trend}`}>
          {trend === 'up' && <TrendingUp size={12} />}
          {trend === 'down' && <TrendingDown size={12} />}
          {trend === 'stable' && <Minus size={12} />}
          <span className="trend-value">
            {changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  );
};