import React, { useState, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useEvaluation } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import { Card, CardContent } from '../components/common/Card';
import VersionHistoryPane from '../components/VersionHistoryPane';
import EvaluationRunsTable from '../components/evaluations/runs/EvaluationRunsTable';
import EvaluationDetailsSidebar from '../components/evaluations/EvaluationDetailsSidebar';
import { EvaluationCardTitle } from '../components/evaluations/EvaluationCardTitle';
import EvaluationOverview from '../components/evaluations/EvaluationOverview';
import VersionBadge from '../components/VersionBadge';
import LMPSourceView from '../components/source/LMPSourceView';
import { FiCopy } from 'react-icons/fi';
import toast from 'react-hot-toast';
import EvaluationDataset from '../components/evaluations/EvaluationDataset';

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
  const [activeIndex, setActiveIndex] = useState(null);

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

  const handleCopyCode = (lmp) => {
    const fullCode = `${lmp.dependencies.trim()}\n\n${lmp.source.trim()}`;
    navigator.clipboard
      .writeText(fullCode)
      .then(() => {
        toast.success("Code copied to clipboard", {
          duration: 2000,
          position: "top-center",
        });
      })
      .catch((err) => {
        console.error("Failed to copy code: ", err);
        toast.error("Failed to copy code", {
          duration: 2000,
          position: "top-center",
        });
      });
  };

  // TODO: Move hte graph state all the way out so we don't do callbacks and get do bidirectional state propagation
  const handleActiveIndexChange = (index) => {
    setActiveIndex(index);
    console.log('Active index in Evaluation:', index);
  };

  // Update the tabs array to include all tabs
  const tabs = ['Runs', 'Metrics', 'Dataset', 'Version History'];

  if (isLoadingEvaluation || !evaluation?.labelers?.length) {
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
            <Link to={`/evaluations/${evaluation.id}`}>
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
          <EvaluationOverview 
            evaluation={evaluation} 
            groupedRuns={groupedRuns}
            onActiveIndexChange={handleActiveIndexChange}
          />

          <div className="mb-6">
            <div className="flex border-b border-border">
              {tabs.map((tab) => (
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
                  activeIndex={activeIndex}
                />
              )}
              {activeTab === 'metrics' && (
                <div>
                  {evaluation.labelers.map((labeler, index) => (
                    <div key={index} className="mb-6 bg-card rounded-lg p-4">
                      <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center space-x-4">
                          <h2 className="text-md font-semibold text-card-foreground">Metric: {labeler.name}</h2>
                          <VersionBadge version={labeler.labeling_lmp.version_number + 1} />
                        </div>
                        <div className="flex space-x-4 items-center">
                          <button
                            className="p-1 rounded bg-secondary hover:bg-secondary/80 transition-colors"
                            onClick={() => handleCopyCode(labeler.labeling_lmp)}
                          >
                            <FiCopy className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                      <div className="overflow-hidden">
                        <LMPSourceView
                          lmp={labeler.labeling_lmp}
                          showDependenciesInitial={true}
                          viewMode="Source"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {activeTab === 'dataset' && (
                <EvaluationDataset evaluation={evaluation} />
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
