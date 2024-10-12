import React from 'react';
import { FiZap, FiBarChart2, FiDatabase, FiTag, FiClock } from 'react-icons/fi';
import { Card, CardContent } from '../common/Card';
import MetricTable from './MetricTable';
import { getTimeAgo } from '../../utils/lmpUtils';

function EvaluationDetailsSidebar({ evaluation }) {
  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold mb-2">Evaluation Details</h3>
          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
            <div className="flex items-center">
              <FiZap className="mr-2 h-4 w-4" />
              <span>{evaluation?.runs.length} runs</span>
            </div>
            <div className="flex items-center">
              <FiBarChart2 className="mr-2 h-4 w-4" />
              <span>{evaluation?.n_evals} datapoints</span>
            </div>
            <div className="flex items-center">
              <FiDatabase className="mr-2 h-4 w-4" />
              <span>Dataset: {evaluation?.dataset_hash.substring(0, 8)}</span>
            </div>
            <div className="flex items-center">
              <FiTag className="mr-2 h-4 w-4" />
              <span>{evaluation?.labelers.length} metrics</span>
            </div>
            <div className="flex items-center col-span-2">
              <FiClock className="mr-2 h-4 w-4" />
              <span>Created: {getTimeAgo(new Date(evaluation?.created_at))}</span>
            </div>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="p-4">
          <h3 className="text-lg font-semibold mb-2">Metrics</h3>
          {evaluation && (
            <MetricTable 
              summaries={evaluation.runs[evaluation.runs.length - 1].labeler_summaries.filter(summary => summary.is_scalar)}
              historicalData={evaluation.runs.reduce((acc, run) => {
                run.labeler_summaries.forEach(summary => {
                  if (!acc[summary.evaluation_labeler_id]) {
                    acc[summary.evaluation_labeler_id] = [];
                  }
                  acc[summary.evaluation_labeler_id].push(summary.data);
                });
                return acc;
              }, {})}
              isVertical={true}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default EvaluationDetailsSidebar;
