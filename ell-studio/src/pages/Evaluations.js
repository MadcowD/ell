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
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10;

  const { data: evaluations, isLoading } = useLatestEvaluations(currentPage, pageSize);

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

  return (
    <GenericPageLayout showSidebar={false}>
      <div className="bg-background text-foreground p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold">Evaluations</h1>
          <Button onClick={handleCreateEvaluation} className="bg-primary text-primary-foreground">
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
