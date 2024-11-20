import React, { useState } from 'react';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import MetricTable from './MetricTable';

const RunSummary = ({ groupedRuns, isVertical }) => {
  const latestRuns = Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  const mostRecentRun = latestRuns.reduce((latest, current) => 
    new Date(current.end_time) > new Date(latest.end_time) ? current : latest
  );

  const scalarSummaries = mostRecentRun.labeler_summaries.filter(summary => summary.is_scalar);

  const historicalData = scalarSummaries.reduce((acc, summary) => {
    acc[summary.evaluation_labeler_id] = groupedRuns[mostRecentRun.evaluated_lmp.name]
      .map(run => run.labeler_summaries
        .find(s => s.evaluation_labeler_id === summary.evaluation_labeler_id)?.data
      )
      .filter(Boolean);
    return acc;
  }, {});

  return (
    <div className="text-xs run-summary-container">
      <LMPCardTitle 
        lmp={mostRecentRun.evaluated_lmp} 
        displayVersion 
        showInvocationCount={true} 
        additionalClassName="text-xs mb-2" 
        paddingClassOverride='p-2'
        shortVersion={true}
      />
      <MetricTable 
        summaries={scalarSummaries}
        historicalData={historicalData}
        isVertical={isVertical}
      />
    </div>
  );
};

export default RunSummary;