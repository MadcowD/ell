import React, { useMemo } from 'react';
import { Card } from '../../common/Card';
import { Link } from 'react-router-dom';
import { LMPCardTitle } from '../../depgraph/LMPCardTitle';
import Graph from '../../graphing/Graph';
import { GraphProvider } from '../../graphing/GraphSystem';
import MetricDisplay from '../MetricDisplay';

function EvaluationRunMetrics({ run, results, fullResults }) {
  // Use fullResults (unfiltered) to determine axis scales
  const { histogramDataMap, axisScales } = useMemo(() => {
    if(!results) return { histogramDataMap: null, axisScales: null };
    
    const dataMap = new Map();
    const scales = new Map();
    
    run?.labeler_summaries?.forEach(summary => {
      const labelerId = summary.evaluation_labeler_id;
      
      // Get values from the full dataset to determine scales
      const allValues = (fullResults || results)
        .flatMap(result => 
          result.labels
            .filter(label => label.labeler_id === labelerId)
            .map(label => label.label_invocation?.contents?.results)
        )
        .filter(value => typeof value === 'number' || typeof value === 'boolean');

      if (allValues.length === 0) return;

      // Calculate global min and max from full dataset
      const globalMin = Math.min(...allValues);
      const globalMax = Math.max(...allValues);
      
      scales.set(labelerId, { min: globalMin, max: globalMax });

      // Now get values from filtered results for the histogram
      const filteredValues = results
        .flatMap(result => 
          result.labels
            .filter(label => label.labeler_id === labelerId)
            .map(label => label.label_invocation?.contents?.results)
        )
        .filter(value => typeof value === 'number' || typeof value === 'boolean');

      if (filteredValues.length === 0) return;

      // Use global min/max for binning, even with filtered data
      if (globalMin === globalMax) {
        const padding = Math.abs(globalMin * 0.1) || 0.1;
        dataMap.set(labelerId, {
          binLabels: [(globalMin - padding).toFixed(2), globalMin.toFixed(2), (globalMin + padding).toFixed(2)],
          counts: [0, filteredValues.length, 0]
        });
        return;
      }

      const numBins = 10;
      const binWidth = (globalMax - globalMin) / numBins;
      
      const histogramData = Array(numBins).fill(0);
      
      filteredValues.forEach(value => {
        const binIndex = Math.min(
          Math.floor((value - globalMin) / binWidth),
          numBins - 1
        );
        if (binIndex >= 0 && binIndex < numBins) {
          histogramData[binIndex]++;
        }
      });

      const binLabels = Array.from({ length: numBins }, (_, i) => {
        const binStart = globalMin + (i * binWidth);
        return ((binStart + (binStart + binWidth)) / 2).toFixed(2);
      });

      dataMap.set(labelerId, {
        binLabels,
        counts: histogramData
      });
    });

    return { histogramDataMap: dataMap, axisScales: scales };
  }, [results, fullResults, run?.labeler_summaries]);

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
                grid: { display: false },
                offset: true,
                ticks: {
                  autoSkip: false
                }
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
            const histogramData = histogramDataMap?.get(summary.evaluation_labeler_id);
            const scale = axisScales?.get(summary.evaluation_labeler_id);
            
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
                    options={{
                      scales: {
                        x: {
                          min: scale.min,
                          max: scale.max
                        }
                      }
                    }}
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