import React from 'react';
import { FiTrendingUp, FiTrendingDown, FiMinus } from 'react-icons/fi';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../common/Tooltips';

const getColorForTrend = (trend) => {
  if (trend > 0) return 'text-emerald-400';
  if (trend < 0) return 'text-rose-400';
  return 'text-gray-400';
};

const getTrendIcon = (trend) => {
  if (trend > 0) return <FiTrendingUp className="inline-block mr-1" />;
  if (trend < 0) return <FiTrendingDown className="inline-block mr-1" />;
  return <FiMinus className="inline-block mr-1" />;
};

const MetricDisplay = ({ currentValue, previousValue, label, showTooltip = true }) => {
  const percentChange = previousValue !== undefined && previousValue !== 0
    ? ((currentValue - previousValue) / Math.abs(previousValue) * 100).toFixed(1)
    : (currentValue !== 0 ? '100.0' : '0.0');

  const trendColorClass = getColorForTrend(parseFloat(percentChange));
  const trendIcon = getTrendIcon(parseFloat(percentChange));

  const content = (
    <div className="text-right min-w-[5rem]">
      <div className="font-bold font-mono">{currentValue.toFixed(2)}</div>
      <div className={`text-[10px] ${trendColorClass} whitespace-nowrap`}>
        {trendIcon}{Math.abs(parseFloat(percentChange)).toFixed(1)}%
      </div>
    </div>
  );

  if (!showTooltip) {
    return content;
  }

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          {content}
        </TooltipTrigger>
        <TooltipContent sideOffset={5}>
          <div className="text-xs">
            <p className="font-medium">{label}</p>
            <p>Current: {currentValue.toFixed(4)}</p>
            <p>Previous: {previousValue !== undefined ? previousValue.toFixed(4) : 'N/A'}</p>
            <p>Change: {previousValue !== undefined ? (currentValue - previousValue).toFixed(4) : 'N/A'}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default MetricDisplay;
