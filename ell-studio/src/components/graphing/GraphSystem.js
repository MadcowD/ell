import React, { createContext, useContext, useState, useCallback } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import { SharedVerticalIndicator, useSharedVerticalIndicator } from './SharedVerticalIndicator';
import ErrorBarPlugin from './ErrorBarPlugin';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, ErrorBarPlugin);

const GraphContext = createContext();

export const useGraphContext = () => useContext(GraphContext);

export const GraphProvider = ({ children, xData, sharedConfig, onHover, onLeave, shared = true }) => {
  const [graphs, setGraphs] = useState({});
  const [activeIndicatorIndex, setActiveIndicatorIndex] = useState(null);
  const [sharedIndicatorY, setSharedIndicatorY] = useState(null);

  const addGraph = useCallback((graphId) => {
    setGraphs(prevGraphs => {
      if (!prevGraphs[graphId]) {
        return {
          ...prevGraphs,
          [graphId]: { metrics: [] }
        };
      }
      return prevGraphs;
    });
  }, []);

  const removeGraph = useCallback((graphId) => {
    setGraphs(prevGraphs => {
      const { [graphId]: removed, ...rest } = prevGraphs;
      return rest;
    });
  }, []);

  const addMetric = useCallback((graphId, metric) => {
    setGraphs(prevGraphs => ({
      ...prevGraphs,
      [graphId]: {
        ...prevGraphs[graphId],
        metrics: [...(prevGraphs[graphId]?.metrics || []), metric]
      }
    }));
  }, []);

  const removeMetric = useCallback((graphId, metricId) => {
    setGraphs(prevGraphs => ({
      ...prevGraphs,
      [graphId]: {
        ...prevGraphs[graphId],
        metrics: prevGraphs[graphId]?.metrics.filter(m => m.id !== metricId) || []
      }
    }));
  }, []);

  const setActiveIndicator = useCallback((index, y) => {
    setActiveIndicatorIndex(index);
    setSharedIndicatorY(y);
    if (onHover) {
      onHover(index);
    }
  }, [onHover]);

  const clearActiveIndicator = useCallback(() => {
    setActiveIndicatorIndex(null);
    setSharedIndicatorY(null);
    if (onLeave) {
      onLeave();
    }
  }, [onLeave]);

  return (
    <GraphContext.Provider value={{ 
      xData, 
      graphs, 
      addGraph, 
      removeGraph, 
      addMetric, 
      removeMetric, 
      sharedConfig,
      activeIndicatorIndex,
      sharedIndicatorY,
      setActiveIndicator,
      clearActiveIndicator,
      shared
    }}>
      {children}
    </GraphContext.Provider>
  );
};

