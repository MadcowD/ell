import React, { useState, useEffect } from 'react';
import { useParams, Link, useSearchParams } from 'react-router-dom';
import { useEvaluationRun, useEvaluationRunResults } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import { Card, CardContent } from '../components/common/Card';
import EvaluationRunResultsTable from '../components/evaluations/runs/EvaluationRunResultsTable';
import EvaluationRunDetailsSidebar from '../components/evaluations/runs/EvaluationRunDetailsSidebar';
import EvaluationRunOverview from '../components/evaluations/runs/EvaluationRunOverview';
import EvaluationRunMetrics from '../components/evaluations/runs/EvaluationRunMetrics';
import SearchAndFiltersBar from '../components/evaluations/runs/SearchAndFiltersBar';

function EvaluationRun() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const requestedInvocationId = searchParams.get("i");
  
  const [page, setPage] = React.useState(0);
  const pageSize = 100;
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredResults, setFilteredResults] = useState(null);
  const [activeTab, setActiveTab] = useState("results");
  
  const { data: run, isLoading: isRunLoading } = useEvaluationRun(id);
  const { 
    data: results, 
    isLoading: isResultsLoading 
  } = useEvaluationRunResults(id, page, pageSize);

  useEffect(() => {
    if (requestedInvocationId && results) {
      const requestedResult = results.find(r => r.invocation_being_labeled.id === requestedInvocationId);
      if (requestedResult) {
        setSelectedTrace(requestedResult.invocation_being_labeled);
      }
    }
  }, [requestedInvocationId, results]);

  const handleTraceSelect = (trace) => {
    setSelectedTrace(trace);
    setSearchParams(trace ? { i: trace.id } : {});
  };

  if (isRunLoading || isResultsLoading) {
    return <div className="flex items-center justify-center h-screen">Loading evaluation run...</div>;
  }

  return (
    <GenericPageLayout
      sidebarContent={<EvaluationRunDetailsSidebar run={run} results={filteredResults || results} />}
      minimizeSidebar={true}
      selectedTrace={selectedTrace}
      setSelectedTrace={handleTraceSelect}
    >
      <div className="bg-background text-foreground">
        <EvaluationRunOverview run={run} />
        
        <div className="mb-6">
          <EvaluationRunMetrics 
            run={run} 
            results={filteredResults || results}
            fullResults={results}
          />
        </div>

        <div>
          <div className="flex border-b border-border">
            <button
              className={`px-4 py-2 focus:outline-none ${
                activeTab === "results"
                  ? "text-primary border-b-2 border-primary font-medium"
                  : "text-muted-foreground hover:text-foreground"
              }`}
              onClick={() => setActiveTab("results")}
            >
              Results
            </button>
          </div>

          <div className="mt-4">
            {activeTab === "results" && (
              <>
                <SearchAndFiltersBar 
                  searchQuery={searchQuery}
                  setSearchQuery={setSearchQuery}
                />
                <Card>
                  <EvaluationRunResultsTable
                    results={results}
                    currentPage={page}
                    setCurrentPage={setPage}
                    pageSize={pageSize}
                    selectedTrace={selectedTrace}
                    setSelectedTrace={handleTraceSelect}
                    searchQuery={searchQuery}
                    onFilteredResultsChange={setFilteredResults}
                  />
                </Card>
              </>
            )}
          </div>
        </div>
      </div>
    </GenericPageLayout>
  );
}

export default EvaluationRun;
