import React from 'react';

const StatItem = ({ icon: Icon, label, value }) => (
  <div 
   
    className="flex items-center justify-between text-sm py-2 border-b border-gray-700 last:border-b-0"
  >
    <span className="flex items-center text-gray-400">
      <Icon className="mr-2" size={14} />
      {label}
    </span>
    <span className="font-medium text-gray-200">{value}</span>
  </div>
);

export default StatItem;