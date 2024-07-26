import React from 'react';

const getColorFromVersion = (version) => {
  const hue = (version * 137.508) % 360; // Golden angle approximation
  return `hsl(${hue}, 40%, 70%)`; // Reduced saturation, increased lightness
};

const VersionBadge = ({ version, lmpId, className = '' }) => {
  const backgroundColor = getColorFromVersion(version);
  const textColor = 'text-gray-900'; // Always use dark text for better contrast

  return (
    <span 
      className={`text-xs font-medium px-2 py-1 rounded-full ${textColor} ${className}`}
      style={{ backgroundColor }}
      title={lmpId ? `LMP ID: ${lmpId}` : undefined}
    >
      Version {version}
    </span>
  );
};

export default VersionBadge;