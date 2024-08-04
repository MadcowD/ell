import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { fetchLMPs, getTimeAgo, fetchTraces } from '../utils/lmpUtils';
import { DependencyGraph } from '../components/depgraph/DependencyGraph';
import { Code } from 'lucide-react';
import { Card, CardHeader, CardContent } from 'components/common/Card';
import { ScrollArea } from 'components/common/ScrollArea';
import { Badge } from 'components/common/Badge';

function Home() {
  const [lmps, setLmps] = useState([]);
  const [loaded, setLoaded] = useState(false);
  const { darkMode } = useTheme();
  const [expandedLMP, setExpandedLMP] = useState(null);
  const [traces, setTraces] = useState([]);

  useEffect(() => {
    const getLMPs = async () => {
      try {
        const aggregatedLMPs = await fetchLMPs();
        const traces = await fetchTraces(aggregatedLMPs);
        setLmps(aggregatedLMPs);
        setTraces(traces);

        setLoaded(true);
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
      <div className="flex w-full h-full">
        <div className="flex flex-col min-h-screen w-[70%] border-r">
          <div className={`flex items-center justify-between border-b p-2 py-4`}>
            <span className={`text-xl font-medium ${darkMode ? 'text-gray-100' : 'text-gray-800'} flex items-center`}>
              <Code className="w-6 h-6 mr-2" />
              Language Model Programs
            </span>
            <div className="flex items-center">
              <span className={`mr-4 text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Total LMPs: {lmps.length}
              </span>
              <span className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                Last Updated: {lmps.length > 0 ? getTimeAgo(lmps[0].versions[0].created_at) : 'N/A'}
              </span>
            </div>
          </div>
          {loaded && <DependencyGraph lmps={lmps} traces={traces}/>}
        </div>
        <ScrollArea className="flex flex-col gap-2 w-[30%] h-screen">
          <div className="space-y-2 p-4">
            {lmps.map((lmp) => (
              <Card 
                key={lmp.name} 
                className={`${darkMode ? 'bg-gray-800' : 'bg-white'} cursor-pointer`}
                onClick={(e) => toggleExpand(lmp.name, e)}
              >
                <CardHeader>
                  <div className="flex justify-between">
                    <Link 
                      to={`/lmp/${lmp.name}`} 
                      className={`text-xl font-semibold ${darkMode ? 'text-gray-100 hover:text-blue-300' : 'text-gray-800 hover:text-blue-600'} break-words`}
                      onClick={(e) => e.stopPropagation()} // Prevent card expansion when clicking the link
                    >
                      {truncateId(lmp.name)}
                    </Link>
                    <div className="flex flex-wrap gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-700'}`}>
                      ID: {truncateId(lmp.versions[0].lmp_id)}
                    </span>

                    <span className={`text-xs px-2 py-1 rounded-full ml-2 ${darkMode ? 'bg-green-600 text-white' : 'bg-green-100 text-green-800'}`}>
                      Latest
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${darkMode ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-800'}`}>
                      {lmp.versions.length} Version{lmp.versions.length > 1 ? 's' : ''}
                    </span>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className={`bg-${darkMode ? 'gray-700' : 'gray-100'} rounded p-3 mb-4 overflow-x-auto`}>
                    <code className={`text-sm ${darkMode ? 'text-gray-300' : 'text-gray-700'} whitespace-pre-wrap break-words`}>
                      {lmp.source.length > 100 ? `${lmp.source.substring(0, 100)}...` : lmp.source}
                    </code>
                  </div>
                  <p className={`text-xs ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                    Last Updated: {getTimeAgo(lmp.versions[0].created_at)}
                  </p>
                  {expandedLMP === lmp.name && lmp.versions.length > 1 && (
                    <div className={`mt-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                      <h3 className="text-sm font-semibold mb-2">Version History:</h3>
                      <ul className="space-y-4">
                        {lmp.versions.map((version, index) => (
                          <li key={version.lmp_id} className="flex items-start">
                            <div className={`w-4 h-4 rounded-full ${darkMode ? 'bg-blue-500' : 'bg-blue-400'} mr-2 mt-1 flex-shrink-0`}></div>
                            <div className="flex-grow min-w-0">
                              <p className="text-xs font-semibold break-words">Version {lmp.versions.length - index}</p>
                              <p className="text-xs break-words">{new Date(version.created_at * 1000).toLocaleString()}</p>
                              <p className="text-xs">Invocations: {version.invocations}</p>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}

export default Home;
