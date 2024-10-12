import React from 'react';
import { FiBarChart2, FiClipboard } from 'react-icons/fi';

const EvaluationsIcon = ({ className = '' }) => (
  <div className={`relative w-5 h-5 ${className}`}>
    <FiBarChart2 className="w-full h-full" />
    <FiClipboard className="w-3/5 h-3/5 absolute bottom-0 right-0" style={{ transform: 'translate(25%, 25%)' }} />
  </div>
);

export default EvaluationsIcon;
