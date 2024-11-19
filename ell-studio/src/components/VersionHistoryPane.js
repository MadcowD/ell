import React from 'react';
import { FiGitCommit, FiClock, FiCopy, FiChevronRight } from 'react-icons/fi';
import { useNavigate, useLocation } from 'react-router-dom';
import VersionBadge from './VersionBadge';

const VersionHistoryPane = ({ 
  versions, 
  onSelect, 
  config: {
    getPath,
    getId,
    isCurrentVersion
  }
}) => {
  const navigate = useNavigate();
  const location = useLocation();

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) return 'just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;

    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // You might want to add a toast notification here
  };

  const groupVersionsByDate = (versions) => {
    const grouped = {};
    versions.forEach(version => {
      const date = new Date(version.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(version);
    });
    return grouped;
  };

  const groupedVersions = groupVersionsByDate(versions);
  let totalIndex = 0;

  const handleVersionClick = (version) => {
    const path = getPath(version);
    navigate(path);
    if (onSelect) {
      onSelect(version);
    }
  };

  return (
    <div className="text-gray-200 p-4">
      {Object.entries(groupedVersions).sort((a, b) => new Date(b[0]) - new Date(a[0])).map(([date, dateVersions]) => (
        <div key={date} className="mb-6">
          <h3 className="text-sm font-semibold mb-2 text-gray-400">{date}</h3>
          {dateVersions.map((version) => {
            totalIndex++;
            const commitLines = (version.commit_message || 'Commit message not available').split('\n');
            const commitTitle = commitLines[0] || 'Commit message not available';
            const commitDetails = commitLines.slice(1).join('\n').trim();
            const versionId = getId(version);
            return (
              <div key={versionId} className="mb-2 border border-gray-700 rounded-lg overflow-hidden">
                <div className={`bg-gray-800 p-3 flex items-center justify-between cursor-pointer hover:bg-gray-750 ${isCurrentVersion(version, location) ? 'bg-blue-900' : ''}`}
                     onClick={() => handleVersionClick(version)}>
                  <div>
                    <div className="flex items-center mb-1">
                      <FiGitCommit className="text-blue-400 mr-2" />
                      <span className="font-semibold">{commitTitle}</span>
                    </div>
                    {commitDetails && (
                      <div className="text-sm text-gray-400 ml-6 mt-1 whitespace-pre-wrap">{commitDetails}</div>
                    )}
                    <div className="flex items-center text-sm text-gray-400 mt-2">
                      <img
                        src={version.author_avatar || 'https://github.com/github.png'}
                        alt="Author"
                        className="w-5 h-5 rounded-full mr-2"
                      />
                      <span>{version.author_name || 'Unknown'} committed</span>
                      <FiClock className="ml-4 mr-1" />
                      <span>{formatDate(version.created_at)}</span>
                    </div>
                  </div>
                  <FiChevronRight className="text-gray-500" />
                </div>
                <div className={`bg-gray-850 px-3 py-2 flex items-center justify-between ${isCurrentVersion(version, location) || (totalIndex === 1 && !location.pathname.includes('/')) ? 'bg-blue-800' : ''}`}>
                  <div className="flex items-center">
                    <VersionBadge version={versions.length - totalIndex + 1} className="mr-2" />
                    <span className="text-xs font-mono text-gray-400">{versionId.substring(0, 7)}</span>
                  </div>
                  <button
                    className="text-gray-400 hover:text-gray-200 focus:outline-none"
                    onClick={() => copyToClipboard(versionId)}
                    title="Copy full hash"
                  >
                    <FiCopy />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

export default VersionHistoryPane;
