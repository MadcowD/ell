import React from 'react';

const ToggleSwitch = ({ leftLabel, rightLabel, isRight, onToggle }) => {
  return (
    <div 
      className="flex items-center bg-[#2a2f3a] rounded-full p-1 cursor-pointer shadow-md" 
      onClick={onToggle}
    >
      <span 
        className={`px-4 py-1 text-sm rounded-full transition-colors duration-200 ${
          isRight ? 'text-gray-300' : 'bg-[#3a4151] text-white font-medium'
        }`}
      >
        {leftLabel}
      </span>
      <span 
        className={`px-4 py-1 text-sm rounded-full transition-colors duration-200 ${
          isRight ? 'bg-[#3a4151] text-white font-medium' : 'text-gray-300'
        }`}
      >
        {rightLabel}
      </span>
    </div>
  );
};

export default ToggleSwitch;