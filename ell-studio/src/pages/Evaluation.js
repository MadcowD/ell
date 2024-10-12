import React, { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useEvaluation } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import { Card, CardContent } from '../components/common/Card';
import VersionHistoryPane from '../components/VersionHistoryPane';
import EvaluationRunsTable from '../components/evaluations/EvaluationRunsTable';
import EvaluationDetailsSidebar from '../components/evaluations/EvaluationDetailsSidebar';
import { EvaluationCardTitle } from '../components/evaluations/EvaluationCardTitle';
import EvaluationOverview from '../components/evaluations/EvaluationOverview';
import VersionBadge from '../components/VersionBadge';

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
                <div className="p-2 flex items-center space-x-2">
                  <EvaluationCardTitle 
                    evaluation={evaluation}
                    fontSize="text-sm"
                    displayVersion={false}
                    shortVersion={false}
                    showRunCount={true}
                    padding={false}
                  />
                </div>
              </Card>
            </Link>
          </h1>
        </div>

        <main className="overflow-y-auto hide-scrollbar">
          <EvaluationOverview evaluation={evaluation} groupedRuns={groupedRuns} />

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
