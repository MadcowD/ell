import React, { useRef, useEffect, useState } from 'react';

const getColorFromVersion = (version) => {
  const hue = (version * 137.508) % 360;
  return `hsl(${hue}, 40%, 70%)`;
};

const VersionBadge = ({ version, hash, className = '', shortVersion = false, truncationLength = 9 }) => {
  const [isOverflowing, setIsOverflowing] = useState(false);
  const badgeRef = useRef(null);
  const baseColor = getColorFromVersion(version);
  const lighterColor = `hsl(${baseColor.match(/\d+/)[0]}, 40%, 75%)`;
  const textColor = 'text-gray-900';

  useEffect(() => {
    const checkOverflow = () => {
      if (badgeRef.current) {
        setIsOverflowing(badgeRef.current.scrollWidth > badgeRef.current.clientWidth);
      }
    };

    checkOverflow();
    window.addEventListener('resize', checkOverflow);
    return () => window.removeEventListener('resize', checkOverflow);
  }, [version, hash]);

  const useShortVersion = shortVersion || isOverflowing;

  return (
    <div ref={badgeRef} className={`inline-flex items-center text-xs font-medium rounded-full overflow-hidden whitespace-nowrap ${className}`} title={hash ? `Hash: ${hash}` : undefined}>
      <div className={`px-2 py-1 ${textColor}`} style={{ backgroundColor: baseColor }}>{useShortVersion ? `v${version}` : `Version ${version}`}</div>
      {hash && !useShortVersion && <div className={`px-2 py-1 ${textColor} font-mono`} style={{ backgroundColor: lighterColor }}>{hash.substring(0, truncationLength)}</div>}
    </div>
  );
};

export default VersionBadge;