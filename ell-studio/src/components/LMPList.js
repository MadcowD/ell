import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { fetchLMPs } from '../utils/lmpUtils';
import { DependencyGraph } from './depgraph/DependencyGraph';




function LMPList() {
  const [lmps, setLmps] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const { darkMode } = useTheme();
  const [expandedLMP, setExpandedLMP] = useState(null);

  useEffect(() => {
    const getLMPs = async () => {
      try {
        const aggregatedLMPs = await fetchLMPs();
        setLoaded(true);
        setLmps(aggregatedLMPs);
      } catch (error) {
        console.error('Error fetching LMPs:', error);
      }
    };
    getLMPs();
  }, []);

  const toggleExpand = (lmpName, event) => {
    // Prevent toggling when clicking on the link
    if (event.target.tagName.toLowerCase() !== 'a') {
      setExpandedLMP(expandedLMP === lmpName ? null : lmpName);
    }
  };

  const truncateId = (id) => {
    return id.length > 8 ? `${id.substring(0, 8)}...` : id;
  };

  return (
    <div className={`bg-${darkMode ? 'gray-900' : 'gray-100'} min-h-screen`}>
      <div className="container mx-auto px-4 py-8">
        <h1 className={`text-3xl font-bold mb-6 ${darkMode ? 'text-gray-100' : 'text-gray-800'}`}>Language Model Programs</h1>
        {loaded && <DependencyGraph lmps={lmps} />}
        <div className="space-y-4">
          {lmps.map((lmp) => (
            <div 
              key={lmp.name} 
              className={`bg-${darkMode ? 'gray-800' : 'white'} rounded-lg shadow-md p-6 cursor-pointer`}
              onClick={(e) => toggleExpand(lmp.name, e)}
            >
              <div className="flex justify-between items-center mb-2">
                <Link 
                  to={`/lmp/${lmp.versions[0].lmp_id}`} 
                  className={`text-xl font-semibold ${darkMode ? 'text-gray-100 hover:text-blue-300' : 'text-gray-800 hover:text-blue-600'}`}
                  onClick={(e) => e.stopPropagation()} // Prevent card expansion when clicking the link
                >
                  {lmp.name}
                </Link>
                <div className="flex space-x-2">
                  <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}>
                    ID: {truncateId(lmp.versions[0].lmp_id)}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800'}`}>
                    {lmp.versions.length} Version{lmp.versions.length > 1 ? 's' : ''}
                  </span>
                </div>
              </div>
              <div className={`bg-${darkMode ? 'gray-700' : 'gray-100'} rounded p-3 mb-4`}>
                <code className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'}`}>
                  {lmp.source.length > 100 ? `${lmp.source.substring(0, 100)}...` : lmp.source}
                </code>
              </div>
              <div className="flex justify-between items-center">
                <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                  Last Updated: {getTimeAgo(lmp.versions[0].created_at)}
                </p>
              </div>
              {expandedLMP === lmp.name && lmp.versions.length > 1 && (
                <div className={`mt-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                  <h3 className="text-sm font-semibold mb-2">Version History:</h3>
                  <ul className="space-y-4">
                    {lmp.versions.map((version, index) => (
                      <li key={version.lmp_id} className="flex items-center">
                        <div className={`w-4 h-4 rounded-full ${darkMode ? 'bg-blue-500' : 'bg-blue-400'} mr-2`}></div>
                        <div>
                          <p className="text-xs font-semibold">Version {lmp.versions.length - index}</p>
                          <p className="text-xs">{new Date(version.created_at * 1000).toLocaleString()}</p>
                          <p className="text-xs">Invocations: {version.invocations}</p>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default LMPList;

function getTimeAgo(date) {
  const now = new Date();
  const secondsPast = (now.getTime() - date.getTime()) / 1000;
  console.log(now, date);
  if (secondsPast < 60) {
    return `${Math.round(secondsPast)} seconds ago`;
  }
  if (secondsPast < 3600) {
    return `${Math.round(secondsPast / 60)} minutes ago`;
  }
  if (secondsPast <= 86400) {
    return `${Math.round(secondsPast / 3600)} hours ago`;
  }
  if (secondsPast <= 2592000) {
    return `${Math.round(secondsPast / 86400)} days ago`;
  }
  if (secondsPast <= 31536000) {
    return `${Math.round(secondsPast / 2592000)} months ago`;
  }
  return `${Math.round(secondsPast / 31536000)} years ago`;
}


