import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';
import TracesRunsPane from '../components/TracesRunsPane';
import DependencyGraphPane from '../components/DependencyGraphPane';
import SourceCodeView from '../components/SourceCodeView';
import { FiCopy, FiFilter, FiColumns } from 'react-icons/fi';
import VersionHistoryPane from '../components/VersionHistoryPane';
import LMPDetailsSidePanel from '../components/LMPDetailsSidePanel';
import toast, { Toaster } from 'react-hot-toast';
import { Link } from 'react-router-dom';
import TraceDetailsSidebar from '../components/TraceDetailsSidebar';

function LMP() {
  const { name, id } = useParams();
  const [lmp, setLmp] = useState(null);
  const [versionHistory, setVersionHistory] = useState([]);
  const [invocations, setInvocations] = useState([]);
  const [uses, setUses] = useState([]);
  const { darkMode } = useTheme();
  const [activeTab, setActiveTab] = useState('runs');
  const [selectedTrace, setSelectedTrace] = useState(null);

  const API_BASE_URL = "http://localhost:8080";

  useEffect(() => {
    const fetchLMPDetails = async () => {
      try {
        const lmpResponse = await axios.get(`${API_BASE_URL}/api/lmps/${name}${id ? `/${id}` : ''}`);
        const all_lmps_matching = lmpResponse.data;
        // choose the latest lmp
        const latest_lmp = all_lmps_matching
          .map(lmp => ({ ...lmp, created_at: new Date(lmp.created_at) }))
          .sort((a, b) => b.created_at - a.created_at)[0];
        setLmp(latest_lmp);

        // Update page title
        

        console.log(lmpResponse.data)
        const versionHistoryResponse = await axios.get(`${API_BASE_URL}/api/lmps/${latest_lmp.name}`);
        console.log("versionHistoryResponse", versionHistoryResponse)
        setVersionHistory((versionHistoryResponse.data || []).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)));

        const invocationsResponse = await axios.get(`${API_BASE_URL}/api/invocations/${name}${id ? `/${id}` : ''}`);
        const sortedInvocations = invocationsResponse.data.sort((a, b) => b.created_at - a.created_at);
        setInvocations(sortedInvocations);

        const usesIds = lmpResponse.data.uses;
        const uses = await Promise.all(usesIds.map(async (use) => {
          const useResponse = await axios.get(`${API_BASE_URL}/api/lmps/${use}`);
          return useResponse.data;
        }));
        setUses(uses);
      } catch (error) {
        console.error('Error fetching LMP details:', error);
      }
    };
    fetchLMPDetails();
  }, [name, id, API_BASE_URL]);



  const handleSeeAllClick = () => {
    setActiveTab('version_history');
  };

  const handleCopyCode = () => {
    const fullCode = `${lmp.dependencies.trim()}\n\n${lmp.source.trim()}`;
    navigator.clipboard.writeText(fullCode)
      .then(() => {
        toast.success('Code copied to clipboard', {
          duration: 2000,
          position: 'top-center',
        });
      })
      .catch(err => {
        console.error('Failed to copy code: ', err);
        toast.error('Failed to copy code', {
          duration: 2000,
          position: 'top-center',
        });
      });
  };

  if (!lmp) return <div className="flex items-center justify-center h-screen bg-gray-900 text-gray-100">Loading...</div>;

  return (
    <div className="min-h-screen bg-[#13151a] text-gray-200">
      <Toaster />
      <div className="flex flex-col h-screen">
        <header className="bg-[#1c1f26] p-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">
              <Link to={`/lmp/${lmp.name}`} onClick={() => window.history.pushState(null, '', `/lmp/${lmp.name}`)}>
                {lmp.name}
              </Link>
            </h1>
            {id && (
              <>
                <span className="text-gray-400">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </span>
                <span className="text-sm px-2 py-1 bg-[#2a2f3a] rounded">ID: {lmp.lmp_id}</span>
              </>
            )}
          </div>
          <div className="flex space-x-2">
            <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-sm hover:bg-[#3a3f4b] transition-colors">
              Add to Dataset
            </button>
            <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-sm hover:bg-[#3a3f4b] transition-colors">
              Share
            </button>
          </div>
        </header>
        
        <div className="flex-grow flex overflow-hidden">
          <main className="flex-grow p-6 overflow-y-auto hide-scrollbar">
            <div className="mb-6 bg-[#1c1f26] rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Language Model Program</h2>
                <div className="flex space-x-2">
                  <button 
                    className="p-1 rounded bg-[#2a2f3a] hover:bg-[#3a3f4b] transition-colors"
                    onClick={handleCopyCode}
                  >
                    <FiCopy className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="overflow-hidden">
                <SourceCodeView
                  dependencies={lmp.dependencies.trim()}
                  source={lmp.source.trim()}
                  uses={lmp.uses}
                  showDependenciesInitial={!!id}
                />
              </div>
            </div>

            <div className="mb-6">
              <div className="flex border-b border-gray-700">
                {['Runs', 'Version History', 'Dependency Graph'].map((tab) => (
                  <button
                    key={tab}
                    className={`px-4 py-2 focus:outline-none ${
                      activeTab === tab.toLowerCase().replace(' ', '_')
                        ? 'text-blue-400 border-b-2 border-blue-400 font-medium'
                        : 'text-gray-400 hover:text-gray-200'
                    }`}
                    onClick={() => setActiveTab(tab.toLowerCase().replace(' ', '_'))}
                  >
                    {tab}
                  </button>
                ))}
              </div>
              
              <div className="mt-4">
                {activeTab === 'runs' && (
                  <>
                    <div className="flex justify-between items-center mb-4">
                      <div className="flex space-x-2">
                        <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors flex items-center">
                          <FiFilter className="mr-1" /> 1 filter
                        </button>
                        <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                          Last 7 days
                        </button>
                        <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                          Root Runs
                        </button>
                        <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                          LLM Calls
                        </button>
                        <button className="px-3 py-1 bg-[#2a2f3a] text-gray-200 rounded text-xs hover:bg-[#3a3f4b] transition-colors">
                          All Runs
                        </button>
                      </div>
                      <button className="p-1 rounded bg-[#2a2f3a] hover:bg-[#3a3f4b] transition-colors">
                        <FiColumns className="w-4 h-4" />
                      </button>
                    </div>
                    <TracesRunsPane
                      invocations={invocations}
                      producingLmp={lmp}
                      onSelectTrace={(trace) => setSelectedTrace(trace)}
                    />
                  </>
                )}
                {activeTab === 'version_history' && <VersionHistoryPane versions={versionHistory} />}
                {activeTab === 'dependency_graph' && <DependencyGraphPane uses={uses} />}
              </div>
            </div>
          </main>

          <LMPDetailsSidePanel
            lmp={lmp}
            versionHistory={versionHistory}
            onSeeAllClick={handleSeeAllClick}
          />
          {selectedTrace && (
            <TraceDetailsSidebar
              invocation={selectedTrace}
              onClose={() => setSelectedTrace(null)}
        />
      )}
        </div>
      </div>
    </div>
  );
}

export default LMP;