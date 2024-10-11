import React from 'react';
import { FiArrowUp, FiArrowDown, FiZap } from 'react-icons/fi';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
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
          <span className={`flex items-center ${color} text-xs`}>
            <Icon className="mr-0.5 h-3 w-3" />
            {Math.abs(percentChange).toFixed(1)}%
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <div className="text-xs">
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
        <span className="flex items-baseline text-xs">
          {value.toFixed(2)}
          <span className="ml-0.5 text-[8px] text-gray-400 border-b border-dotted border-gray-400 leading-[1.3]">±{stdDev.toFixed(2)}</span>
        </span>
      </TooltipTrigger>
      <TooltipContent>
        <div className="text-xs">
          <p>Mean: {value.toFixed(4)}</p>
          <p>Standard Deviation: {stdDev.toFixed(4)}</p>
          <p>Number of Datapoints: {n}</p>
        </div>
      </TooltipContent>
    </Tooltip>
  </TooltipProvider>
);

const RunSummary = ({ groupedRuns }) => {
  const latestRuns = Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  const mostRecentRun = latestRuns.reduce((latest, current) => 
    new Date(current.end_time) > new Date(latest.end_time) ? current : latest
  );

  const previousRun = groupedRuns[`${mostRecentRun.evaluated_lmp.name}`]
    .slice(-2, -1)[0];

  return (
    <div className="text-xs">
      <LMPCardTitle 
        lmp={mostRecentRun.evaluated_lmp} 
        displayVersion 
        showInvocationCount={true} 
        additionalClassName="text-[10px] mb-1" 
        paddingClassOverride='p-0'
      />
      <div className="space-y-1">
        {mostRecentRun.labeler_summaries.map(summary => {
          if (!summary.is_scalar) return null;
          const previousSummary = previousRun?.labeler_summaries.find(
            s => s.evaluation_labeler_id === summary.evaluation_labeler_id
          );
          const currentValue = summary.data.mean;
          const previousValue = previousSummary?.data.mean || 0;

          return (
            <div key={summary.evaluation_labeler_id} className="flex items-center justify-between">
              <span className="font-medium truncate mr-2" title={summary.evaluation_labeler.name}>
                {summary.evaluation_labeler.name}:
              </span>
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
    </div>
  );
};

export default RunSummary;