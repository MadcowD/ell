import React from 'react';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import RunSummary from './RunSummary';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';
import MetricGraphGrid from './MetricGraphGrid';

function EvaluationOverview({ evaluation, groupedRuns }) {
  return (
    <>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">
          Evaluation
          <span className="text-muted-foreground mx-2">•</span>
          <VersionBadge version={evaluation.version_number} />
        </h2>
        <MetricGraphGrid evaluation={evaluation} groupedRuns={groupedRuns} />
      </div>
    </>
  );
}

export default EvaluationOverview;
