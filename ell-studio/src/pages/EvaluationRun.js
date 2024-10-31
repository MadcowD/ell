import React from 'react';
import { useParams } from 'react-router-dom';
import { useEvaluationRun, useEvaluationRunResults } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import { Card } from '../components/common/Card';
import InvocationsTable from '../components/invocations/InvocationsTable';
import EvaluationRunResultsTable from '../components/evaluations/EvaluationRunResultsTable';

function EvaluationRunStats({ run, results }) {
  const totalInvocations = results?.length || 0;
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <Card className="p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-2">Success Rate</h3>
        <p className="text-2xl font-bold">
          98%
        </p>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-2">Average Latency</h3>
        <p className="text-2xl font-bold">
          245ms
        </p>
      </Card>
      <Card className="p-4">
        <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Invocations</h3>
        <p className="text-2xl font-bold">
          {totalInvocations}
        </p>
      </Card>
    </div>
  );
}

function MetricSummaries({ run }) {
  return (
    <Card className="p-4 mb-6">
      <h2 className="text-lg font-semibold mb-4">Metric Summaries</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {run?.labeler_summaries?.map((summary, index) => (
          <Card key={index} className="p-4 bg-background">
            <h3 className="text-sm font-medium mb-2">{summary.evaluation_labeler.name}</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Mean:</span>
                <span>{summary.data?.mean?.toFixed(2) || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Std Dev:</span>
                <span>{summary.data?.std?.toFixed(2) || 'N/A'}</span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </Card>
  );
}

function EvaluationRun() {
  const { id } = useParams();
  const [page, setPage] = React.useState(0);
  const pageSize = 100;
  
  const { data: run, isLoading: isRunLoading } = useEvaluationRun(id);
  const { 
    data: results, 
    isLoading: isResultsLoading 
  } = useEvaluationRunResults(id, page, pageSize);

  console.log(results, run, id)
  
  if (isRunLoading || isResultsLoading) {
    return <div className="flex items-center justify-center h-screen">Loading evaluation run...</div>;
  }

  return (
    <GenericPageLayout>
      <div className="p-6">
        <div className="mb-6">
          <h1 className="text-2xl font-bold mb-2">
            Evaluation Run #{id}
          </h1>
          <p className="text-muted-foreground">
            {run?.evaluated_lmp?.name} - Started at {new Date(run?.start_time).toLocaleString()}
          </p>
        </div>

        <EvaluationRunStats run={run} results={results} />
        
        <div className="mb-6">
          <Card className="p-4">
            <h2 className="text-lg font-semibold mb-4">Performance Over Time</h2>
            <div className="h-64 w-full bg-muted flex items-center justify-center">
              <p className="text-muted-foreground">Performance Graph Placeholder</p>
            </div>
          </Card>
        </div>

        <MetricSummaries run={run} />

        <div>
          <h2 className="text-lg font-semibold mb-4">Results</h2>
          <Card>
            <EvaluationRunResultsTable
              results={results}
              currentPage={page}
              setCurrentPage={setPage}
              pageSize={pageSize}
            />
          </Card>
        </div>
      </div>
    </GenericPageLayout>
  );
}

export default EvaluationRun;
