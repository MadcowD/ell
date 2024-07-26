import React, { useState, useEffect, useCallback } from 'react';
import { FiCopy, FiZap, FiEdit2, FiFilter, FiClock, FiColumns, FiPause, FiPlay } from 'react-icons/fi';
import TraceDetailsSidebar from '../components/TraceDetailsSidebar';
import TracesRunsPane from '../components/TracesRunsPane';
import axios from 'axios';


const API_BASE_URL = "http://localhost:8080";
const Traces = () => {
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [invocations, setInvocations] = useState([]);
  const [isPolling, setIsPolling] = useState(true);

  const fetchInvocations = useCallback(async () => {
    try {
      const invocationsResponse = await axios.get(`${API_BASE_URL}/api/invocations`);
      const sortedInvocations = invocationsResponse.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setInvocations(sortedInvocations);
    } catch (error) {
      console.error('Error fetching invocations:', error);
    }
  }, []);

  useEffect(() => {
    fetchInvocations(); // Initial fetch

    let intervalId;
    if (isPolling) {
      intervalId = setInterval(fetchInvocations, 200); // Poll every second
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isPolling, fetchInvocations]);

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  return (
    <div className="flex bg-[#0d1117] text-gray-300 h-screen overflow-hidden">
      <div className="flex-grow p-6 overflow-y-auto">
        <div className="flex items-center mb-6">
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <span>Personal</span>
            <span>&gt;</span>
            <span>Projects</span>
            <span>&gt;</span>
            <div className="flex items-center space-x-1">
              <FiCopy className="text-blue-400" />
              <span className="text-white">default</span>
            </div>
          </div>
          <span className="ml-auto px-2 py-1 text-xs bg-[#1c2128] text-blue-400 rounded">DEVELOPER</span>
        </div>
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-white flex items-center">
            <FiCopy className="mr-2 text-blue-400" />
            default
          </h1>
          <div className="flex items-center space-x-2">
            <FiCopy className="text-gray-400" />
            <span className="text-gray-400">ID</span>
            <div className="flex items-center bg-[#1c2128] rounded px-2 py-1">
              <span className="mr-2">Data Retention</span>
              <select className="bg-transparent text-white">
                <option>14d</option>
              </select>
            </div>
            <button className="flex items-center px-3 py-1.5 bg-[#1c2128] text-sm rounded hover:bg-gray-700">
              <FiZap className="mr-1" />
              Add Rule
            </button>
            <button className="flex items-center px-3 py-1.5 bg-[#1c2128] text-sm rounded hover:bg-gray-700">
              <FiEdit2 className="mr-1" />
              Edit
            </button>
          </div>
        </div>
        <div className="flex space-x-6 mb-6 border-b border-gray-800">
          <button className="text-blue-400 font-medium pb-4 border-b-2 border-blue-400">Runs</button>
          <button className="text-gray-400 hover:text-white pb-4">Threads</button>
          <button className="text-gray-400 hover:text-white pb-4">Monitor</button>
          <button className="text-gray-400 hover:text-white pb-4">Setup</button>
        </div>
        <div className="flex items-center space-x-2 mb-6">
          <button className="flex items-center px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">
            <FiFilter className="mr-1" />
            1 filter
          </button>
          <button className="flex items-center px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">
            <FiClock className="mr-1" />
            Last 7 days
          </button>
          <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">Root Runs</button>
          <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">LLM Calls</button>
          <button className="px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">All Runs</button>
          <button
            className={`flex items-center px-2 py-1 ${isPolling ? 'bg-blue-600' : 'bg-[#1c2128]'} text-xs rounded hover:bg-gray-700`}
            onClick={togglePolling}
          >
            {isPolling ? <FiPause className="mr-1" /> : <FiPlay className="mr-1" />}
            {isPolling ? 'Pause Updates' : 'Resume Updates'}
          </button>
          <button className="ml-auto flex items-center px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">
            <FiColumns className="mr-1" />
            Columns
          </button>
        </div>
        <TracesRunsPane invocations={invocations} onSelectTrace={setSelectedTrace} />
      </div>
      {selectedTrace && (
        <TraceDetailsSidebar
          trace={selectedTrace}
          onClose={() => setSelectedTrace(null)}
        />
      )}
    </div>
  );
};

export default Traces;