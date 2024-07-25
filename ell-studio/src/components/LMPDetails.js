import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { useTheme } from '../contexts/ThemeContext';
import TracesRunsPane from './TracesRunsPane';
import DependencyGraphPane from './DependencyGraphPane';
import SourceCodeView from './SourceCodeView';
import { FiCopy, FiFilter, FiClock, FiTag, FiColumns } from 'react-icons/fi';
import VersionHistoryPane from './VersionHistoryPane';

function LMPDetails() {
  const { name, id } = useParams();
  const [lmp, setLmp] = useState(null);
  const [versionHistory, setVersionHistory] = useState([]);
  const [invocations, setInvocations] = useState([]);
  const [uses, setUses] = useState([]);
  const { darkMode } = useTheme();
  const [activeTab, setActiveTab] = useState('runs');

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

        console.log(lmpResponse.data)
        const versionHistoryResponse = await axios.get(`${API_BASE_URL}/api/lmps/${latest_lmp.name}`);
        console.log("versionHistoryResponse", versionHistoryResponse)
        setVersionHistory(versionHistoryResponse.data || []);

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

  console.log(lmp)

  if (!lmp) return <div className="flex items-center justify-center h-screen bg-gray-900 text-gray-100">Loading...</div>;

  return (
    <div className="min-h-screen bg-[#13151a] text-gray-200">
      <div className="flex flex-col h-screen">
        <header className="bg-[#1c1f26] p-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <h1 className="text-xl font-semibold">{lmp.name}</h1>
            <span className="text-sm px-2 py-1 bg-[#2a2f3a] rounded">ID: {lmp.lmp_id}</span>
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
          <main className="flex-grow p-6 overflow-y-auto">
            <div className="mb-6 bg-[#1c1f26] rounded-lg p-4">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-lg font-semibold">Language Model Program</h2>
                <div className="flex space-x-2">
                  <button className="p-1 rounded bg-[#2a2f3a] hover:bg-[#3a3f4b] transition-colors">
                    <FiCopy className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <div className="overflow-hidden">
                <SourceCodeView
                  dependencies={lmp.dependencies.trim()}
                  source={lmp.source.trim()}
                  uses={lmp.uses}
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
                      traces={invocations.map(inv => ({
                        name: `Invocation ${inv.id}`,
                        input: JSON.stringify(inv.args),
                        output: JSON.stringify(inv.result),
                        startTime: new Date(inv.created_at * 1000).toLocaleString(),
                        latency: `${inv.latency}ms`
                      }))}
                      onSelectTrace={(trace) => console.log('Selected trace:', trace)}
                    />
                  </>
                )}
                {activeTab === 'version_history' && <VersionHistoryPane versions={versionHistory} />}
                {activeTab === 'dependency_graph' && <DependencyGraphPane uses={uses} />}
              </div>
            </div>
          </main>

          <aside className="w-80 bg-[#1c1f26] p-6 overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">Details</h2>
            <div className="space-y-4">
              <p className="flex items-center text-sm">
                <FiClock className="mr-2 text-gray-400" />
                Created: {new Date(lmp.created_at * 1000).toLocaleString()}
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
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default LMPDetails;