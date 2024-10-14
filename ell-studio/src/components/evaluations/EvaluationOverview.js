import React, { useState } from 'react';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import RunSummary from './RunSummary';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';
import MetricGraphGrid from './MetricGraphGrid';

function EvaluationOverview({ evaluation, groupedRuns, onActiveIndexChange }) {
  const [activeIndex, setActiveIndex] = useState(null);

  const handleActiveIndexChange = (index) => {
    setActiveIndex(index);
    onActiveIndexChange(index);
  };

  return (
    <>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">
          Evaluation
          <span className="text-muted-foreground mx-2">•</span>
          <VersionBadge version={evaluation.version_number} />
        </h2>
        {evaluation.labelers ? (
          <MetricGraphGrid 
            evaluation={evaluation} 
            groupedRuns={groupedRuns} 
            onActiveIndexChange={handleActiveIndexChange}
          />
        ) : (
          <div className="animate-pulse">
            <div className="h-4 bg-gray-300 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-300 rounded w-1/4"></div>
          </div>
        )}
      </div>
    </>
  );
}

export default EvaluationOverview;
