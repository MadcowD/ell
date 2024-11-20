import React, { useState, useCallback } from 'react';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Card } from '../common/Card';
import Graph from '../graphing/Graph';
import { GraphProvider } from '../graphing/GraphSystem';
import MetricDisplay from './MetricDisplay';
import { Link } from 'react-router-dom';

const MetricGraphGrid = ({ evaluation, groupedRuns, onActiveIndexChange }) => {
  const [activeIndex, setActiveIndex] = useState(null);

  const getHistoricalData = (labeler) => {
    if (!labeler) return { means: [], stdDevs: [], errors: [], confidenceIntervals: [] };
    return Object.values(groupedRuns).reduce((acc, runs) => {
      runs.forEach(run => {
        const summary = run.labeler_summaries.find(s => s.evaluation_labeler_id === labeler.id);
        if (summary) {
          const { mean, std, min, max } = summary.data;
          const count = summary.count;
          console.log(count)
          
          // Calculate Standard Error of the Mean (SEM)
          const sem = std / Math.sqrt(count);
          
          // Z-score for 95% confidence
          const zScore = 1.96;
          
          // Margin of Error
          let marginOfError = zScore * sem;
          
          // Bounded Confidence Interval
          let lowerBound = Math.max(mean - marginOfError, min);
          let upperBound = Math.min(mean + marginOfError, max);
          
          acc.means.push(mean);
          acc.stdDevs.push(std);
          acc.errors.push(marginOfError);
          acc.confidenceIntervals.push({ low: lowerBound, high: upperBound });
        }
      });
      return acc;
    }, { means: [], stdDevs: [], errors: [], confidenceIntervals: [] });
  };

  const xData = Array.from({ length: getHistoricalData(evaluation.labelers?.[0]).means.length}, (_, i) => `${i + 1}`);

  const handleHover = useCallback((index) => {
    setActiveIndex(index); 
    onActiveIndexChange(index);
  }, [onActiveIndexChange]);

  const handleLeave = useCallback(() => {
    setActiveIndex(null);
    onActiveIndexChange(null);
  }, [onActiveIndexChange]);

  const hasMultipleValues = getHistoricalData(evaluation.labelers[0]).means.length > 1;
  return (
    <GraphProvider 
      xData={xData} 
      sharedConfig={{ 
        title: 'Evaluation Metrics', 
        options: {
          animation: {
            duration: 400 // Reduce from default 1000ms
          },
          transitions: {
            active: {
              animation: {
                duration: 200 // Faster hover state transitions
              }
            }
          },
          plugins: {
            title: { display: false },
            legend: { display: false },
            tooltip: { 
              enabled: true, 
              intersect: false, 
              position: 'average', 
              // TODO: Make the label custom so when we click it takes us to that run id.
            },
          },
          scales: {
            x: {
              display: true,
              title: {
                display: true,
                text: 'Run Number'
              }
            },
            y: {
              display: true,
              title: {
                display: false
              }
            }
          }
        } 
      }} 
      onHover={handleHover}
      onLeave={handleLeave}
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {evaluation.labelers.map((labeler) => {
          const { means: historicalData, stdDevs, confidenceIntervals } = getHistoricalData(labeler);
          if (historicalData.length === 0) return null;

          const currentValue = activeIndex !== null ? historicalData[activeIndex] : historicalData[historicalData.length - 1];
          const previousValue = activeIndex !== null && activeIndex > 0 ? historicalData[activeIndex - 1] : historicalData[historicalData.length - 2];

          return (
            <Card key={labeler.id}>
              <div className={`flex justify-between items-center p-2 ${hasMultipleValues ? 'border-b border-gray-800' : ''}`}>
                <Link to={`/lmp/${labeler.labeling_lmp.name}/${labeler.labeling_lmp.lmp_id}`}>
                <LMPCardTitle
                  lmp={labeler.labeling_lmp}
                  nameOverridePrint={labeler.name}
                  displayVersion
                  showInvocationCount={false}
                  additionalClassName="text-xs"
                  paddingClassOverride="p-0"
                  shortVersion={true}
                />
                </Link>
                <MetricDisplay
                  currentValue={currentValue}
                  previousValue={previousValue}
                  label={labeler.name}
                />
              </div>
              {hasMultipleValues && (
                <div className="p-4">
                  <Graph
                    graphId={`labeler-${labeler.id}`}
                    metrics={[
                      {
                        label: labeler.name,
                        yData: historicalData,
                        errorBars: confidenceIntervals,
                        color: currentValue > historicalData[0] ? 'rgba(52, 211, 153, 0.8)' : 'rgba(239, 68, 68, 0.8)',
                        config: {
                          backgroundColor: currentValue > historicalData[0] ? 'rgba(52, 211, 153, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                          borderColor: currentValue > historicalData[0] ? 'rgba(52, 211, 153, 0.8)' : 'rgba(239, 68, 68, 0.8)',
                          fill: true,
                          tension: 0.4,
                          borderWidth: 1,
                          pointRadius: 3,
                        }
                      }
                    ]}
                  />
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </GraphProvider>
  );
};

export default MetricGraphGrid;