export const GraphRenderer = ({ graphId }) => {
  const { 
    xData, 
    graphs, 
    sharedConfig, 
    activeIndicatorIndex, 
    sharedIndicatorY, 
    setActiveIndicator,
    clearActiveIndicator,
    shared
  } = useGraphContext();
  const graph = graphs[graphId];
  const chartRef = React.useRef(null);
  const indicatorState = useSharedVerticalIndicator(chartRef, activeIndicatorIndex, sharedIndicatorY, clearActiveIndicator);
  
  if (!graph || !graph.metrics || graph.metrics.length === 0) {
    return <div>Loading graph...</div>;
  }

  const chartType = graph.metrics[0]?.type || 'line';

  const labels = shared ? xData : graph.metrics[0]?.xData || xData;

  const data = {
    labels,
    datasets: graph.metrics.map(metric => ({
      label: metric.label,
      data: metric.yData,
      xData: metric.xData,
      borderColor: metric.color,
      backgroundColor: chartType === 'line' ? metric.color : `${metric.color}80`,
      errorBars: metric.errorBars,
      barPercentage: chartType === 'histogram' ? 1.0 : 0.9,
      categoryPercentage: chartType === 'histogram' ? 1.0 : 0.8,
      ...metric.config,
    })),
  };

  const hasNonZeroErrorBars = data.datasets.some(dataset => 
    dataset.errorBars && dataset.errorBars.some(error => error > 0 || (error.low - error.high > 0))
  );

  let yAxisScale = {
    ...sharedConfig.options.scales.y,};
  if (hasNonZeroErrorBars || true) {
    const minMaxValues = data.datasets.reduce((acc, dataset) => {
      dataset.data.forEach((value, index) => {
        const errorBar = dataset.errorBars ? dataset.errorBars[index] : 0;
        if (typeof errorBar === 'number') {
          acc.min = Math.min(acc.min, value - errorBar);
          acc.max = Math.max(acc.max, value + errorBar);
        } else if (errorBar && typeof errorBar === 'object') {
          console.log('errorBar', errorBar);
          acc.min = Math.min(acc.min, errorBar.low);
          acc.max = Math.max(acc.max, errorBar.high);
        } else {
          acc.min = Math.min(acc.min, value);
          acc.max = Math.max(acc.max, value);
        }
      });
      return acc;
    }, { min: Infinity, max: -Infinity });

    const yAxisPadding = (minMaxValues.max - minMaxValues.min) * 0.1;

    yAxisScale = {
      y: {
        ...sharedConfig.options.scales.y,
        beginAtZero: false,
        min: Math.max(0, minMaxValues.min - yAxisPadding),
        max: minMaxValues.max + yAxisPadding,
      }
    };
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    hover: { mode: 'index', intersect: false },
    ...sharedConfig.options,
    onHover: (event, elements, chart) => {
      if (elements && elements.length > 0) {
        const rect = chart.canvas.getBoundingClientRect();
        const y = rect.bottom - rect.top + 40;
        setActiveIndicator(elements[0].index, y);
      } else {
        clearActiveIndicator();
      }
    },
    scales: {
      ...sharedConfig.options.scales,
      ...yAxisScale,
    },
    plugins: {
      ...sharedConfig.options.plugins,
      tooltip: {
        callbacks: {
          label: function(context) {
            const value = context.parsed.y;
            const chartType = context.chart.config.type;
            const metricLabel = context.dataset.label || '';
            
            if (chartType === 'histogram' || chartType === 'bar') {
              // For histograms, show the bin range and count
              const binLabel = context.label;
              const binWidth = parseFloat(context.dataset.xData?.[1]) - parseFloat(context.dataset.xData?.[0]);
              const binStart = parseFloat(binLabel) - (binWidth / 2);
              const binEnd = parseFloat(binLabel) + (binWidth / 2);
              return `${metricLabel} ${value} samples`;
            }
            
            // For line charts, keep the existing logic
            let label = `${metricLabel}: ${value.toFixed(2)}`;
            
            const chartErrorBarData = context.chart.errorBarData;
            const errorData = chartErrorBarData?.[context.datasetIndex]?.[context.dataIndex];
            
            if (errorData) {
              label += ` (95% CI: [${errorData.low.toFixed(2)}, ${errorData.high.toFixed(2)}])`;
            }
            
            return label;
          }
        }
      },
      errorBar: {
        draw: chartType === 'line',
      },
    },
  };

  const ChartComponent = chartType === 'line' ? Line : Bar;

  return (
    <div style={{ width: '100%', height: '250px', position: 'relative' }}>
      <ChartComponent ref={chartRef} options={options} data={data} />
      {shared && chartType === 'line' && (
        <SharedVerticalIndicator
          visible={indicatorState.visible}
          position={indicatorState.position}
          labels={data.labels}
          datasets={data.datasets}
          activeIndex={activeIndicatorIndex}
          chartHeight={indicatorState.chartHeight}
        />
      )}
    </div>
  );
};

export const MetricAdder = ({ graphId, label, yData, xData, color, config, errorBars, type }) => {
  const { addMetric, removeMetric } = useGraphContext();

  React.useEffect(() => {
    const metricId = Date.now();
    addMetric(graphId, { id: metricId, label, yData, xData, color, config, errorBars, type });
    return () => removeMetric(graphId, metricId);
  }, [graphId, label, yData, xData, color, config, errorBars, type, addMetric, removeMetric]);

  return null;
};

export const useGraph = (graphId) => {
  const { addGraph, removeGraph } = useGraphContext();

  React.useEffect(() => {
    addGraph(graphId);
    return () => removeGraph(graphId);
  }, [graphId, addGraph, removeGraph]);

  return useGraphContext().graphs[graphId];
};
