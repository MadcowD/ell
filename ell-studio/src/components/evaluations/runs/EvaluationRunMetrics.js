import React, { useMemo } from 'react';
import { Card } from '../../common/Card';
import { Link } from 'react-router-dom';
import { LMPCardTitle } from '../../depgraph/LMPCardTitle';
import Graph from '../../graphing/Graph';
import { GraphProvider } from '../../graphing/GraphSystem';
import MetricDisplay from '../MetricDisplay';

function EvaluationRunMetrics({ run, results }) {
  // Cache histogram data for all labelers
  const histogramDataMap = useMemo(() => {
    // if (!results) return new Map();
    if(!results) return null;
    
    const dataMap = new Map();
    
    run?.labeler_summaries?.forEach(summary => {
      const labelerId = summary.evaluation_labeler_id;
      
      // Extract all numeric values for this labeler
      const values = results
        .flatMap(result => 
          result.labels
            .filter(label => label.labeler_id === labelerId)
            .map(label => label.label_invocation?.contents?.results)
        )
        .filter(value => typeof value === 'number' || typeof value === 'boolean');

      if (values.length === 0) return;

      // Calculate min and max from actual values
      const min = Math.min(...values);
      const max = Math.max(...values);
      
      // Create 10 bins spanning the range
      const numBins = 10;
      const binWidth = (max - min) / numBins;
      
      // Initialize histogram data
      const histogramData = Array(numBins).fill(0);
      
      // Count values in each bin
      values.forEach(value => {
        const binIndex = Math.min(
          Math.floor((value - min) / binWidth),
          numBins - 1
        );
        if (binIndex >= 0 && binIndex < numBins) {
          histogramData[binIndex]++;
        }
      });

      // Create bin labels
      const binLabels = Array.from({ length: numBins }, (_, i) => {
        const binStart = min + (i * binWidth);
        return ((binStart + (binStart + binWidth)) / 2).toFixed(2);
      });

      dataMap.set(labelerId, {
        binLabels,
        counts: histogramData
      });
    });

    return dataMap;
  }, [results, run?.labeler_summaries]); // Only recalculate when results or summaries change
  console.log(histogramDataMap)

  if(!results) return null;
  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Metrics</h2>
      <GraphProvider 
        shared={false}
        sharedConfig={{ 
          options: {
            animation: { duration: 400 },
            plugins: {
              title: { display: false },
              legend: { display: false },
              tooltip: { enabled: true },
            },
            scales: {
              x: {
                display: true,
                title: {
                  display: true,
                  text: 'Value'
                },
                grid: { display: false }
              },
              y: {
                display: true,
                title: {
                  display: true,
                  text: 'Frequency'
                },
                beginAtZero: true,
                grid: { display: true }
              }
            }
          } 
        }}
      >
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {run?.labeler_summaries?.map((summary, index) => {
            const histogramData = histogramDataMap.get(summary.evaluation_labeler_id);
            console.log(histogramData)
            // Skip if we don't have histogram data
            if (!histogramData) return null;
            
            return (
              <Card key={index} className="p-4">
                <div className="flex justify-between items-center border-b border-gray-800 pb-2">
                  <Link to={`/lmp/${summary.evaluation_labeler?.labeling_lmp?.name}/${summary.evaluation_labeler?.labeling_lmp?.lmp_id}`}>
                    <LMPCardTitle
                      lmp={summary.evaluation_labeler?.labeling_lmp}
                      nameOverridePrint={summary.evaluation_labeler.name}
                      displayVersion
                      showInvocationCount={false}
                      additionalClassName="text-xs"
                      paddingClassOverride="p-0"
                      shortVersion={true}
                    />
                  </Link>
                  <MetricDisplay
                    currentValue={summary.data.mean}
                    label={summary.name}
                  />
                </div>
                <div className="mt-4">
                  <Graph
                    graphId={`histogram-${summary.evaluation_labeler_id}`}
                    type="histogram"
                    metrics={[
                      {
                        label: summary.name,
                        yData: histogramData.counts,
                        xData: histogramData.binLabels,
                        color: 'rgba(52, 211, 153, 0.8)',
                        config: {
                          backgroundColor: 'rgba(52, 211, 153, 0.2)',
                          borderColor: 'rgba(52, 211, 153, 0.8)',
                          borderWidth: 1,
                        }
                      }
                    ]}
                  />
                </div>
              </Card>
            );
          })}
        </div>
      </GraphProvider>
    </div>
  );
}

export default EvaluationRunMetrics;