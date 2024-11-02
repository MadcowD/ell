import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
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
  const [page, setPage] = React.useState(0);
  const pageSize = 100;
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredResults, setFilteredResults] = useState(null);
  
  const { data: run, isLoading: isRunLoading } = useEvaluationRun(id);
  const { 
    data: results, 
    isLoading: isResultsLoading 
  } = useEvaluationRunResults(id, page, pageSize);

  if (isRunLoading || isResultsLoading) {
    return <div className="flex items-center justify-center h-screen">Loading evaluation run...</div>;
  }

  return (
    <GenericPageLayout
      sidebarContent={<EvaluationRunDetailsSidebar run={run} results={filteredResults || results} />}
      minimizeSidebar={true}
      selectedTrace={selectedTrace}
      setSelectedTrace={setSelectedTrace}
    >
      <div className="bg-background text-foreground">
        <EvaluationRunOverview run={run} />
        
        <EvaluationRunMetrics 
          run={run} 
          results={filteredResults || results}
          fullResults={results}
        />

        <div>
          <h2 className="text-lg font-semibold mb-4">Results</h2>
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
              setSelectedTrace={setSelectedTrace}
              searchQuery={searchQuery}
              onFilteredResultsChange={setFilteredResults}
            />
          </Card>
        </div>
      </div>
    </GenericPageLayout>
  );
}

export default EvaluationRun;
