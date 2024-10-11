import React, { useRef, useState, useEffect, useLayoutEffect } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Tooltip as ChartTooltip, Filler } from 'chart.js';
import { LMPCardTitle } from '../depgraph/LMPCardTitle';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '../common/Tooltips';
import { FiTrendingUp, FiTrendingDown, FiMinus, FiBarChart2 } from 'react-icons/fi';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, ChartTooltip, Filler);

const getColorForTrend = (trend) => {
  if (trend > 0) return 'text-emerald-400';
  if (trend < 0) return 'text-rose-400';
  return 'text-gray-400';
};

const getTrendIcon = (trend) => {
  if (trend > 0) return <FiTrendingUp className="inline-block mr-1" />;
  if (trend < 0) return <FiTrendingDown className="inline-block mr-1" />;
  return <FiMinus className="inline-block mr-1" />;
};

const calculateConfidence = (current, previous, currentStdDev, previousStdDev, n) => {
  if (previous === undefined || previous === null) return 0;
  const pooledStdDev = Math.sqrt((currentStdDev**2 + previousStdDev**2) / 2);
  const standardError = pooledStdDev * Math.sqrt(2/n);
  const zScore = Math.abs(current - previous) / standardError;
  const confidence = (1 - 2 * (1 - pnorm(zScore))) * 100;
  return confidence;
};

const pnorm = (x) => {
  const t = 1 / (1 + 0.2316419 * Math.abs(x));
  const d = 0.3989423 * Math.exp(-x * x / 2);
  let p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
  if (x > 0) p = 1 - p;
  return p;
};

const MetricChart = ({ data, hoverIndex, onHover }) => {
  const chartRef = useRef(null);

  const trend = data[data.length - 1] - data[0];
  const trendColor = trend > 0 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(239, 68, 68, 0.8)';
  const fillColor = trend > 0 ? 'rgba(52, 211, 153, 0.2)' : 'rgba(239, 68, 68, 0.2)';

  const chartData = {
    labels: data.map((_, index) => index + 1),
    datasets: [{
      data,
      borderColor: trendColor,
      backgroundColor: fillColor,
      pointRadius: 0,
      borderWidth: 1,
      tension: 0.4,
      fill: true,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: { enabled: false }
    },
    scales: { 
      x: { display: false }, 
      y: { 
        display: false,
        min: Math.min(...data) * 0.95,
        max: Math.max(...data) * 1.05,
      } 
    },
  };

  return (
    <div 
      className="w-full h-5"
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.round((x / rect.width) * (data.length - 1));
        onHover(index);
      }}
      onMouseLeave={() => onHover(null)}
    >
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
};

const MetricDisplay = ({ summary, historicalData, isVertical }) => {
  const [hoverIndex, setHoverIndex] = useState(null);

  const currentValue = hoverIndex !== null ? historicalData[hoverIndex].mean : summary.data.mean;
  const previousValue = historicalData[historicalData.length - 2]?.mean;
  
  const percentChange = previousValue !== undefined && previousValue !== 0
    ? ((currentValue - previousValue) / Math.abs(previousValue) * 100).toFixed(1)
    : (currentValue !== 0 ? '100.0' : '0.0');

  const trendColor = getColorForTrend(parseFloat(percentChange));
  const trendIcon = getTrendIcon(parseFloat(percentChange));
  const confidence = calculateConfidence(
    currentValue,
    previousValue,
    summary.data.std,
    historicalData[historicalData.length - 2]?.std || 0,
    summary.count
  );

  return (
    <TooltipProvider delayDuration={300}>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={`flex flex-col space-y-1 text-xs py-1 hover:bg-accent/50 transition-colors duration-200`}>
            <div className={`w-full  font-medium truncate flex items-center`} title={summary.evaluation_labeler.name}>
              <FiBarChart2 className="mr-1 h-3 w-3 text-muted-foreground flex-shrink-0" />
              <code className="metric-label text-xs font-medium truncate max-w-[calc(100%-1.5rem)]">
                {summary.evaluation_labeler.name}
              </code>
            </div>
            <div className={`w-full flex items-center justify-between md:justify-end space-x-2`}>
              <div className="w-full min-w-[100px] max-w-[200px]">
                <MetricChart 
                  data={historicalData.map(d => d.mean)} 
                  hoverIndex={hoverIndex}
                  onHover={setHoverIndex}
                />
              </div>
              <div className="text-right min-w-[3rem]">
                <div className="font-bold font-mono">{currentValue.toFixed(2)}</div>
                <div className={`text-[10px] ${trendColor}`}>
                  {trendIcon}
                  {Math.abs(parseFloat(percentChange)).toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent sideOffset={25}>
          <div className="text-xs">
            <p className="font-medium">{summary.evaluation_labeler.name}</p>
            <p>Current: {currentValue.toFixed(4)} (±{summary.data.std.toFixed(4)})</p>
            <p>Previous: {previousValue !== undefined ? previousValue.toFixed(4) : 'N/A'}</p>
            <p>Change: {previousValue !== undefined ? (currentValue - previousValue).toFixed(4) : 'N/A'}</p>
            <p>Confidence: {confidence.toFixed(2)}%</p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
};

const RunSummary = ({ groupedRuns, isVertical }) => {
  const latestRuns = Object.values(groupedRuns).map(runs => runs[runs.length - 1]);
  const mostRecentRun = latestRuns.reduce((latest, current) => 
    new Date(current.end_time) > new Date(latest.end_time) ? current : latest
  );

  const scalarSummaries = mostRecentRun.labeler_summaries.filter(summary => summary.is_scalar);

  return (
    <div className="text-xs run-summary-container">
      <LMPCardTitle 
        lmp={mostRecentRun.evaluated_lmp} 
        displayVersion 
        showInvocationCount={true} 
        additionalClassName="text-xs mb-2" 
        paddingClassOverride='p-2'
      />
      <div className="pt-0 p-2 grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2">
        {scalarSummaries.map((summary, index) => {
          const historicalData = groupedRuns[mostRecentRun.evaluated_lmp.name]
            .map(run => run.labeler_summaries
              .find(s => s.evaluation_labeler_id === summary.evaluation_labeler_id)?.data
            )
            .filter(Boolean);

          return (
            <React.Fragment key={summary.evaluation_labeler_id}>
              <MetricDisplay 
                summary={summary}
                historicalData={historicalData}
                isVertical={isVertical}
              />
              {index < scalarSummaries.length - 1 && (
                <div className="border-b border-gray-900 my-0 md:hidden" />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};

export default RunSummary;