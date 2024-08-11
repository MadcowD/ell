import React, { useState, useEffect, useMemo } from 'react';
import { FiZap, FiEdit2, FiFilter, FiClock, FiColumns, FiPause, FiPlay, FiSearch } from 'react-icons/fi';
import InvocationsTable from '../components/invocations/InvocationsTable';
import InvocationsLayout from '../components/invocations/InvocationsLayout';
import MetricChart from '../components/MetricChart';
import { useNavigate, useLocation } from 'react-router-dom';
import { useInvocationsFromLMP, useInvocationsAggregate } from '../hooks/useBackend';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from "../components/common/Resizable";
import { ScrollArea } from '../components/common/ScrollArea';

const Traces = () => {
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
    setSelectedTrace(trace);
    navigate(`?i=${trace.id}`);
  };

  const filteredInvocations = useMemo(() => {
    if (!invocations) return [];
    return invocations.filter(inv => {
      const matchesSearch = 
        inv.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inv.lmp.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        inv.args.some(arg => JSON.stringify(arg).toLowerCase().includes(searchTerm.toLowerCase())) ||
        inv.results.some(result => JSON.stringify(result).toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesFilter = 
        selectedFilter === 'All Runs' || 
        (selectedFilter === 'Root Runs' && !inv.used_by_id) ||
        (selectedFilter === 'LLM Calls' && inv.lmp.is_lm);

      const matchesAdvanced =
        (!advancedFilters.lmpName || inv.lmp.name.toLowerCase().includes(advancedFilters.lmpName.toLowerCase())) &&
        (!advancedFilters.inputContains || inv.args.some(arg => JSON.stringify(arg).toLowerCase().includes(advancedFilters.inputContains.toLowerCase()))) &&
        (!advancedFilters.outputContains || inv.results.some(result => JSON.stringify(result).toLowerCase().includes(advancedFilters.outputContains.toLowerCase()))) &&
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

  if (isLoading || isAggregateLoading) {
    return <div>Loading...</div>;
  }

  return (
    <ResizablePanelGroup direction="horizontal" className="w-full h-screen">
      <ResizablePanel defaultSize={selectedTrace ? 100 : 70} minSize={30}>
        <InvocationsLayout 
          selectedTrace={selectedTrace} 
          setSelectedTrace={setSelectedTrace}
          showSidebar={selectedTrace}
          containerClass={'p-6 flex flex-col h-full'}
        >
          <div className="flex justify-between items-center mb-6">
            <h1 className="text-2xl font-semibold text-white flex items-center">
              {/* <FiZap className="mr-2 text-blue-400" /> */}
              Invocations
            </h1>
          </div>

          {/* Search bar, advanced filters, and controls */}
          <div className="mb-6 space-y-4">
            <div className="flex items-center space-x-4">
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
              <button 
                className="flex items-center px-3 py-2 bg-[#2d333b] text-sm rounded hover:bg-gray-700"
                onClick={() => setAdvancedFilters(prev => ({ ...prev, isOpen: !prev.isOpen }))}
              >
                <FiFilter className="mr-2" />
                Advanced Filters
              </button>
              <button
                className={`flex items-center px-3 py-2 ${isPolling ? 'bg-blue-600' : 'bg-[#2d333b]'} rounded hover:bg-gray-700`}
                onClick={togglePolling}
              >
                {isPolling ? <FiPause className="mr-2" /> : <FiPlay className="mr-2" />}
                {isPolling ? 'Pause Updates' : 'Resume Updates'}
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
      </ResizablePanel>
      {!selectedTrace && (
        <>
          <ResizableHandle withHandle />
          <ResizablePanel defaultSize={30} minSize={20}>
            <ScrollArea className="h-full p-4 bg-[#1c1f26]">
              {!isAggregateLoading && aggregateData && (
                <>
                  <div className="grid grid-cols-2 gap-4 mb-6">
                    <div className="bg-[#161b22] p-3 rounded">
                      <h3 className="text-sm font-semibold text-white mb-1">Total Invocations</h3>
                      <p className="text-2xl font-bold text-white">{aggregateData.total_invocations}</p>
                    </div>
                    <div className="bg-[#161b22] p-3 rounded">
                      <h3 className="text-sm font-semibold text-white mb-1">Avg Latency</h3>
                      <p className="text-2xl font-bold text-white">{aggregateData.avg_latency.toFixed(2)}ms</p>
                    </div>
                    <div className="bg-[#161b22] p-3 rounded">
                      <h3 className="text-sm font-semibold text-white mb-1">Total Tokens</h3>
                      <p className="text-2xl font-bold text-white">{aggregateData.total_tokens}</p>
                    </div>
                    <div className="bg-[#161b22] p-3 rounded">
                      <h3 className="text-sm font-semibold text-white mb-1">Unique LMPs</h3>
                      <p className="text-2xl font-bold text-white">{aggregateData.unique_lmps}</p>
                    </div>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-[#161b22] p-4 rounded">
                      <h3 className="text-md font-semibold text-white mb-3">Invocations Over Time</h3>
                      <MetricChart 
                        rawData={aggregateData.graph_data}
                        dataKey="count"
                        aggregation={"sum"}
                        color="#8884d8"
                        title={`Invocations (${aggregateData.total_invocations})`}
                        yAxisLabel="Count"
                      />
                    </div>

                    <div className="bg-[#161b22] p-4 rounded">
                      <h3 className="text-md font-semibold text-white mb-3">Latency Over Time</h3>
                      <MetricChart 
                        rawData={aggregateData.graph_data}
                        dataKey="avg_latency"
                        aggregation={"avg"}
                        color="#82ca9d"
                        title={`Average Latency (${aggregateData.avg_latency.toFixed(2)}ms)`}
                        yAxisLabel="ms"
                      />
                    </div>

                    <div className="bg-[#161b22] p-4 rounded">
                      <h3 className="text-md font-semibold text-white mb-3">Tokens Over Time</h3>
                      <MetricChart 
                        rawData={aggregateData.graph_data}
                        dataKey="tokens"
                        color="#ffc658"
                        title={`Total Tokens (${aggregateData.total_tokens})`}
                        yAxisLabel="Tokens"
                      />
                    </div>


                    <div className="bg-[#161b22] p-4 rounded">
                      <h3 className="text-md font-semibold text-white mb-3">Top 5 LMPs</h3>
                      <ul className="space-y-2">
                        {sidebarMetrics.topLMPs.map(([lmp, count], index) => (
                          <li key={lmp} className="flex justify-between items-center text-white">
                            <span>{index + 1}. {lmp}</span>
                            <span className="text-sm text-gray-400">{count} invocations</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="bg-[#161b22] p-4 rounded">
                      <h3 className="text-md font-semibold text-white mb-3">Additional Metrics</h3>
                      <div className="space-y-2 text-white">
                        <div className="flex justify-between">
                          <span>Success Rate:</span>
                          <span>{aggregateData.success_rate?.toFixed(2)}%</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Avg Tokens per Invocation:</span>
                          <span>{(aggregateData.total_tokens / aggregateData.total_invocations).toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </ScrollArea>
          </ResizablePanel>
        </>
      )}
    </ResizablePanelGroup>
  );
};

export default Traces;