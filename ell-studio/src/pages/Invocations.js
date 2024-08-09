import React, { useState, useEffect, useMemo } from 'react';
import { FiCopy, FiZap, FiEdit2, FiFilter, FiClock, FiColumns, FiPause, FiPlay, FiSearch } from 'react-icons/fi';
import InvocationsTable from '../components/invocations/InvocationsTable';
import InvocationsLayout from '../components/invocations/InvocationsLayout';
import MetricChart from '../components/MetricChart';
import LMPHistoryChart from '../components/LMPHistoryChart'; // New import
import { useNavigate, useLocation } from 'react-router-dom';
import { useInvocationsFromLMP, useLMPHistory } from '../hooks/useBackend'; // Added useLMPHistory

const Traces = () => {
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [isPolling, setIsPolling] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  const { data: invocations , isLoading } = useInvocationsFromLMP(null, null, currentPage, pageSize);
  const { data: lmpHistory, isLoading: isLMPHistoryLoading } = useLMPHistory(365); // Fetch 1 year of data

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All Runs');

  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const invocationId = searchParams.get('i');
    if (invocationId && invocations) {
      const selectedInvocation = invocations.find(inv => inv.id === invocationId);
      if (selectedInvocation) {
        setSelectedTrace(selectedInvocation);
      }
    }
  }, [location.search, invocations]);

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  const handleSelectTrace = (trace) => {
    setSelectedTrace(trace);
    navigate(`?i=${trace.id}`);
  };

  const filteredInvocations = useMemo(() => {
    if (!invocations) return [];
    return invocations.filter(inv => 
      inv.id.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (selectedFilter === 'All Runs' || 
       (selectedFilter === 'Root Runs' && inv.is_root_run) ||
       (selectedFilter === 'LLM Calls' && inv.is_llm_call))
    );
  }, [invocations, searchTerm, selectedFilter]);

  const chartData = useMemo(() => {
    if (!invocations || invocations.length === 0) return [];

    return invocations
      .map(inv => ({
        date: new Date(inv.created_at),
        count: 1,
        latency: inv.latency_ms
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [invocations]);

  const totalInvocations = useMemo(() => invocations?.length || 0, [invocations]);
  const avgLatency = useMemo(() => {
    if (!invocations || invocations.length === 0) return 0;
    const sum = invocations.reduce((acc, inv) => acc + inv.latency_ms, 0);
    return sum / invocations.length;
  }, [invocations]);

  if (isLoading || isLMPHistoryLoading) {
    return <div>Loading...</div>;
  }

  return (
    <InvocationsLayout 
      selectedTrace={selectedTrace} 
      setSelectedTrace={setSelectedTrace}
      showSidebar={true}
      containerClass={'p-6 flex flex-col h-full'}
    >
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-white flex items-center">
          <FiCopy className="mr-2 text-blue-400" />
          Invocations
        </h1>
        <div className="flex items-center space-x-2">
          <FiCopy className="text-gray-400" />
          <span className="text-gray-400">ID</span>
          <button className="flex items-center px-3 py-1.5 bg-[#1c2128] text-sm rounded hover:bg-gray-700">
            <FiZap className="mr-1" />
            Add Rule
          </button>m
          <button className="flex items-center px-3 py-1.5 bg-[#1c2128] text-sm rounded hover:bg-gray-700">
            <FiEdit2 className="mr-1" />
            Edit
          </button>
        </div>
      </div>

      {/* New search and filter interface */}
      <div className="mb-6 bg-[#1c2128] p-4 rounded-lg">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-grow relative">
            <input
              type="text"
              placeholder="Search invocations..."
              className="w-full bg-[#2d333b] text-white px-4 py-2 rounded-md pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
          </div>
          <button className="flex items-center px-3 py-2 bg-[#2d333b] text-sm rounded hover:bg-gray-700">
            <FiFilter className="mr-2" />
            Advanced Filters
          </button>
        </div>
        <div className="flex space-x-2">
          {['All Runs', 'Root Runs', 'LLM Calls'].map((filter) => (
            <button
              key={filter}
              className={`px-3 py-1.5 rounded ${selectedFilter === filter ? 'bg-blue-600' : 'bg-[#2d333b]'} hover:bg-gray-700`}
              onClick={() => setSelectedFilter(filter)}
            >
              {filter}
            </button>
          ))}
          <button className="flex items-center px-3 py-1.5 bg-[#2d333b] rounded hover:bg-gray-700 ml-2">
            <FiClock className="mr-2" />
            Last 7 days
          </button>
          <button
            className={`flex items-center px-3 py-1.5 ${isPolling ? 'bg-blue-600' : 'bg-[#2d333b]'} rounded hover:bg-gray-700 ml-auto`}
            onClick={togglePolling}
          >
            {isPolling ? <FiPause className="mr-2" /> : <FiPlay className="mr-2" />}
            {isPolling ? 'Pause Updates' : 'Resume Updates'}
          </button>
        </div>
      </div>

      <div className="flex space-x-6 mb-6 flex-grow">
        <div className="flex-1">
          <MetricChart 
            rawData={chartData}
            dataKey="count"
            color="#8884d8"
            title="Invocations"
            yAxisLabel="Count"
          />
        </div>
        <div className="flex-1">
          <MetricChart 
            rawData={chartData}
            dataKey="latency"
            color="#82ca9d"
            title="Latency"
            aggregation="avg"
            yAxisLabel="ms"
          />
        </div>
        {/* <div className="flex-1">
          <LMPHistoryChart 
            data={lmpHistory}
            title="LMP History"
          />
        </div> */}
      </div>
      <div className="flex items-center space-x-2 mb-6">
        <button className="flex items-center px-2 py-1 bg-[#1c2128] text-xs rounded hover:bg-gray-700">
          <FiColumns className="mr-1" />
          Columns
        </button>
      </div>
      <InvocationsTable 
        invocations={filteredInvocations} 
        currentPage={currentPage}
        expandAll={true}
        setCurrentPage={setCurrentPage}
        pageSize={pageSize}
        onSelectTrace={handleSelectTrace} 
        currentlySelectedTrace={selectedTrace}
      />
    </InvocationsLayout>
  );
};

export default Traces;