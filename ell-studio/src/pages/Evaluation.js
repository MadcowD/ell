import React, { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useEvaluation } from '../hooks/useBackend';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap } from 'react-icons/fi';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import VersionBadge from '../components/VersionBadge';
import { Card, CardContent } from '../components/common/Card';
import VersionHistoryPane from '../components/VersionHistoryPane';
import RunSummary from '../components/evaluations/RunSummary';
import EvaluationRunsTable from '../components/evaluations/EvaluationRunsTable';
import EvaluationDetailsSidebar from '../components/evaluations/EvaluationDetailsSidebar';
import { getTimeAgo } from '../utils/lmpUtils';

const evaluationConfig = {
  getPath: (version) => `/evaluations/${version.id}`,
  getId: (version) => version.id,
  isCurrentVersion: (version, location) => location.pathname.endsWith(version.id)
};

function Evaluation() {
  const { id } = useParams();
  const [activeTab, setActiveTab] = useState('runs');
  const [selectedRun, setSelectedRun] = useState(null);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10;

  const { data: evaluation, isLoading: isLoadingEvaluation } = useEvaluation(id);

  const groupedRuns = useMemo(() => {
    const groups = {};
    evaluation?.runs.forEach(run => {
      const lmpName = run.evaluated_lmp.name;
      if (!groups[lmpName]) groups[lmpName] = [];
      groups[lmpName].push(run);
    });
    return groups;
  }, [evaluation?.runs]);

  if (isLoadingEvaluation) {
    return <div className="flex items-center justify-center h-screen">Loading evaluation...</div>;
  }

  return (
    <GenericPageLayout
      selectedTrace={selectedRun}
      setSelectedTrace={setSelectedRun}
      sidebarContent={<EvaluationDetailsSidebar evaluation={evaluation} />}
    >
      <div className="bg-background text-foreground">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-lg flex items-center">
            <Link to={`/evaluation/${evaluation.id}`}>
              <Card className="bg-card text-card-foreground">
                <CardContent className="p-2 flex items-center space-x-2">
                  <FiBarChart2 className="h-4 w-4 text-yellow-600" />
                  <code className="px-2 py-1 rounded-md bg-blue-100 text-blue-800 text-sm font-medium truncate">
                    {evaluation.name}
                  </code>
                  <VersionBadge 
                    version={evaluation.version_number} 
                    hash={evaluation.id} 
                    className="text-xs"
                  />
                  <div className="flex items-center text-xs text-gray-400" title={`${evaluation.runs.length} runs`}>
                    <FiZap className="w-3 h-3 mr-1" />
                    {evaluation.runs.length}
                  </div>
                </CardContent>
              </Card>
            </Link>
          </h1>
        </div>

        <main className="overflow-y-auto hide-scrollbar">
          <Card className="mb-6">
            <CardContent className="p-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground mb-2">
                <div className="flex items-center">
                  <FiZap className="mr-1 h-3 w-3" />
                  <span>{evaluation.runs.length} runs ({evaluation.runs.filter(run => run.success).length} successful)</span>
                </div>
                <div className="flex items-center">
                  <FiBarChart2 className="mr-1 h-3 w-3" />
                  <span>{evaluation.n_evals} datapoints</span>
                </div>
                <div className="flex items-center">
                  <FiDatabase className="mr-1 h-3 w-3" />
                  <span>Dataset: {evaluation.dataset_hash.substring(0, 8)}</span>
                </div>
                <div className="flex items-center">
                  <FiTag className="mr-1 h-3 w-3" />
                  <span>{evaluation.labelers.length} metrics</span>
                </div>
                <div className="flex items-center col-span-2">
                  <FiClock className="mr-1 h-3 w-3" />
                  <span>Created: {getTimeAgo(new Date(evaluation.created_at))}</span>
                </div>
              </div>

              {evaluation.commit_message && (
                <p className="mt-2 text-xs text-muted-foreground italic">{evaluation.commit_message}</p>
              )}
            </CardContent>
          </Card>

          <Card className="mb-6">
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-4">Latest Run Summary</h2>
              <RunSummary
                groupedRuns={groupedRuns}
                totalRuns={evaluation.runs.length}
                successfulRuns={evaluation.runs.filter(run => run.success).length}
                isVertical={false}
              />
            </CardContent>
          </Card>

          <div className="mb-6">
            <div className="flex border-b border-border">
              {['Runs', 'Version History'].map((tab) => (
                <button
                  key={tab}
                  className={`px-4 py-2 focus:outline-none ${
                    activeTab === tab.toLowerCase().replace(' ', '_')
                      ? 'text-primary border-b-2 border-primary font-medium'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                  onClick={() => setActiveTab(tab.toLowerCase().replace(' ', '_'))}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="mt-4">
              {activeTab === 'runs' && (
                <EvaluationRunsTable 
                  runs={evaluation.runs}
                  currentPage={currentPage}
                  setCurrentPage={setCurrentPage}
                  pageSize={pageSize}
                  onSelectRun={setSelectedRun}
                  currentlySelectedRun={selectedRun}
                />
              )}
              {activeTab === 'version_history' && (
                <VersionHistoryPane 
                  versions={[evaluation]} 
                  config={evaluationConfig}
                />
              )}
            </div>
          </div>
        </main>
      </div>
    </GenericPageLayout>
  );
}

export default Evaluation;
