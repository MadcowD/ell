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

const MetricDisplay = ({ currentValue : nonFloatCurrentValue, previousValue, label, showTooltip = true, showTrend = true }) => {
  const currentValue = Number(nonFloatCurrentValue);
  const percentChange = previousValue !== undefined && previousValue !== 0
    ? ((currentValue - previousValue) / Math.abs(previousValue) * 100).toFixed(1)
    : (currentValue !== 0 ? '100.0' : '0.0');

  const trendColorClass = getColorForTrend(parseFloat(percentChange));
  const trendIcon = getTrendIcon(parseFloat(percentChange));
  const [isHighlighted, setIsHighlighted] = React.useState(false);
  React.useEffect(() => {
    setIsHighlighted(true);
    // Reduce timeout from 150ms to 100ms
    const timer = setTimeout(() => setIsHighlighted(false), 100);
    return () => clearTimeout(timer);
  }, [currentValue]);

  const content = (
    <div className="text-right min-w-[3rem]">
      <div className={`font-bold font-mono overflow-hidden`}>
        <span className={`inline-block transition-all duration-75 ease-in-out ${isHighlighted ? `${trendColorClass} transform scale-105` : 'transform scale-100'}`}>
          {currentValue.toFixed(2)}
        </span>
      </div>
      {showTrend && (
        <div className={`text-[10px] ${trendColorClass} whitespace-nowrap transition-opacity duration-150 ease-in-out ${isHighlighted ? 'opacity-100' : 'opacity-80'}`}>
          {trendIcon}{Math.abs(parseFloat(percentChange)).toFixed(1)}%
        </div>
      )}
    </div>
  );

  if (!showTooltip) {
    return content;
  }


  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div >
            {content}
          </div>
        </TooltipTrigger>
        <TooltipContent sideOffset={5}>
          <div className="text-xs">
            <p className="font-medium">{label}</p>
            <p>Current: {currentValue.toFixed(4)}</p>
            <p>Previous: {previousValue !== undefined && previousValue !== null ? previousValue.toFixed(4) : 'N/A'}</p>
            <p>Change: {previousValue !== undefined && previousValue !== null ? (currentValue - previousValue).toFixed(4) : 'N/A'}</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

export default MetricDisplay;
