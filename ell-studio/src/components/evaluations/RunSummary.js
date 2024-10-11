import React from 'react';
import { FiUsers, FiCheckCircle, FiArrowUp, FiArrowDown } from 'react-icons/fi';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Card } from '../common/Card';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../common/Tooltips';

const getPercentageChange = (current, previous) => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

const calculateConfidence = (current, previous, currentStdDev, previousStdDev, n) => {
  const pooledStdDev = Math.sqrt((currentStdDev**2 + previousStdDev**2) / 2);
  const standardError = pooledStdDev * Math.sqrt(2/n);
  const zScore = Math.abs(current - previous) / standardError;
  const confidence = (1 - 2 * (1 - pnorm(zScore))) * 100;
  return confidence;
};

// Approximation of the cumulative distribution function for the standard normal distribution
const pnorm = (x) => {
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989423 * Math.exp(-x * x / 2);
  let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  if (x > 0) p = 1 - p;
  return p;
};

const MetricChange = ({ current, previous, currentStdDev, previousStdDev, n }) => {
  const percentChange = getPercentageChange(current, previous);
  const isPositive = percentChange > 0;
  const color = isPositive ? 'text-green-600' : 'text-red-600';
  const Icon = isPositive ? FiArrowUp : FiArrowDown;
  const confidence = calculateConfidence(current, previous, currentStdDev, previousStdDev, n);

  return (
    <TooltipProvider delayDuration={50}>
      <Tooltip>
        <TooltipTrigger asChild>
          <span className={`flex items-center ${color} cursor-help`}>
            <Icon className="mr-1" />
            {(current - previous).toFixed(2)} ({Math.abs(percentChange).toFixed(2)}%)

          </span>
        </TooltipTrigger>
        <TooltipContent>
          <div>
            <p>Change: {(current - previous).toFixed(4)}</p>
            <p>Percentage Change: {percentChange.toFixed(2)}%</p>
            <p>Confidence: {confidence.toFixed(2)}%</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const MetricValue = ({ value, stdDev, n }) => (
  <TooltipProvider>
    <Tooltip delayDuration={0}>
      <TooltipTrigger asChild>
        <span className="flex items-baseline cursor-help">
          {value.toFixed(2)}
          <span className="ml-1  text-[8px] text-gray-400 border-b border-dotted border-gray-400 leading-[1.3]">±{stdDev.toFixed(2)}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <div>
          <p>Mean: {value.toFixed(4)}</p>
          <p>Standard Deviation: {stdDev.toFixed(4)}</p>
          <p>Number of Datapoints: {n}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
);

const RunSummary = ({ groupedRuns, totalRuns, successfulRuns }) => {
  const latestRuns = Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  const mostRecentRun = latestRuns.reduce((latest, current) => 
    new Date(current.end_time) > new Date(latest.end_time) ? current : latest
  );

  const previousRun = groupedRuns[`${mostRecentRun.evaluated_lmp.name}`]
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
                  <MetricValue value={currentValue} stdDev={summary.data.std} n={summary.count} />
                  {previousRun && (
                    <MetricChange 
                      current={currentValue} 
                      previous={previousValue} 
                      currentStdDev={summary.data.std}
                      previousStdDev={previousSummary?.data.std || 0}
                      n={summary.count}
                    />
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