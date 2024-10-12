import React, { createContext, useContext, useState, useCallback } from 'react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { Line } from 'react-chartjs-2';
import { CustomTooltip, useTooltip } from './CustomTooltip';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const GraphContext = createContext();

export const useGraphContext = () => useContext(GraphContext);

export const GraphProvider = ({ children, xData, sharedConfig, onHover, onLeave }) => {
  const [graphs, setGraphs] = useState({});
  const [activeTooltipIndex, setActiveTooltipIndex] = useState(null);
  const [sharedTooltipY, setSharedTooltipY] = useState(null);

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

  const setActiveTooltip = useCallback((index, y) => {
    setActiveTooltipIndex(index);
    setSharedTooltipY(y);
    if (onHover) {
      onHover(index);
    }
  }, [onHover]);

  const clearActiveTooltip = useCallback(() => {
    setActiveTooltipIndex(null);
    setSharedTooltipY(null);
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
      activeTooltipIndex,
      sharedTooltipY,
      setActiveTooltip,
      clearActiveTooltip
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
    activeTooltipIndex, 
    sharedTooltipY, 
    setActiveTooltip, 
    clearActiveTooltip 
  } = useGraphContext();
  const graph = graphs[graphId];
  const chartRef = React.useRef(null);
  const tooltipState = useTooltip(chartRef, activeTooltipIndex, sharedTooltipY, clearActiveTooltip);
  
  if (!graph || !graph.metrics || graph.metrics.length === 0) {
    return <div>Loading graph...</div>;
  }

  const data = {
    labels: xData,
    datasets: graph.metrics.map(metric => ({
      label: metric.label,
      data: metric.yData,
      borderColor: metric.color,
      backgroundColor: metric.color,
      ...metric.config,
    })),
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: sharedConfig.title },
      tooltip: { enabled: false },
    },
    hover: { mode: 'index', intersect: false },
    onHover: (event, elements, chart) => {
      if (elements && elements.length > 0) {
        const rect = chart.canvas.getBoundingClientRect();
        const y = rect.bottom - rect.top + 40;
        setActiveTooltip(elements[0].index, y);
      } else {
        clearActiveTooltip();
      }
    },
    ...sharedConfig.options,
  };

  return (
    <div style={{ width: '100%', height: '250px', position: 'relative' }}>
      <Line ref={chartRef} options={options} data={data} />
      <CustomTooltip
        visible={tooltipState.visible}
        position={tooltipState.position}
        labels={data.labels}
        datasets={data.datasets}
        activeIndex={activeTooltipIndex}
        chartHeight={tooltipState.chartHeight}
      />
    </div>
  );
};

export const MetricAdder = ({ graphId, label, yData, color, config }) => {
  const { addMetric, removeMetric } = useGraphContext();

  React.useEffect(() => {
    const metricId = Date.now();
    console.log(`Adding metric to graph ${graphId}:`, { id: metricId, label, yData, color, config });
    addMetric(graphId, { id: metricId, label, yData, color, config });
    return () => removeMetric(graphId, metricId);
  }, [graphId, label, yData, color, config, addMetric, removeMetric]);

  return null;
};

export const useGraph = (graphId) => {
  const { addGraph, removeGraph } = useGraphContext();

  React.useEffect(() => {
    console.log(`Initializing graph ${graphId}`);
    addGraph(graphId);
    return () => removeGraph(graphId);
  }, [graphId, addGraph, removeGraph]);

  return useGraphContext().graphs[graphId]; // Return the graph data
};
