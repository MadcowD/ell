import React from 'react';
import { FiUsers, FiCheckCircle, FiArrowUp, FiArrowDown, FiInfo } from 'react-icons/fi';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Card } from '../common/Card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../common/Tooltip';

const getPercentageChange = (current, previous) => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

const MetricChange = ({ current, previous }) => {
  const percentChange = getPercentageChange(current, previous);
  const isPositive = percentChange > 0;
  const color = isPositive ? 'text-green-600' : 'text-red-600';
  const Icon = isPositive ? FiArrowUp : FiArrowDown;

  return (
    <span className={`flex items-center ${color}`}>
      <Icon className="mr-1" />
      {(current - previous).toFixed(2)} ({Math.abs(percentChange).toFixed(2)}%)
    </span>
  );
};

const MetricValue = ({ value, stdDev }) => (
  <TooltipProvider>
    <Tooltip>
      <TooltipTrigger asChild>
        <span className="flex items-center cursor-help">
          {value.toFixed(2)} <FiInfo className="ml-1 text-gray-400" size={12} />
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <p>Mean: {value.toFixed(2)}</p>
        <p>Std Dev: {stdDev.toFixed(2)}</p>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
);

const RunSummary = ({ groupedRuns, totalRuns, successfulRuns }) => {
  const latestRuns = Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  const mostRecentRun = latestRuns.reduce((latest, current) => 
    new Date(current.end_time) > new Date(latest.end_time) ? current : latest
  );

  const previousRun = groupedRuns[`${mostRecentRun.evaluated_lmp.name}.${mostRecentRun.evaluated_lmp.lmp_id}`]
    .slice(-2, -1)[0];

  return (
    <div className="border-t pt-4 mt-4">
      <h3 className="text-sm font-semibold mb-2">Latest Run Summary</h3>
      <div className="grid grid-cols-2 gap-4 text-sm mb-4">
        <div className="flex items-center">
          <FiUsers className="mr-2" />
          <span>{totalRuns} total runs</span>
        </div>
        <div className="flex items-center">
          <FiCheckCircle className="mr-2" />
          <span>{successfulRuns} successful</span>
        </div>
      </div>

      <Card className="p-2 mb-4">
        <h4 className="text-xs font-semibold mb-2">Most Recently Evaluated LMP</h4>
        <LMPCardTitle 
          lmp={mostRecentRun.evaluated_lmp} 
          displayVersion 
          showInvocationCount={true} 
          additionalClassName="text-xs" 
          paddingClassOverride='p-2'
        />
        <div className="mt-2 space-y-2">
          {mostRecentRun.labeler_summaries.map(summary => {
            if (!summary.is_scalar) return null;
            const previousSummary = previousRun?.labeler_summaries.find(
              s => s.evaluation_labeler_id === summary.evaluation_labeler_id
            );
            const currentValue = summary.data.mean;
            const previousValue = previousSummary?.data.mean || 0;

            return (
              <div key={summary.evaluation_labeler_id} className="flex justify-between items-center text-xs">
                <span className="font-medium">{summary.evaluation_labeler.name}:</span>
                <div className="flex items-center space-x-2">
                  <MetricValue value={currentValue} stdDev={summary.data.std} />
                  {previousRun && (
                    <MetricChange current={currentValue} previous={previousValue} />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
};

export default RunSummary;