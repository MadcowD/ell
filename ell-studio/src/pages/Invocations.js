import React, { useState, useEffect, useMemo } from 'react';
import { FiZap, FiEdit2, FiFilter, FiClock, FiColumns, FiPause, FiPlay, FiSearch } from 'react-icons/fi';
import InvocationsTable from '../components/invocations/InvocationsTable';
import { useNavigate, useLocation } from 'react-router-dom';
import { useInvocationsFromLMP, useInvocationsAggregate } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import InvocationsAnalyticsSidePanel from '../components/invocations/InvocationsAnalyticsSidePanel';

const Invocations = () => {
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [isPolling, setIsPolling] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 50;

  const { data: invocations, isLoading } = useInvocationsFromLMP(null, null, currentPage, pageSize);
  const { data: aggregateData, isLoading: isAggregateLoading } = useInvocationsAggregate(null, null, 30);

  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All Runs');
  const [advancedFilters, setAdvancedFilters] = useState({
    lmpName: '',
    inputContains: '',
    outputContains: '',
    latencyMin: '',
    latencyMax: '',
    tokensMin: '',
    tokensMax: '',
  });

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

  useEffect(() => {
    if (aggregateData) {
      console.log("Received aggregate data:", aggregateData);
    }
  }, [aggregateData]);

  const togglePolling = () => {
    setIsPolling(!isPolling);
  };

  const handleSelectTrace = (trace) => {
    if(trace) {
      setSelectedTrace(trace);
      navigate(`?i=${trace.id}`);
    } else{
      setSelectedTrace(null);
      navigate(``);
    }
  };

  const filteredInvocations = useMemo(() => {
    if (!invocations) return [];
    return invocations.filter(inv => {
      const matchesSearch = 
        inv.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inv.lmp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(inv.contents?.params).toLowerCase().includes(searchTerm.toLowerCase()) ||
        JSON.stringify(inv.contents?.results).toLowerCase().includes(searchTerm.toLowerCase());

      const matchesFilter = 
        selectedFilter === 'All Runs' || 
        (selectedFilter === 'Root Runs' && !inv.used_by_id) ||
        (selectedFilter === 'LLM Calls' && inv.lmp.is_lm);

      const matchesAdvanced =
        (!advancedFilters.lmpName || inv.lmp.name.toLowerCase().includes(advancedFilters.lmpName.toLowerCase())) &&
        (!advancedFilters.inputContains || JSON.stringify(inv.contents?.params).toLowerCase().includes(advancedFilters.inputContains.toLowerCase())) &&
        (!advancedFilters.outputContains || inv.contents?.results.some(result => JSON.stringify(result).toLowerCase().includes(advancedFilters.outputContains.toLowerCase()))) &&
        (!advancedFilters.latencyMin || inv.latency_ms >= parseFloat(advancedFilters.latencyMin) * 1000) &&
        (!advancedFilters.latencyMax || inv.latency_ms <= parseFloat(advancedFilters.latencyMax) * 1000) &&
        (!advancedFilters.tokensMin || (inv.prompt_tokens + inv.completion_tokens) >= parseInt(advancedFilters.tokensMin)) &&
        (!advancedFilters.tokensMax || (inv.prompt_tokens + inv.completion_tokens) <= parseInt(advancedFilters.tokensMax));

      return matchesSearch && matchesFilter && matchesAdvanced;
    });
  }, [invocations, searchTerm, selectedFilter, advancedFilters]);

  const chartData = useMemo(() => {
    if (!filteredInvocations || filteredInvocations.length === 0) return [];

    return filteredInvocations
      .map(inv => ({
        date: new Date(inv.created_at),
        count: 1,
        latency: inv.latency_ms
      }))
      .sort((a, b) => new Date(a.date) - new Date(b.date));
  }, [filteredInvocations]);

  const totalInvocations = useMemo(() => filteredInvocations.length, [filteredInvocations]);
  const avgLatency = useMemo(() => {
    if (filteredInvocations.length === 0) return 0;
    const sum = filteredInvocations.reduce((acc, inv) => acc + inv.latency_ms, 0);
    return sum / filteredInvocations.length;
  }, [filteredInvocations]);

  const sidebarMetrics = useMemo(() => {
    if (!filteredInvocations.length) return null;

    const totalTokens = filteredInvocations.reduce((acc, inv) => acc + inv.prompt_tokens + inv.completion_tokens, 0);
    const uniqueLMPs = new Set(filteredInvocations.map(inv => inv.lmp.name)).size;
    const successRate = (filteredInvocations.filter(inv => inv.status === 'success').length / filteredInvocations.length) * 100;

    const lmpUsage = filteredInvocations.reduce((acc, inv) => {
      acc[inv.lmp.name] = (acc[inv.lmp.name] || 0) + 1;
      return acc;
    }, {});

    const topLMPs = Object.entries(lmpUsage)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5);

    return {
      totalInvocations,
      avgLatency,
      totalTokens,
      uniqueLMPs,
      successRate,
      topLMPs
    };
  }, [filteredInvocations, totalInvocations, avgLatency]);

  const sidebarContent = (
    <InvocationsAnalyticsSidePanel
      aggregateData={aggregateData}
      sidebarMetrics={sidebarMetrics}
    />
  );

  if (isLoading || isAggregateLoading) {
    return <div>Loading...</div>;
  }

  return (
    <GenericPageLayout
      selectedTrace={selectedTrace}
      setSelectedTrace={setSelectedTrace}
      sidebarContent={sidebarContent}
    >
      <div className="bg-background text-foreground">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold">Invocations</h1>
          <div className="flex items-center space-x-2">
            <button
              className={`px-3 py-1 rounded text-xs ${isPolling ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}
              onClick={togglePolling}
            >
              {isPolling ? <FiPause className="inline mr-1" /> : <FiPlay className="inline mr-1" />}
              {isPolling ? 'Pause' : 'Resume'}
            </button>
          </div>
        </div>

        <div className="mb-6 flex items-center space-x-4">
          <div className="relative flex-grow">
            <input
              type="text"
              placeholder="Search invocations..."
              className="w-full pl-10 pr-4 py-2 bg-input text-foreground rounded-md"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
          </div>
          <button 
            className="flex items-center px-3 py-2 bg-[#2d333b] text-sm rounded hover:bg-gray-700"
            onClick={() => setAdvancedFilters(prev => ({ ...prev, isOpen: !prev.isOpen }))}
          >
            <FiFilter className="mr-2" />
            Advanced Filters
          </button>
        </div>
        
        {advancedFilters.isOpen && (
          <div className="grid grid-cols-2 gap-4 bg-[#2d333b] p-4 rounded-md">
            <input
              type="text"
              placeholder="LMP Name"
              className="bg-[#1c2128] text-white px-3 py-1 rounded"
              value={advancedFilters.lmpName}
              onChange={(e) => setAdvancedFilters(prev => ({ ...prev, lmpName: e.target.value }))}
            />
            <input
              type="text"
              placeholder="Input Contains"
              className="bg-[#1c2128] text-white px-3 py-1 rounded"
              value={advancedFilters.inputContains}
              onChange={(e) => setAdvancedFilters(prev => ({ ...prev, inputContains: e.target.value }))}
            />
            <input
              type="text"
              placeholder="Output Contains"
              className="bg-[#1c2128] text-white px-3 py-1 rounded"
              value={advancedFilters.outputContains}
              onChange={(e) => setAdvancedFilters(prev => ({ ...prev, outputContains: e.target.value }))}
            />
            <div className="flex space-x-2">
              <input
                type="number"
                placeholder="Min Latency (s)"
                className="bg-[#1c2128] text-white px-3 py-1 rounded w-1/2"
                value={advancedFilters.latencyMin}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, latencyMin: e.target.value }))}
              />
              <input
                type="number"
                placeholder="Max Latency (s)"
                className="bg-[#1c2128] text-white px-3 py-1 rounded w-1/2"
                value={advancedFilters.latencyMax}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, latencyMax: e.target.value }))}
              />
            </div>
            <div className="flex space-x-2">
              <input
                type="number"
                placeholder="Min Tokens"
                className="bg-[#1c2128] text-white px-3 py-1 rounded w-1/2"
                value={advancedFilters.tokensMin}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, tokensMin: e.target.value }))}
              />
              <input
                type="number"
                placeholder="Max Tokens"
                className="bg-[#1c2128] text-white px-3 py-1 rounded w-1/2"
                value={advancedFilters.tokensMax}
                onChange={(e) => setAdvancedFilters(prev => ({ ...prev, tokensMax: e.target.value }))}
              />
            </div>
          </div>
        )}
        
     
        <InvocationsTable 
          invocations={filteredInvocations} 
          currentPage={currentPage}
          expandAll={true}
          setCurrentPage={setCurrentPage}
          pageSize={pageSize}
          onSelectTrace={handleSelectTrace} 
          currentlySelectedTrace={selectedTrace}
        />
      </div>
    </GenericPageLayout>
  );
};

export default Invocations;