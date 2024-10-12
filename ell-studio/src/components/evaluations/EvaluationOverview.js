import React from 'react';
import { FiBarChart2, FiClock, FiDatabase, FiTag, FiZap } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import RunSummary from './RunSummary';
import VersionBadge from '../VersionBadge';
import { getTimeAgo } from '../../utils/lmpUtils';

function EvaluationOverview({ evaluation, groupedRuns }) {
  return (
    <>
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Evaluation
        <span className="text-muted-foreground mx-2">•</span>
        <VersionBadge version={evaluation.version_number } />
        </h2>
      </div>
    </>
  );
}

export default EvaluationOverview;
