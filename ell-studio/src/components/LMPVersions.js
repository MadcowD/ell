import React from 'react';
import { Link } from 'react-router-dom';

function formatTimeAgo(date) {
  const seconds = Math.floor((new Date() - new Date(date)) / 1000);
  const intervals = [
    { label: 'year', seconds: 31536000 },
    { label: 'month', seconds: 2592000 },
    { label: 'day', seconds: 86400 },
    { label: 'hour', seconds: 3600 },
    { label: 'minute', seconds: 60 },
    { label: 'second', seconds: 1 }
  ];

  for (let i = 0; i < intervals.length; i++) {
    const interval = intervals[i];
    const count = Math.floor(seconds / interval.seconds);
    if (count >= 1) {
      return `${count} ${interval.label}${count > 1 ? 's' : ''} ago`;
    }
  }
  return 'just now';
}

function LMPVersions({ versions }) {
  return (
    <div className="mt-4 space-y-2">
      <h3 className="text-lg font-semibold">Version History</h3>
      <ul className="space-y-2">
        {versions.map((version, index) => (
          <li key={version.id} className="flex items-center space-x-2">
            <span className="text-gray-500">{index === 0 ? 'Latest' : `v${versions.length - index}`}</span>
            <Link to={`/lmp/${version.lmp_id}`} className="font-mono bg-gray-100 px-2 py-1 rounded text-sm">
              {version.lmp_id}
            </Link>
            <span className="text-gray-500 text-sm">{formatTimeAgo(version.created_at)}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default LMPVersions;