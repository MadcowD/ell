import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiFilter, FiPlusCircle } from 'react-icons/fi';
import { useEvaluations, useLatestEvaluations } from '../hooks/useBackend';
import GenericPageLayout from '../components/layouts/GenericPageLayout';
import { Card, CardHeader, CardContent } from '../components/common/Card';
import { ScrollArea } from '../components/common/ScrollArea';
import { Button } from '../components/common/Button';
import EvaluationCard from '../components/evaluations/EvaluationCard';

const Evaluations = () => {
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('All');
  const [showAllVersions, setShowAllVersions] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10;

  const { data: allEvaluations, isLoading: isLoadingAll } = useEvaluations(currentPage, pageSize);
  const { data: latestEvaluations, isLoading: isLoadingLatest } = useLatestEvaluations(currentPage, pageSize);

  const evaluations = showAllVersions ? allEvaluations : latestEvaluations;
  const isLoading = showAllVersions ? isLoadingAll : isLoadingLatest;

  const filteredEvaluations = useMemo(() => {
    if (!evaluations) return [];
    return evaluations.filter(evl => 
      evl.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (selectedFilter === 'All' || evl.status === selectedFilter)
    );
  }, [evaluations, searchTerm, selectedFilter]);

  const handleCreateEvaluation = () => {
    // Navigate to evaluation creation page or open a modal
    navigate('/evaluations/create');
  };

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!evaluations || evaluations.length === 0) {
    return (
      <GenericPageLayout showSidebar={false}>
        <div className="bg-background text-foreground p-6">
          <Card className="w-3/4 max-w-2xl mx-auto">
            <CardHeader>
              <h2 className="text-2xl font-semibold text-foreground">No Evaluations Found</h2>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground mb-4">
                It looks like you don't have any evaluations set up yet.
              </p>
              <p className="text-muted-foreground mb-4">
                To get started with evaluating your LMPs, try the following example:
              </p>
              <pre className="bg-muted p-4 rounded-md overflow-x-auto">
                <code className="text-sm">
{`import ell
from ell import Evaluation

ell.init(store='./logdir')

@ell.simple(model="gpt-4o")
def mylmp(greeting: str):
    return f"Say hi there!"

def metric(datapoint, output):
    return 1 if output == "Hi there!" else 0

# Initialize your evaluation
eval = Evaluation(
    name="basic-eval",
    dataset=[{"input": ["Hello"], "expected": "Hi there!"}],
    metrics={"score": metric}
)


# Run the evaluation
results = eval.run(mylmp)`}
                </code>
              </pre>
              <p className="text-muted-foreground mt-4">
                Run this script, then refresh this page to see your first evaluation.
              </p>
            </CardContent>
          </Card>
        </div>
      </GenericPageLayout>
    );
  }

  return (
    <GenericPageLayout showSidebar={false}>
      <div className="bg-background text-foreground p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold">Evaluations</h1>
          <Button  className="disabled bg-primary text-primary-foreground opacity-50 cursor-not-allowed">
            <FiPlusCircle className="mr-2" />
            Create Evaluation
          </Button>
        </div>

        <div className="mb-6 flex items-center space-x-4">
          <div className="relative flex-grow">
            <input
              type="text"
              placeholder="Search evaluations..."
              className="w-full pl-10 pr-4 py-2 bg-input text-foreground rounded-md"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
          </div>
          <select
            className="bg-input text-foreground px-3 py-2 rounded-md"
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
          >
            <option value="All">All</option>
            <option value="Active">Active</option>
            <option value="Completed">Completed</option>
            <option value="Draft">Draft</option>
          </select>
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="showAllVersions"
              checked={showAllVersions}
              onChange={(e) => setShowAllVersions(e.target.checked)}
              className="rounded border-input"
            />
            <label htmlFor="showAllVersions" className="text-sm">
              Show all versions
            </label>
          </div>
        </div>

        <ScrollArea className="h-[calc(100vh-200px)]">
          <div className="space-y-4">
            {filteredEvaluations.map((evaluation) => (
              <EvaluationCard key={evaluation.id} evaluation={evaluation} />
            ))}
          </div>
        </ScrollArea>

        {filteredEvaluations.length === 0 && (
          <Card className="mt-4">
            <CardContent className="text-center py-8">
              <p className="text-muted-foreground">No evaluations found. Create a new evaluation to get started.</p>
            </CardContent>
          </Card>
        )}
      </div>
    </GenericPageLayout>
  );
};

export default Evaluations;
