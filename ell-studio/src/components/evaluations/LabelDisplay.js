import React from 'react';

const LabelDisplay = ({ 
  value : valueNumberish, // This is the mean
  isAggregate = false, 
  stats = null // { min, max, stdDev }
}) => {
    const value = typeof valueNumberish === 'boolean' ? Number(valueNumberish) : valueNumberish;

  if (typeof value !== 'number') {
    return <div className="font-mono text-sm">{value}</div>;
  }

  if (!isAggregate || !stats) {
    return <div className="font-mono text-sm">{value.toFixed(2)}</div>;
  }

  const { min, max, stdDev } = stats;
  const mean = value;
  
  // Handle the case where min equals max
  const isConstant = min === max;
  
  // Calculate positions as percentages, clamping to the range
  const meanPos = isConstant ? 50 : ((mean - min) / (max - min)) * 100;
  const leftStdDevPos = isConstant ? 50 : Math.max(((mean - stdDev - min) / (max - min)) * 100, 0);
  const rightStdDevPos = isConstant ? 50 : Math.min(((mean + stdDev - min) / (max - min)) * 100, 100);
  const boxWidth = rightStdDevPos - leftStdDevPos;

  return (
    <div className="font-mono text-sm">
      <div>{value.toFixed(2)}</div>
      <div className="relative w-full h-2 mt-0.5">
        {/* Base bar */}
        <div className={`absolute w-full h-px rounded-full top-1/2 -translate-y-1/2 ${isConstant ? 'bg-gray-200/30' : 'bg-gray-100/50'}`} />
        {/* StdDev box - only show if there's variation */}
        {!isConstant && (
          <div 
            className="absolute h-1.5 bg-gray-50/30 border border-gray-100/30 top-1/2 -translate-y-1/2"
            style={{ 
              left: `${leftStdDevPos}%`,
              width: `${boxWidth}%`
            }}
          />
        )}

        {/* Mean marker - made slightly larger when it's a constant value */}
        <div 
          className={`absolute h-2 bg-white/75 top-0 w-[1px]`}
          style={{ 
            left: `${meanPos}%`,
            transform: 'translateX(-50%)'
          }}
        />
      </div>
    </div>
  );
};

export default LabelDisplay;