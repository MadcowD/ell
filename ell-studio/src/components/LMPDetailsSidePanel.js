import React from 'react';
import { Link } from 'react-router-dom';
import { FiClock, FiTag, FiGitCommit } from 'react-icons/fi';
import { getTimeAgo } from '../utils/lmpUtils';
import ReactMarkdown from 'react-markdown';

function VersionItem({ version, index, totalVersions, currentLmpId }) {
  const isLatest = index === 0;
  const isCurrent = version.lmp_id === currentLmpId;
  const versionNumber = totalVersions - index;
  const commitLines = (version.commit_message || 'Commit message not available').split('\n');
  const commitTitle = commitLines[0] || `Version ${versionNumber}`;
  const commitDetails = commitLines.slice(1).join('\n').trim();

  return (
    <div className="flex items-start mb-3">
      <div className="mr-3 relative">
        <div className={`w-3 h-3 rounded-full ${isCurrent ? 'bg-blue-500' : isLatest ? 'bg-green-500' : 'bg-gray-500'}`}></div>
        {index !== 0 && (
          <div className="absolute top-3 left-1.5 w-0.5 h-full bg-gray-700"></div>
        )}
      </div>
      <Link
        to={`/lmp/${version.name}/${version.lmp_id}`}
        className={`flex-grow text-sm ${isCurrent ? 'font-semibold text-white' : isLatest ? 'text-green-400' : 'text-gray-400'} hover:text-white`}
      >
        <div className="flex justify-between items-center">
          <span>{commitTitle}</span>
          {isLatest && <span className="text-xs bg-green-500 text-white px-2 py-0.5 rounded">Latest</span>}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {getTimeAgo(new Date(version.created_at + "Z"))}
        </div>
      </Link>
    </div>
  );
}

function LMPDetailsSidePanel({ lmp, versionHistory, onSeeAllClick }) {
  const currentVersionIndex = versionHistory.findIndex(v => v.lmp_id === lmp.lmp_id);
  const totalVersions = versionHistory.length;
  const displayVersions = versionHistory.slice(Math.max(0, currentVersionIndex - 2), currentVersionIndex + 3);

  return (
    <aside className="w-[250px] min-w-[350px] sm:min-w-[350px] bg-[#1c1f26] p-6 overflow-y-auto">
      <h2 className="text-lg font-semibold mb-4">Details</h2>
      <div className="space-y-4">
        <p className="flex items-center text-sm">
          <FiClock className="mr-2 text-gray-400" />
          Created: {new Date(lmp.created_at).toLocaleString()}
        </p>
        <p className="flex items-center text-sm">
          <FiTag className="mr-2 text-gray-400" />
          Is LMP: 
          <span className={`ml-2 px-2 py-0.5 rounded ${lmp.is_lmp ? 'bg-green-500' : 'bg-red-500'} text-white text-xs font-medium`}>
            {lmp.is_lmp ? 'Yes' : 'No'}
          </span>
        </p>
        {lmp.lm_kwargs && (
          <div>
            <h3 className="text-md font-semibold mb-2">LM Keywords</h3>
            <pre className="bg-[#13151a] p-2 rounded overflow-x-auto text-xs">
              <code>{JSON.stringify(lmp.lm_kwargs, null, 2)}</code>
            </pre>
          </div>
        )}

        <div className="mt-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-md font-semibold flex items-center">
              <FiGitCommit className="mr-2" />
              Version History
            </h3>
            <button
              className="text-sm text-blue-400 hover:text-blue-300"
              onClick={onSeeAllClick}
            >
              See All
            </button>
          </div>
          <div className="text-sm text-gray-400 mb-4">
            Total versions: {totalVersions}
          </div>
          <div className="space-y-2">
            {displayVersions.map((v, index) => (
              <VersionItem
                key={v.lmp_id}
                version={v}
                index={index}
                totalVersions={totalVersions}
                currentLmpId={lmp.lmp_id}
              />
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}

export default LMPDetailsSidePanel;