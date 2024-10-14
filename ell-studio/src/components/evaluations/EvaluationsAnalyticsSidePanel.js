import React, { useMemo } from 'react';
import { FiBarChart2, FiClock, FiDatabase } from 'react-icons/fi';

const EvaluationsAnalyticsSidePanel = ({ evaluations }) => {
  const analytics = useMemo(() => {
    const totalEvaluations = evaluations.length;
    const activeEvaluations = evaluations.filter(e => e.status === 'Active').length;
    const completedEvaluations = evaluations.filter(e => e.status === 'Completed').length;
    const totalDatapoints = evaluations.reduce((sum, e) => sum + e.n_evals, 0);
    
    return { totalEvaluations, activeEvaluations, completedEvaluations, totalDatapoints };
  }, [evaluations]);

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-lg font-semibold text-foreground mb-4">Evaluation Analytics</h2>
      
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Total Evaluations</span>
          <span className="text-foreground font-medium">{analytics.totalEvaluations}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Active Evaluations</span>
          <span className="text-foreground font-medium">{analytics.activeEvaluations}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Completed Evaluations</span>
          <span className="text-foreground font-medium">{analytics.completedEvaluations}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Total Datapoints</span>
          <span className="text-foreground font-medium">{analytics.totalDatapoints}</span>
        </div>
      </div>

      {/* You can add more analytics or charts here */}
    </div>
  );
};

export default EvaluationsAnalyticsSidePanel;