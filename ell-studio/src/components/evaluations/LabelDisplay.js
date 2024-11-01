import React from 'react';

const LabelDisplay = ({ 
  value, // This is the mean
  isAggregate = false, 
  stats = null // { min, max, stdDev }
}) => {
  if (typeof value !== 'number') {
    return <div className="font-mono text-sm">{value}</div>;
  }

  if (!isAggregate || !stats) {
    return <div className="font-mono text-sm">{value.toFixed(2)}</div>;
  }

  const { min, max, stdDev } = stats;
  const mean = value;
  
  // Calculate positions as percentages, clamping to the range
  const meanPos = ((mean - min) / (max - min)) * 100;
  const leftStdDevPos = Math.max(((mean - stdDev - min) / (max - min)) * 100, 0);
  const rightStdDevPos = Math.min(((mean + stdDev - min) / (max - min)) * 100, 100);
  const boxWidth = rightStdDevPos - leftStdDevPos;

  return (
    <div className="font-mono text-sm">
      <div>{value.toFixed(2)}</div>
      <div className="relative w-full h-2 mt-0.5">
        {/* Base bar */}
        <div className="absolute w-full h-px bg-gray-100/50 rounded-full top-1/2 -translate-y-1/2" />
        
        {/* StdDev box */}
        <div 
          className="absolute h-1.5 bg-gray-50/30 border border-gray-100/30 top-1/2 -translate-y-1/2"
          style={{ 
            left: `${leftStdDevPos}%`,
            width: `${boxWidth}%`
          }}
        />

        {/* Mean marker */}
        <div 
          className="absolute w-[1px] h-2 bg-white/75 top-0"
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