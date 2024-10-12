import React, { useState, useCallback } from 'react';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Card } from '../common/Card';
import Graph from '../graphing/Graph';
import { GraphProvider } from '../graphing/GraphSystem';
import MetricDisplay from './MetricDisplay';

const MetricGraphGrid = ({ evaluation, groupedRuns }) => {
  const [activeIndex, setActiveIndex] = useState(null);

  const getHistoricalData = (labeler) => {
    return Object.values(groupedRuns).flatMap(runs => 
      runs.map(run => {
        const summary = run.labeler_summaries.find(s => s.evaluation_labeler_id === labeler.id);
        return summary ? summary.data.mean : null;
      }).filter(Boolean)
    );
  };

  const xData = Array.from({ length: getHistoricalData(evaluation.labelers[0]).length }, (_, i) => `Run ${i + 1}`);

  const handleHover = useCallback((index) => {
    setActiveIndex(index);
  }, []);

  const handleLeave = useCallback(() => {
    setActiveIndex(null);
  }, []);

  return (
    <GraphProvider 
      xData={xData} 
      sharedConfig={{ 
        title: 'Evaluation Metrics', 
        options: {
          plugins: {
            title: { display: false },
            legend: { display: false },
          }
        } 
      }} 
      onHover={handleHover}
      onLeave={handleLeave}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {evaluation.labelers.map((labeler) => {
          const historicalData = getHistoricalData(labeler);
          if (historicalData.length === 0) return null;

          const graphId = `labeler-${labeler.id}`;
          const trend = historicalData[historicalData.length - 1] - historicalData[0];
          const trendColor = trend > 0 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(239, 68, 68, 0.8)';
          const fillColor = trend > 0 ? 'rgba(52, 211, 153, 0.2)' : 'rgba(239, 68, 68, 0.2)';

          const metrics = [
            {
              label: labeler.name,
              yData: historicalData,
              color: trendColor,
              config: {
                backgroundColor: fillColor,
                borderColor: trendColor,
                fill: true,
                tension: 0.4,
                borderWidth: 1,
                pointRadius: 3,
              }
            }
          ];
          const currentValue = activeIndex !== null && activeIndex < historicalData.length
            ? historicalData[activeIndex]
            : historicalData[historicalData.length - 1] || null;
          const previousValue = activeIndex !== null && activeIndex > 0
            ? historicalData[activeIndex - 1]
            : currentValue;

          return (
            <Card key={labeler.id}>
              <div className="border-b border-gray-800 flex justify-between items-center p-2">
                <LMPCardTitle
                  lmp={labeler.labeling_lmp}
                  nameOverridePrint={labeler.name}
                  displayVersion
                  showInvocationCount={false}
                  additionalClassName="text-xs"
                  paddingClassOverride="p-0"
                  shortVersion={true}
                />
                <MetricDisplay
                  currentValue={currentValue}
                  previousValue={previousValue}
                  label={labeler.name}
                />
              </div>
              <div className="p-4">
                <Graph
                  graphId={graphId}
                  metrics={metrics}
                />
              </div>
            </Card>
          );
        })}
      </div>
    </GraphProvider>
  );
};

export default MetricGraphGrid;
